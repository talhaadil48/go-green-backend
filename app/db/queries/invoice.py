import asyncpg
from app.db.base import record_to_dict, records_to_list
from datetime import datetime


async def insert_invoice(
    conn: asyncpg.Connection,
    claim_id: str,
    info: str,
    docs: list,
    storage_bill: float,
    rent_bill: float,
    user_name: str,
) -> int:
    row = await conn.fetchrow(
        """INSERT INTO invoice (claim_id, info, docs, storage_bill, rent_bill, user_name)
           VALUES ($1, $2, $3, $4, $5, $6) RETURNING id;""",
        claim_id, info, docs, storage_bill, rent_bill, user_name,
    )
    return row["id"] if row else 0


async def update_invoice(
    conn: asyncpg.Connection,
    invoice_id: int,
    info=None,
    storage_bill=None,
    rent_bill=None,
    user_name=None,
    payment_date=None,
    payment_amount=None,
    user=None,
) -> int:
    prev = await conn.fetchrow(
        "SELECT payment_date, claim_id FROM invoice WHERE id = $1;", invoice_id
    )
    if not prev:
        return 0

    old_payment_date = prev["payment_date"]
    claim_id = prev["claim_id"]

    fields = []
    values = []
    if info is not None:
        fields.append(f"info = ${len(values)+1}")
        values.append(info)
    if storage_bill is not None:
        fields.append(f"storage_bill = ${len(values)+1}")
        values.append(storage_bill)
    if rent_bill is not None:
        fields.append(f"rent_bill = ${len(values)+1}")
        values.append(rent_bill)
    if user_name is not None:
        fields.append(f"user_name = ${len(values)+1}")
        values.append(user_name)
    if payment_date is not None:
        fields.append(f"payment_date = ${len(values)+1}")
        values.append(payment_date)
    if payment_amount is not None:
        fields.append(f"payment_amount = ${len(values)+1}")
        values.append(payment_amount)

    if not fields:
        return 0

    values.append(invoice_id)
    row = await conn.fetchrow(
        f"UPDATE invoice SET {', '.join(fields)} WHERE id = ${len(values)} RETURNING id, payment_date;",
        *values,
    )
    if not row:
        return 0

    return row["id"]


async def get_all_invoices(conn: asyncpg.Connection) -> list[dict]:
    rows = await conn.fetch("""
        SELECT i.id, i.claim_id, c.claimant_name, i.invoice_datetime,
               i.info, i.docs, i.storage_bill, i.rent_bill,
               i.user_name, i.payment_date, i.payment_amount
        FROM invoice i
        LEFT JOIN claims c ON i.claim_id = c.claim_id
        ORDER BY i.invoice_datetime DESC;
    """)
    return records_to_list(rows)


async def get_invoices_by_claim_id(conn: asyncpg.Connection, claim_id: str) -> list[dict]:
    rows = await conn.fetch(
        """SELECT id, claim_id, invoice_datetime, info, docs, storage_bill, rent_bill, user_name, payment_date, payment_amount
           FROM invoice WHERE claim_id = $1 ORDER BY invoice_datetime DESC;""",
        claim_id,
    )
    return records_to_list(rows)


async def insert_long_hire_invoice(
    conn: asyncpg.Connection, claim_id: str, amount: float, user_name: str
) -> int:
    row = await conn.fetchrow(
        "INSERT INTO long_hire_invoices (claim_id, amount, date_sent, user_name) VALUES ($1, $2, CURRENT_DATE, $3) RETURNING id;",
        claim_id, amount, user_name,
    )
    return row["id"] if row else 0


async def update_long_claim_invoice_sent(conn: asyncpg.Connection, claim_id: str) -> None:
    await conn.execute(
        "UPDATE long_claims SET invoice_sent = TRUE, date_sent = CURRENT_DATE WHERE id = $1;",
        claim_id,
    )


async def get_all_long_hire_invoices(conn: asyncpg.Connection) -> list[dict]:
    rows = await conn.fetch("""
        SELECT lhi.id, lhi.claim_id, lc.hirer_name, lhi.amount, lhi.date_sent, lhi.user_name
        FROM long_hire_invoices lhi
        LEFT JOIN long_claims lc ON lhi.claim_id = lc.id
        ORDER BY lhi.date_sent DESC;
    """)
    return records_to_list(rows)
