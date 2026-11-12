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


async def upsert_hire_checklist(
    conn: asyncpg.Connection,
    long_claim_id: str,
    car_id: int,
    claimant_id: int,
    data: dict,
) -> dict | None:
    fields_to_update = [col for col in UPDATABLE_COLUMNS if col in data]

    columns = ["long_claim_id", "car_id", "claimant_id"] + fields_to_update
    ph = ", ".join(f"${i+1}" for i in range(len(columns)))
    set_clause = ", ".join(f"{col} = EXCLUDED.{col}" for col in fields_to_update)

    if set_clause:
        conflict_action = f"DO UPDATE SET {set_clause}"
    else:
        conflict_action = "DO NOTHING"

    query = f"""
        INSERT INTO hire_checklist ({', '.join(columns)})
        VALUES ({ph})
        ON CONFLICT (long_claim_id, car_id, claimant_id) {conflict_action}
        RETURNING *;
    """

    values = [long_claim_id, car_id, claimant_id] + [data[col] for col in fields_to_update]

    try:
        row = await conn.fetchrow(query, *values)
        return record_to_dict(row)
    except Exception as e:
        print(f"Error in upsert_hire_checklist: {e}")
        return None


async def get_hire_checklists(
    conn: asyncpg.Connection,
    long_claim_id: str,
    car_id: int,
    claimant_id: int,
) -> list[dict]:
    rows = await conn.fetch(
        """SELECT * FROM hire_checklist
           WHERE long_claim_id = $1 AND car_id = $2 AND claimant_id = $3
           ORDER BY inspection_id ASC;""",
        long_claim_id, car_id, claimant_id,
    )
    return records_to_list(rows)
