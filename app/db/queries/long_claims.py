import asyncpg
from app.db.base import record_to_dict, records_to_list


async def insert_long_claim(
    conn: asyncpg.Connection,
    starting_date,
    ending_date,
    hirer_name=None,
) -> int:
    row = await conn.fetchrow(
        "INSERT INTO long_claims (starting_date, ending_date, hirer_name) VALUES ($1, $2, $3) RETURNING id;",
        starting_date, ending_date, hirer_name,
    )
    return row["id"]


async def update_long_claim(
    conn: asyncpg.Connection,
    long_claim_id: str,
    starting_date,
    ending_date,
    hirer_name=None,
) -> None:
    await conn.execute(
        "UPDATE long_claims SET starting_date = $1, ending_date = $2, hirer_name = $3 WHERE id = $4;",
        starting_date, ending_date, hirer_name, long_claim_id,
    )


async def add_car_to_long_claim(conn: asyncpg.Connection, long_claim_id: str, car_id: int) -> None:
    await conn.execute(
        "INSERT INTO long_claim_cars (long_claim_id, car_id) VALUES ($1, $2);",
        long_claim_id, car_id,
    )


async def remove_car_from_long_claim(conn: asyncpg.Connection, long_claim_id: str, car_id: int) -> None:
    await conn.execute(
        "DELETE FROM long_claim_cars WHERE long_claim_id = $1 AND car_id = $2;",
        long_claim_id, car_id,
    )


async def get_all_long_claims(conn: asyncpg.Connection) -> list[dict]:
    rows = await conn.fetch(
        """SELECT id, starting_date, ending_date, invoice_sent, date_sent, hirer_name
           FROM long_claims WHERE recently_deleted = FALSE ORDER BY id DESC;"""
    )
    return records_to_list(rows)


async def get_long_claim_by_id(conn: asyncpg.Connection, claim_id) -> dict | None:
    row = await conn.fetchrow(
        """SELECT id, starting_date, ending_date, invoice_sent, hirer_name
           FROM long_claims WHERE id = $1;""",
        claim_id,
    )
    return record_to_dict(row)


async def mark_invoice(conn: asyncpg.Connection, long_claim_id: str) -> bool:
    result = await conn.execute(
        "UPDATE long_claims SET invoice_sent = TRUE, date_sent = CURRENT_DATE WHERE id = $1;",
        long_claim_id,
    )
    return result != "UPDATE 0"


async def mark_as_recently_deleted(conn: asyncpg.Connection, claim_id: str, deleted_by: str) -> int:
    result = await conn.execute(
        "UPDATE long_claims SET recently_deleted = TRUE, recently_deleted_date = NOW(), deleted_by = $1 WHERE id = $2;",
        deleted_by, claim_id,
    )
    parts = result.split()
    return int(parts[1]) if len(parts) == 2 else 0


async def delete_long_claim(conn: asyncpg.Connection, claim_id: str) -> int:
    result = await conn.execute("DELETE FROM long_claims WHERE id = $1;", claim_id)
    parts = result.split()
    return int(parts[1]) if len(parts) == 2 else 0


async def restore_claim(conn: asyncpg.Connection, claim_id: str) -> int:
    result = await conn.execute(
        "UPDATE long_claims SET recently_deleted = FALSE, recently_deleted_date = NULL WHERE id = $1;",
        claim_id,
    )
    parts = result.split()
    return int(parts[1]) if len(parts) == 2 else 0


async def get_soft_deleted_long_claims(conn: asyncpg.Connection) -> list[dict]:
    rows = await conn.fetch(
        """SELECT id, starting_date, ending_date, invoice_sent, date_sent, hirer_name, deleted_by
           FROM long_claims WHERE recently_deleted = TRUE ORDER BY id DESC;"""
    )
    return records_to_list(rows)


async def get_cars_by_long_claim(conn: asyncpg.Connection, long_claim_id) -> list[dict]:
    rows = await conn.fetch(
        """SELECT c.* FROM long_claim_cars lcc
           JOIN cars c ON c.id = lcc.car_id
           WHERE lcc.long_claim_id = $1;""",
        long_claim_id,
    )
    return records_to_list(rows)


async def update_daily_rate(
    conn: asyncpg.Connection, long_claim_id: str, car_id: int, daily_rate: float
) -> bool:
    result = await conn.execute(
        "UPDATE long_claim_cars SET daily_rate = $1 WHERE long_claim_id = $2 AND car_id = $3;",
        daily_rate, long_claim_id, car_id,
    )
    return result != "UPDATE 0"


async def get_daily_rates_for_claim(conn: asyncpg.Connection, long_claim_id: str) -> list[dict]:
    rows = await conn.fetch(
        "SELECT car_id, daily_rate FROM long_claim_cars WHERE long_claim_id = $1;",
        long_claim_id,
    )
    return records_to_list(rows)
