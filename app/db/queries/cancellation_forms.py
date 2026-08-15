import asyncpg
from app.db.base import record_to_dict

UPDATABLE_COLUMNS = ["name", "address", "postcode", "email", "cancellation_date", "cancellation_signature"]


async def upsert_cancellation_form(
    conn: asyncpg.Connection, claim_id: str, data: dict
) -> dict | None:
    fields_to_update = [col for col in UPDATABLE_COLUMNS if col in data]
    if not fields_to_update:
        return None

    columns = ["claim_id"] + fields_to_update
    ph = ", ".join(f"${i+1}" for i in range(len(columns)))
    set_clause = ", ".join(f"{col} = EXCLUDED.{col}" for col in fields_to_update)
    query = f"""
        INSERT INTO cancellation_forms ({', '.join(columns)})
        VALUES ({ph})
        ON CONFLICT (claim_id) DO UPDATE SET {set_clause}
        RETURNING *;
    """
    values = [claim_id] + [data[k] for k in fields_to_update]

    try:
        row = await conn.fetchrow(query, *values)
        return record_to_dict(row)
    except Exception as e:
        print(f"Error in upsert_cancellation_form: {e}")
        return None


async def get_cancellation_form(conn: asyncpg.Connection, claim_id: str) -> dict | None:
    row = await conn.fetchrow(
        "SELECT * FROM cancellation_forms WHERE claim_id = $1;", claim_id
    )
    return record_to_dict(row)
