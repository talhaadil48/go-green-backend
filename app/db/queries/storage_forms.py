import asyncpg
from app.db.base import record_to_dict

UPDATABLE_COLUMNS = [
    "name", "postcode", "address1", "address2",
    "vehicle_make", "vehicle_model", "registration_number",
    "date_of_recovery", "storage_start_date", "storage_end_date",
    "number_of_days", "charges_per_day", "total_storage_charge",
    "recovery_charge", "subtotal", "vat_amount", "invoice_total",
    "client_date", "owner_date", "client_signature", "owner_signature", "storage_location_key",
]


async def upsert_storage_form(
    conn: asyncpg.Connection, claim_id: str, data: dict
) -> dict | None:
    # Convert empty strings to None
    cleaned = {k: (None if v == "" else v) for k, v in data.items()}
    fields_to_update = [col for col in UPDATABLE_COLUMNS if col in cleaned]
    if not fields_to_update:
        return None

    columns = ["claim_id"] + fields_to_update
    ph = ", ".join(f"${i+1}" for i in range(len(columns)))
    set_clause = ", ".join(f"{col} = EXCLUDED.{col}" for col in fields_to_update)
    query = f"""
        INSERT INTO storage_forms ({', '.join(columns)})
        VALUES ({ph})
        ON CONFLICT (claim_id) DO UPDATE SET {set_clause}
        RETURNING *;
    """
    values = [claim_id] + [cleaned[k] for k in fields_to_update]

    try:
        row = await conn.fetchrow(query, *values)
        return record_to_dict(row)
    except Exception as e:
        print(f"Error in upsert_storage_form: {e}")
        return None


async def get_storage_form(conn: asyncpg.Connection, claim_id: str) -> dict | None:
    row = await conn.fetchrow("SELECT * FROM storage_forms WHERE claim_id = $1;", claim_id)
    return record_to_dict(row)


async def get_storage_by_claim(conn: asyncpg.Connection, claim_id: str):
    row = await conn.fetchrow(
        "SELECT invoice_total FROM storage_forms WHERE claim_id = $1;", claim_id
    )
    return row["invoice_total"] if row else None
