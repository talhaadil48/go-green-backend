import asyncpg
import json
from app.db.base import record_to_dict
from datetime import datetime

UPDATABLE_COLUMNS = [
    "hirer_name", "title", "permanent_address",
    "additional_driver_name", "licence_no",
    "new_date_issued", "new_expiry_date", "new_dob", "new_date_test_passed", "new_occupation", "new_licence_no",
    "date_issued", "expiry_date", "dob", "date_test_passed", "occupation",
    "daily_rate", "policy_excess", "deposit", "refuelling_charge",
    "insurance_company", "policy_no", "insurance_dates",
    "own_insurance_confirm", "insurance_date", "insurance_time",
    "motoring_offence_3yrs", "disqualified_5yrs", "accident_3yrs",
    "insurance_declined_5yrs", "dishonesty_conviction",
    "medical_condition1", "medical_condition2", "medical_details",
    "additional_driver_auth",
    "hire_vehicle_reg", "hire_vehicle_make", "hire_vehicle_model", "hire_vehicle_group",
    "hire_vehicle_date_out", "hire_vehicle_date_in",
    "hire_vehicle_fuel_out", "hire_vehicle_fuel_in",
    "change_vehicle_reg", "change_vehicle_make", "change_vehicle_model", "change_vehicle_group",
    "change_vehicle_date_out", "change_vehicle_date_in",
    "change_vehicle_fuel_out", "change_vehicle_fuel_in",
    "admin_fee", "delivery_charge", "cdw_per_day",
    "days_out", "days_in", "total_days",
    "rate_per_day", "refuelling_total",
    "subtotal", "vat", "total_cost",
    "declaration_date", "liability_date",
    "hirer_signature_terms", "company_signature",
    "hirer_signature_insurance", "declaration_signature", "liability_signature",
    "change_vehicle_history", "hire_vehicle_miles_out", "hire_vehicle_miles_in",
]


async def get_existing_rental(conn: asyncpg.Connection, claim_id: str) -> dict:
    row = await conn.fetchrow(
        """SELECT hire_vehicle_reg, hire_vehicle_date_out, hire_vehicle_date_in, change_vehicle_history
           FROM rental_agreements WHERE claim_id = $1;""",
        claim_id,
    )
    if not row:
        return {}
    result = dict(row)
    if result.get("change_vehicle_history") and isinstance(result["change_vehicle_history"], str):
        result["change_vehicle_history"] = json.loads(result["change_vehicle_history"])
    return result


async def upsert_rental_agreement(
    conn: asyncpg.Connection, claim_id: str, data: dict
) -> dict | None:
    fields_to_update = [col for col in UPDATABLE_COLUMNS if col in data]
    if not fields_to_update:
        return None

    columns = ["claim_id"] + fields_to_update
    ph = ", ".join(f"${i+1}" for i in range(len(columns)))
    set_clause = ", ".join(f"{col} = EXCLUDED.{col}" for col in fields_to_update)
    query = f"""
        INSERT INTO rental_agreements ({', '.join(columns)})
        VALUES ({ph})
        ON CONFLICT (claim_id) DO UPDATE SET {set_clause}
        RETURNING *;
    """

    values = [claim_id]
    for k in fields_to_update:
        if k == "change_vehicle_history" and k in data:
            val = data[k]
            values.append(json.dumps(val) if not isinstance(val, str) else val)
        else:
            values.append(data[k])

    try:
        row = await conn.fetchrow(query, *values)
        return record_to_dict(row)
    except Exception as e:
        print(f"Error in upsert_rental_agreement: {e}")
        return None


async def get_rental_agreement(conn: asyncpg.Connection, claim_id: str) -> dict | None:
    row = await conn.fetchrow(
        "SELECT * FROM rental_agreements WHERE claim_id = $1;", claim_id
    )
    return record_to_dict(row)


async def get_rental_by_claim(conn: asyncpg.Connection, claim_id: str):
    row = await conn.fetchrow(
        "SELECT total_cost FROM rental_agreements WHERE claim_id = $1;", claim_id
    )
    return row["total_cost"] if row else None


async def refresh_rental_agreements_view(conn: asyncpg.Connection) -> None:
    try:
        await conn.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY rental_agreements_mv;")
    except Exception as e:
        print(f"Error refreshing materialized view: {e}")
