import asyncpg
from app.db.base import records_to_list


async def insert_fleet_history(
    conn: asyncpg.Connection,
    hire_start: str,
    hire_end: str | None,
    claim_id: str,
    car_reg: str,
    miles_in: str | None,
    miles_out: str | None,
) -> None:
    if miles_in == "":
        miles_in = None
    if miles_out == "":
        miles_out = None
    await conn.execute(
        "INSERT INTO fleet_history (hire_start, hire_end, claim_id, car_reg, miles_in, miles_out) VALUES ($1, $2, $3, $4, $5, $6);",
        hire_start, hire_end, claim_id, car_reg, miles_in, miles_out,
    )


async def update_fleet_history_hire_end(
    conn: asyncpg.Connection,
    hire_end: str,
    claim_id: str,
    car_reg: str,
    hire_start: str,
    miles_in: str | None,
    miles_out: str | None,
) -> None:
    if miles_in == "":
        miles_in = None
    if miles_out == "":
        miles_out = None
    await conn.execute(
        """UPDATE fleet_history SET hire_end = $1, miles_in = $2, miles_out = $3
           WHERE claim_id = $4 AND car_reg = $5 AND hire_start = $6;""",
        hire_end, miles_in, miles_out, claim_id, car_reg, hire_start,
    )


async def get_all_fleet_history(conn: asyncpg.Connection) -> list[dict]:
    rows = await conn.fetch("SELECT * FROM fleet_history ORDER BY hire_start DESC;")
    return records_to_list(rows)
