import asyncpg
from app.db.base import record_to_dict, records_to_list

UPDATABLE_COLUMNS = [
    "condition_1", "condition_2", "condition_3", "condition_4", "condition_5",
    "condition_6", "condition_7", "condition_8", "condition_9", "condition_10",
    "condition_11", "condition_12", "condition_13", "condition_14", "condition_15",
    "condition_16", "condition_17", "condition_18", "condition_19", "condition_20",
    "condition_21", "condition_22", "condition_23", "condition_24", "condition_25",
    "condition_26", "condition_27", "condition_28", "condition_29", "condition_30",
    "date", "customer", "detailer", "order_number", "year", "make", "model",
    "notes", "recommendations",
    "customer_signature", "detailer_signature", "base_vehicle_image", "annotated_vehicle_image",
]


async def upsert_pre_inspection_form(
    conn: asyncpg.Connection,
    claim_id: str,
    data: dict,
    inspection_id: str | None = None,
) -> dict | None:
    fields_to_update = [col for col in UPDATABLE_COLUMNS if col in data]

    try:
        if inspection_id:
            columns = ["claim_id", "inspection_id"] + fields_to_update
            ph = ", ".join(f"${i+1}" for i in range(len(columns)))
            set_clause = ", ".join(f"{col} = EXCLUDED.{col}" for col in fields_to_update)
            query = f"""
                INSERT INTO pre_inspection_forms ({', '.join(columns)})
                VALUES ({ph})
                ON CONFLICT (inspection_id) DO UPDATE SET {set_clause}
                RETURNING *;
            """
            values = [claim_id, inspection_id] + [data[col] for col in fields_to_update]
        else:
            columns = ["claim_id"] + fields_to_update
            ph = ", ".join(f"${i+1}" for i in range(len(columns)))
            query = f"""
                INSERT INTO pre_inspection_forms ({', '.join(columns)})
                VALUES ({ph})
                RETURNING *;
            """
            values = [claim_id] + [data[col] for col in fields_to_update]

        row = await conn.fetchrow(query, *values)
        return record_to_dict(row)
    except Exception as e:
        print(f"Error in upsert_pre_inspection_form: {e}")
        return None


async def get_pre_inspection_form(conn: asyncpg.Connection, claim_id: str) -> list[dict]:
    rows = await conn.fetch(
        "SELECT * FROM pre_inspection_forms WHERE claim_id = $1 ORDER BY inspection_id ASC;",
        claim_id,
    )
    return records_to_list(rows)


async def get_pre_inspection_form_by_inspection(
    conn: asyncpg.Connection, inspection_id: str
) -> dict | None:
    row = await conn.fetchrow(
        "SELECT * FROM pre_inspection_forms WHERE inspection_id = $1;", inspection_id
    )
    return record_to_dict(row)
