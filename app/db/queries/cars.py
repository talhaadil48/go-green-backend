import asyncpg
from app.db.base import record_to_dict, records_to_list


async def insert_car(
    conn: asyncpg.Connection, model, name, reg_no, attributes=None
) -> bool:
    if attributes is None:
        attributes = []
    await conn.execute(
        "INSERT INTO cars (model, name, reg_no, attributes) VALUES ($1, $2, $3, $4);",
        model, name, reg_no, attributes,
    )
    return True


async def update_car(
    conn: asyncpg.Connection, car_id: int, model, name, service_time, attributes=None
) -> bool:
    if attributes is None:
        attributes = []
    result = await conn.execute(
        "UPDATE cars SET model=$1, name=$2, service_time=$3, attributes=$4 WHERE id=$5;",
        model, name, service_time, attributes, car_id,
    )
    return result != "UPDATE 0"


async def delete_car(conn: asyncpg.Connection, car_id) -> bool:
    result = await conn.execute("DELETE FROM cars WHERE id = $1;", int(car_id))
    return result != "DELETE 0"


async def get_car_by_id(conn: asyncpg.Connection, car_id: int) -> dict | None:
    row = await conn.fetchrow("SELECT * FROM cars WHERE id = $1;", car_id)
    return record_to_dict(row)


async def get_all_cars(conn: asyncpg.Connection) -> list[dict]:
    rows = await conn.fetch("""
        SELECT
            c.*,
            ra.claim_id AS current_holder_claim_id,
            fh.miles_list
        FROM cars c
        LEFT JOIN LATERAL (
            SELECT r.claim_id
            FROM rental_agreements r
            WHERE (
                r.hire_vehicle_reg = c.reg_no
                AND r.hire_vehicle_date_out IS NOT NULL
                AND r.hire_vehicle_date_in IS NULL
            )
            OR EXISTS (
                SELECT 1
                FROM jsonb_array_elements(r.change_vehicle_history) AS ch
                WHERE ch->>'vehicle_reg' = c.reg_no
                AND ch->>'date_out' IS NOT NULL
                AND (ch->>'date_in' = '' OR ch->>'date_in' IS NULL)
            )
            ORDER BY r.rental_agreement_id DESC
            LIMIT 1
        ) ra ON TRUE
        LEFT JOIN LATERAL (
            SELECT ARRAY_AGG(f.miles_in) AS miles_list
            FROM fleet_history f
            WHERE f.car_reg = c.reg_no
        ) fh ON TRUE
        ORDER BY c.id ASC;
    """)

    result = []
    for row in rows:
        car = dict(row)
        miles_list = car.get("miles_list") or []
        valid_miles = []
        for m in miles_list:
            try:
                if m is not None and str(m).isdigit():
                    valid_miles.append(int(m))
            except Exception:
                pass
        car["last_miles_in"] = max(valid_miles) if valid_miles else None
        result.append(car)
    return result


async def get_free_cars(conn: asyncpg.Connection) -> list[dict]:
    rows = await conn.fetch(
        "SELECT * FROM cars WHERE is_long_hire = FALSE ORDER BY id ASC;"
    )
    return records_to_list(rows)


async def get_non_long_hire_cars_count(conn: asyncpg.Connection) -> int:
    return await conn.fetchval(
        "SELECT COUNT(*) FROM cars WHERE is_long_hire = FALSE;"
    )


async def get_available_cars(conn: asyncpg.Connection) -> list[dict]:
    rows = await conn.fetch("""
        SELECT * FROM cars
        WHERE is_long_hire = TRUE
        AND id NOT IN (SELECT car_id FROM claimant WHERE end_date IS NULL);
    """)
    return records_to_list(rows)


async def update_is_long_hire(conn: asyncpg.Connection, car_id: int, value: bool) -> dict | None:
    row = await conn.fetchrow(
        "UPDATE cars SET is_long_hire = $1 WHERE id = $2 RETURNING *;", value, car_id
    )
    return record_to_dict(row)


async def update_is_available(conn: asyncpg.Connection, reg_no: str, value: bool) -> dict | None:
    row = await conn.fetchrow(
        "UPDATE cars SET is_available = $1 WHERE reg_no = $2 RETURNING *;", value, reg_no
    )
    return record_to_dict(row)
