"""
Business logic for rental agreement upserts — fleet history, availability, status updates.
All operations run inside a single transaction.
"""
import asyncpg
import json
from datetime import datetime
from app.db.queries import rental_agreements as ra_q
from app.db.queries import fleet_history as fh_q
from app.db.queries import cars as cars_q
from app.db.queries import claims as claims_q


def _parse_date(d):
    if d and isinstance(d, str) and d.strip():
        try:
            return datetime.strptime(d, "%Y-%m-%d").date()
        except ValueError:
            return None
    elif hasattr(d, "date"):
        return d.date() if callable(d.date) else d
    elif hasattr(d, "year"):
        return d
    return None


async def _handle_fleet_history(
    conn: asyncpg.Connection,
    reg, old_out, old_in, new_out, new_in, miles_out_val, miles_in_val, claim_id
):
    if new_in and not new_out:
        return
    if old_out and new_out and old_out != new_out:
        return

    if not old_out and not old_in:
        if new_out and not new_in:
            await fh_q.insert_fleet_history(new_out, None, claim_id, reg, miles_in_val, miles_out_val)
        elif new_out and new_in:
            await fh_q.insert_fleet_history(new_out, new_in, claim_id, reg, miles_in_val, miles_out_val)
    elif old_out and not old_in:
        if new_out and new_in:
            await fh_q.update_fleet_history_hire_end(new_in, claim_id, reg, old_out, miles_in_val, miles_out_val)
    elif old_out and old_in:
        await fh_q.update_fleet_history_hire_end(old_in, claim_id, reg, old_out, miles_in_val, miles_out_val)


async def upsert_rental_agreement(
    conn: asyncpg.Connection, claim_id: str, data: dict
) -> dict | None:
    async with conn.transaction():
        # 1. Capture existing state before upsert
        existing = await ra_q.get_existing_rental(conn, claim_id)

        # 2. Do the upsert
        result = await ra_q.upsert_rental_agreement(conn, claim_id, data)
        if not result:
            return None

        # 3. Handle hire vehicle fleet history
        old_out = existing.get("hire_vehicle_date_out")
        old_in = existing.get("hire_vehicle_date_in")
        new_out = result.get("hire_vehicle_date_out")
        new_in = result.get("hire_vehicle_date_in")
        reg = result.get("hire_vehicle_reg")
        miles_out_val = result.get("hire_vehicle_miles_out")
        miles_in_val = result.get("hire_vehicle_miles_in")

        if reg:
            await _handle_fleet_history(conn, reg, old_out, old_in, new_out, new_in, miles_out_val, miles_in_val, claim_id)

        # 4. Handle change vehicle history
        old_history = existing.get("change_vehicle_history", []) or []
        if isinstance(old_history, str):
            try:
                old_history = json.loads(old_history)
            except Exception:
                old_history = []

        new_history = result.get("change_vehicle_history")
        if isinstance(new_history, str):
            try:
                new_history = json.loads(new_history)
            except Exception:
                new_history = []
        new_history = new_history or []

        old_map = {
            (c.get("vehicle_reg"), c.get("date_out")): c
            for c in old_history
        }

        for change in new_history:
            c_reg = change.get("vehicle_reg")
            c_new_out = change.get("date_out")
            c_new_in = change.get("date_in")
            if not c_reg:
                continue
            old = old_map.get((c_reg, c_new_out), {})
            c_old_out = old.get("date_out")
            c_old_in = old.get("date_in")
            miles_in = change.get("miles_in")
            miles_out = change.get("miles_out")
            await _handle_fleet_history(conn, c_reg, c_old_out, c_old_in, c_new_out, c_new_in, miles_out, miles_in, claim_id)

        # 5. Hire vehicle availability + claim status
        hire_out = result.get("hire_vehicle_date_out")
        hire_in = result.get("hire_vehicle_date_in")
        hire_reg = result.get("hire_vehicle_reg")

        was_both_null = (old_out is None and old_in is None)
        is_now_both_present = (hire_out is not None and hire_in is not None)

        if hire_out and hire_in:
            await claims_q.update_claim_status(conn, claim_id, "hire end")
            if not (was_both_null and is_now_both_present) and hire_reg:
                await cars_q.update_is_available(conn, hire_reg, True)
        elif hire_out:
            await claims_q.update_claim_status(conn, claim_id, "hire start")
            if hire_reg:
                await cars_q.update_is_available(conn, hire_reg, False)

        # 6. Determine latest status from all vehicle entries
        all_entries = []
        if hire_out or hire_in:
            all_entries.append({
                "vehicle_reg": hire_reg,
                "date_out": _parse_date(hire_out),
                "date_in": _parse_date(hire_in),
            })
        for change in new_history:
            c_reg = change.get("vehicle_reg")
            out_date = _parse_date(change.get("date_out"))
            in_date = _parse_date(change.get("date_in"))
            if c_reg and (out_date or in_date):
                all_entries.append({"vehicle_reg": c_reg, "date_out": out_date, "date_in": in_date})

        latest_entry = max(
            (e for e in all_entries if e.get("date_out")),
            key=lambda x: x["date_out"],
            default=None,
        )
        if latest_entry:
            if latest_entry.get("date_out") and not latest_entry.get("date_in"):
                await claims_q.update_claim_status(conn, claim_id, "hire start")
            elif latest_entry.get("date_out") and latest_entry.get("date_in"):
                await claims_q.update_claim_status(conn, claim_id, "hire end")

        # 7. Change vehicle availability
        for change in new_history:
            c_reg = change.get("vehicle_reg")
            out_date = change.get("date_out")
            in_date = change.get("date_in")
            if not c_reg:
                continue
            old_entry = old_map.get((c_reg, out_date), {})
            was_no_previous = (old_entry.get("date_out") is None and old_entry.get("date_in") is None)
            is_complete = (out_date is not None and in_date is not None)
            if out_date and in_date:
                if not (was_no_previous and is_complete):
                    await cars_q.update_is_available(conn, c_reg, True)
            elif out_date:
                await cars_q.update_is_available(conn, c_reg, False)

        # 8. Refresh materialized view
        await ra_q.refresh_rental_agreements_view(conn)

        return result
