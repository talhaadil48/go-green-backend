"""
Rental-agreement query methods.

Covers all database operations for the ``rental_agreements`` table including
the fleet-history side-effects that are triggered on every save.
"""

import json
from psycopg2.extras import RealDictCursor

from .base import ClaimFormBase, parse_date


class RentalAgreementQueries(ClaimFormBase):
    """
    Mixin class that provides rental-agreement read/write queries.

    The upsert method automatically maintains ``fleet_history`` records and
    updates car availability whenever hire-vehicle dates change.
    """

    # ------------------------------------------------------------------
    # Write helpers
    # ------------------------------------------------------------------

    def upsert_rental_agreement(self, claim_id: str, data: dict) -> dict | None:
        """
        Insert or update a rental agreement (upsert on ``claim_id``).

        Side effects on success:
        - Fleet-history rows are inserted or updated based on hire dates.
        - Car availability (``cars.is_available``) is toggled.
        - Claim status is updated to ``"hire start"`` or ``"hire end"``.
        - The ``rental_agreements_mv`` materialised view is refreshed.

        Only columns present in *data* are written.

        Args:
            claim_id: The claim this rental agreement belongs to.
            data: Flat dict of column-name → value pairs.

        Returns:
            The saved row as a dict, or ``None`` if no fields were provided
            or on failure.
        """

        def get_existing_rental():
            """Fetch key hire-date and vehicle fields from the existing row."""
            query = """
                SELECT
                    hire_vehicle_reg,
                    hire_vehicle_date_out,
                    hire_vehicle_date_in,
                    change_vehicle_history
                FROM rental_agreements
                WHERE claim_id = %s;
            """
            with self.conn.cursor() as cur:
                cur.execute(query, (claim_id,))
                row = cur.fetchone()
                if not row:
                    return {}
                cols = [d[0] for d in cur.description]
                result = dict(zip(cols, row))
                if result.get("change_vehicle_history") and isinstance(
                    result["change_vehicle_history"], str
                ):
                    result["change_vehicle_history"] = json.loads(
                        result["change_vehicle_history"]
                    )
                return result

        def handle_fleet_history(reg, old_out, old_in, new_out, new_in, miles_out_val, miles_in_val):
            """
            Decide whether to insert or update a fleet-history record.

            Rules:
            - If ``new_in`` is set but ``new_out`` is not → invalid, skip.
            - Changing an existing ``date_out`` is not allowed.
            - CASE 1: both dates previously null → insert.
            - CASE 2: ``date_out`` existed but ``date_in`` was null → update.
            - CASE 3: both dates existed → update to overwrite.
            """
            if new_in and not new_out:
                return
            if old_out and new_out and old_out != new_out:
                return

            if not old_out and not old_in:
                if new_out and not new_in:
                    self.insert_fleet_history(new_out, None, claim_id, reg, miles_in_val, miles_out_val)
                elif new_out and new_in:
                    self.insert_fleet_history(new_out, new_in, claim_id, reg, miles_in_val, miles_out_val)
            elif old_out and not old_in:
                if new_out and new_in:
                    self.update_fleet_history_hire_end(new_in, claim_id, reg, old_out, miles_in_val, miles_out_val)
            elif old_out and old_in:
                self.update_fleet_history_hire_end(old_in, claim_id, reg, old_out, miles_in_val, miles_out_val)

        existing = get_existing_rental()

        updatable_columns = [
            "hirer_name", "title", "permanent_address",
            "additional_driver_name", "licence_no",
            "new_date_issued", "new_expiry_date", "new_dob",
            "new_date_test_passed", "new_occupation", "new_licence_no",
            "date_issued", "expiry_date", "dob", "date_test_passed", "occupation",
            "daily_rate", "policy_excess", "deposit", "refuelling_charge",
            "insurance_company", "policy_no", "insurance_dates",
            "own_insurance_confirm", "insurance_date", "insurance_time",
            "motoring_offence_3yrs", "disqualified_5yrs", "accident_3yrs",
            "insurance_declined_5yrs", "dishonesty_conviction",
            "medical_condition1", "medical_condition2", "medical_details",
            "additional_driver_auth",
            "hire_vehicle_reg", "hire_vehicle_make", "hire_vehicle_model",
            "hire_vehicle_group",
            "hire_vehicle_date_out", "hire_vehicle_date_in",
            "hire_vehicle_fuel_out", "hire_vehicle_fuel_in",
            "change_vehicle_reg", "change_vehicle_make", "change_vehicle_model",
            "change_vehicle_group",
            "change_vehicle_date_out", "change_vehicle_date_in",
            "change_vehicle_fuel_out", "change_vehicle_fuel_in",
            "admin_fee", "delivery_charge", "cdw_per_day",
            "days_out", "days_in", "total_days",
            "rate_per_day", "refuelling_total",
            "subtotal", "vat", "total_cost",
            "declaration_date", "liability_date",
            "hirer_signature_terms", "company_signature",
            "hirer_signature_insurance", "declaration_signature",
            "liability_signature",
            "change_vehicle_history",
            "hire_vehicle_miles_out", "hire_vehicle_miles_in",
        ]

        fields_to_update = [col for col in updatable_columns if col in data]
        if not fields_to_update:
            return None

        set_clause = ", ".join(f"{col} = EXCLUDED.{col}" for col in fields_to_update)
        columns = ["claim_id"] + fields_to_update
        values_placeholders = ", ".join(f"%({col})s" for col in columns)

        query = f"""
            INSERT INTO rental_agreements ({', '.join(columns)})
            VALUES ({values_placeholders})
            ON CONFLICT (claim_id)
            DO UPDATE SET
                {set_clause}
            RETURNING *;
        """

        params = {"claim_id": claim_id}
        for k in fields_to_update:
            if k == "change_vehicle_history" and k in data:
                params[k] = json.dumps(data[k])
            else:
                params[k] = data[k]

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, params)
                row = cur.fetchone()

                if not row:
                    return None

                col_names = [desc[0] for desc in cur.description]
                result = dict(zip(col_names, row))

                # ── Hire vehicle fleet-history ─────────────────────────────
                old_out = existing.get("hire_vehicle_date_out")
                old_in = existing.get("hire_vehicle_date_in")
                new_out = result.get("hire_vehicle_date_out")
                new_in = result.get("hire_vehicle_date_in")
                reg = result.get("hire_vehicle_reg")
                miles_out_val = result.get("hire_vehicle_miles_out")
                miles_in_val = result.get("hire_vehicle_miles_in")

                if reg:
                    handle_fleet_history(reg, old_out, old_in, new_out, new_in, miles_out_val, miles_in_val)

                # ── Change-vehicle fleet-history ───────────────────────────
                old_history = existing.get("change_vehicle_history", []) or []
                new_history = result.get("change_vehicle_history")

                if isinstance(new_history, str):
                    new_history = json.loads(new_history)
                new_history = new_history or []

                old_map = {
                    (c.get("vehicle_reg"), c.get("date_out")): c
                    for c in old_history
                }

                for change in new_history:
                    reg = change.get("vehicle_reg")
                    new_out = change.get("date_out")
                    new_in = change.get("date_in")
                    if not reg:
                        continue
                    old = old_map.get((reg, new_out), {})
                    old_out = old.get("date_out")
                    old_in = old.get("date_in")
                    miles_in = change.get("miles_in")
                    miles_out = change.get("miles_out")
                    handle_fleet_history(reg, old_out, old_in, new_out, new_in, miles_out, miles_in)

                # ── Car availability + claim status ────────────────────────
                hire_out = result.get("hire_vehicle_date_out")
                hire_in = result.get("hire_vehicle_date_in")
                hire_reg = result.get("hire_vehicle_reg")

                was_both_null = (
                    existing.get("hire_vehicle_date_out") is None
                    and existing.get("hire_vehicle_date_in") is None
                )
                is_now_both_present = hire_out is not None and hire_in is not None

                if hire_out and hire_in:
                    self.update_claim_status(claim_id, "hire end")
                    if not (was_both_null and is_now_both_present):
                        if hire_reg:
                            self.update_is_available(hire_reg, True)
                elif hire_out:
                    self.update_claim_status(claim_id, "hire start")
                    if hire_reg:
                        self.update_is_available(hire_reg, False)

                # ── Compute latest-entry status from all hire entries ──────
                all_entries = []
                if hire_out or hire_in:
                    all_entries.append({
                        "vehicle_reg": hire_reg,
                        "date_out": parse_date(hire_out),
                        "date_in": parse_date(hire_in),
                    })
                for change in new_history:
                    reg = change.get("vehicle_reg")
                    out_date = parse_date(change.get("date_out"))
                    in_date = parse_date(change.get("date_in"))
                    if reg and (out_date or in_date):
                        all_entries.append({
                            "vehicle_reg": reg,
                            "date_out": out_date,
                            "date_in": in_date,
                        })

                latest_entry = max(
                    (e for e in all_entries if e.get("date_out")),
                    key=lambda x: x["date_out"],
                    default=None,
                )
                if latest_entry:
                    if latest_entry.get("date_out") and not latest_entry.get("date_in"):
                        self.update_claim_status(claim_id, "hire start")
                    elif latest_entry.get("date_out") and latest_entry.get("date_in"):
                        self.update_claim_status(claim_id, "hire end")

                # ── Change-vehicle availability ────────────────────────────
                if new_history:
                    for change in new_history:
                        reg = change.get("vehicle_reg")
                        out_date = change.get("date_out")
                        in_date = change.get("date_in")
                        if not reg:
                            continue
                        old_entry = old_map.get((reg, out_date), {})
                        was_no_previous_entry = (
                            old_entry.get("date_out") is None
                            and old_entry.get("date_in") is None
                        )
                        is_complete_hire_now = out_date is not None and in_date is not None
                        if out_date and in_date:
                            if not (was_no_previous_entry and is_complete_hire_now):
                                self.update_is_available(reg, True)
                        elif out_date:
                            self.update_is_available(reg, False)

                self.conn.commit()
                self.refresh_rental_agreements_view()
                return result

        except Exception as e:
            print(f"Error in upsert_rental_agreement: {e}")
            self.conn.rollback()
            return None

    # ------------------------------------------------------------------
    # Read helpers
    # ------------------------------------------------------------------

    def get_rental_agreement(self, claim_id: str) -> dict | None:
        """
        Retrieve the rental agreement for a given claim.

        Args:
            claim_id: The unique claim identifier.

        Returns:
            The row as a dict, or ``None`` if not found.
        """
        query = "SELECT * FROM rental_agreements WHERE claim_id = %s;"
        with self.conn.cursor() as cur:
            cur.execute(query, (claim_id,))
            row = cur.fetchone()
            if row:
                columns = [desc[0] for desc in cur.description]
                return dict(zip(columns, row))
        return None

    def get_rental_by_claim(self, claim_id: str) -> float | None:
        """
        Return the ``total_cost`` for the rental agreement associated with a claim.

        Args:
            claim_id: The unique claim identifier.

        Returns:
            The total cost as a float, or ``None`` if not found.
        """
        query = "SELECT total_cost FROM rental_agreements WHERE claim_id = %s"
        with self.conn.cursor() as cur:
            cur.execute(query, (claim_id,))
            row = cur.fetchone()
            if not row:
                return None
            (total_cost,) = row
            return total_cost

    def update_hire_vehicle_dates(
        self,
        claim_id: str,
        date_in: str = None,
        date_out: str = None,
    ) -> dict | None:
        """
        Upsert only the hire-vehicle date fields on a rental agreement.

        Both ``date_in`` and ``date_out`` are always sent to the query (they
        may be ``None``, which becomes ``NULL`` in Postgres).

        Args:
            claim_id: The unique claim identifier.
            date_in: New hire-in date string (``YYYY-MM-DD``) or ``None``.
            date_out: New hire-out date string (``YYYY-MM-DD``) or ``None``.

        Returns:
            The updated row as a dict, or ``None`` on failure.
        """
        fields = []
        params = {"claim_id": claim_id}

        if "date_in" in locals():
            fields.append("hire_vehicle_date_in = %(date_in)s")
            params["date_in"] = date_in

        if "date_out" in locals():
            fields.append("hire_vehicle_date_out = %(date_out)s")
            params["date_out"] = date_out

        if not fields:
            return None

        query = f"""
            INSERT INTO rental_agreements (claim_id, hire_vehicle_date_in, hire_vehicle_date_out)
            VALUES (%(claim_id)s, %(date_in)s, %(date_out)s)
            ON CONFLICT (claim_id)
            DO UPDATE SET
                {', '.join(fields)}
            RETURNING *;
        """

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, params)
                row = cur.fetchone()
                if row:
                    self.conn.commit()
                    self.refresh_rental_agreements_view()
                    columns = [desc[0] for desc in cur.description]
                    return dict(zip(columns, row))
            return None
        except Exception as e:
            print(f"Error updating hire vehicle dates: {e}")
            self.conn.rollback()
            return None

    def refresh_rental_agreements_view(self):
        """
        Refresh the ``rental_agreements_mv`` materialised view concurrently.

        Errors are caught and logged so they never interrupt the main
        transaction flow.
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY rental_agreements_mv;")
            self.conn.commit()
        except Exception as e:
            print(f"Error refreshing materialized view: {e}")
            self.conn.rollback()
