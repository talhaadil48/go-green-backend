import asyncpg
from app.db.queries import notifications as notif_q
from app.db.queries import claims as claims_q


async def add_update_and_notify(
    conn: asyncpg.Connection, claim_id: str, new_update: dict, user_id: int
) -> bool:
    result = await claims_q.add_update(conn, claim_id, new_update)
    if result:
        message = new_update.get("message", "New update added")
        await notif_q.broadcast_notification(conn, user_id, claim_id, message)
    return result
