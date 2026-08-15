import asyncpg
from app.db.queries import invoice as inv_q
from app.db.queries import claims as claims_q
from datetime import datetime


async def create_invoice(
    conn: asyncpg.Connection,
    claim_id: str,
    info: str,
    docs: list,
    storage_bill: float,
    rent_bill: float,
    user_name: str,
) -> int:
    async with conn.transaction():
        if docs and "Rental Agreement" in docs:
            await claims_q.update_claim_status(conn, claim_id, "invoice sent")
            await claims_q.update_invoice_date(conn, claim_id, datetime.now())
        return await inv_q.insert_invoice(conn, claim_id, info, docs, storage_bill, rent_bill, user_name)


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
    async with conn.transaction():
        prev = await conn.fetchrow("SELECT payment_date, claim_id FROM invoice WHERE id = $1;", invoice_id)
        if not prev:
            return 0
        old_payment_date = prev["payment_date"]
        claim_id = prev["claim_id"]

        result_id = await inv_q.update_invoice(
            conn, invoice_id, info, storage_bill, rent_bill,
            user_name, payment_date, payment_amount, user,
        )

        if result_id and old_payment_date is None and payment_date is not None:
            from app.db.queries.claims import close_claim
            await close_claim(conn, claim_id, user or "system", "Invoice payment recorded")

        return result_id


async def create_long_hire_invoice(
    conn: asyncpg.Connection, claim_id: str, amount: float, user_name: str
) -> int:
    async with conn.transaction():
        invoice_id = await inv_q.insert_long_hire_invoice(conn, claim_id, amount, user_name)
        await inv_q.update_long_claim_invoice_sent(conn, claim_id)
        return invoice_id
