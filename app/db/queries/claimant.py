import asyncpg
from app.db.base import record_to_dict, records_to_list


async def insert_claimant(
    conn: asyncpg.Connection,
    long_claim_id,
    car_id,
    start_date=None,
    end_date=None,
    miles=None,
    name=None,
    location=None,
    delivery_charges=0,
    claimant_id=None,
    ref_no=None,
) -> int:
    row = await conn.fetchrow(
        """INSERT INTO claimant
           (claimant_id, ref_no, long_claim_id, car_id, start_date, end_date, miles, name, location, delivery_charges)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
           RETURNING id;""",
        claimant_id, ref_no, long_claim_id, car_id,
        start_date, end_date, miles, name, location, delivery_charges,
    )
    return row["id"]


async def update_claimant(
    conn: asyncpg.Connection,
    claimant_id: int,
    new_claimant_id=None,
    ref_no=None,
    start_date=None,
    end_date=None,
    miles=None,
    name=None,
    location=None,
    delivery_charges=None,
) -> bool:
    fields = []
    values = []
    if new_claimant_id is not None:
        fields.append(f"claimant_id = ${len(values)+1}")
        values.append(new_claimant_id)
    if ref_no is not None:
        fields.append(f"ref_no = ${len(values)+1}")
        values.append(ref_no)
    if start_date is not None:
        fields.append(f"start_date = ${len(values)+1}")
        values.append(start_date)
    if end_date is not None:
        fields.append(f"end_date = ${len(values)+1}")
        values.append(end_date)
    if miles is not None:
        fields.append(f"miles = ${len(values)+1}")
        values.append(miles)
    if name is not None:
        fields.append(f"name = ${len(values)+1}")
        values.append(name)
    if location is not None:
        fields.append(f"location = ${len(values)+1}")
        values.append(location)
    if delivery_charges is not None:
        fields.append(f"delivery_charges = ${len(values)+1}")
        values.append(delivery_charges)

    if not fields:
        return False

    values.append(claimant_id)
    result = await conn.execute(
        f"UPDATE claimant SET {', '.join(fields)} WHERE id = ${len(values)};",
        *values,
    )
    return result != "UPDATE 0"


async def delete_claimant(conn: asyncpg.Connection, claimant_id: int) -> bool:
    result = await conn.execute("DELETE FROM claimant WHERE id = $1;", claimant_id)
    return result != "DELETE 0"


async def get_claimant(conn: asyncpg.Connection, claimant_id=None, long_claim_id=None, car_id=None) -> list[dict]:
    query = "SELECT * FROM claimant WHERE 1=1"
    params = []
    if claimant_id is not None:
        params.append(claimant_id)
        query += f" AND id = ${len(params)}"
    if long_claim_id is not None:
        params.append(long_claim_id)
        query += f" AND long_claim_id = ${len(params)}"
    if car_id is not None:
        params.append(car_id)
        query += f" AND car_id = ${len(params)}"
    rows = await conn.fetch(query, *params)
    return records_to_list(rows)


async def get_all_claimants(conn: asyncpg.Connection) -> list[dict]:
    rows = await conn.fetch("SELECT * FROM claimant ORDER BY id DESC;")
    return records_to_list(rows)


async def get_claimants_by_car(conn: asyncpg.Connection, car_id: int, claim_id: str) -> list[dict]:
    rows = await conn.fetch(
        "SELECT * FROM claimant WHERE car_id = $1 AND long_claim_id = $2;",
        car_id, claim_id,
    )
    return records_to_list(rows)


async def get_claimants_for_claim(conn: asyncpg.Connection, long_claim_id: str) -> list[dict]:
    rows = await conn.fetch(
        "SELECT * FROM claimant WHERE long_claim_id = $1;", long_claim_id
    )
    return records_to_list(rows)
