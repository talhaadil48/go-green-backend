import asyncpg
from app.db.base import record_to_dict, records_to_list


async def broadcast_notification(
    conn: asyncpg.Connection, sender_id: int, title: str, message: str
) -> None:
    async with conn.transaction():
        row = await conn.fetchrow(
            "INSERT INTO notifications (created_by, title, message) VALUES ($1, $2, $3) RETURNING id;",
            sender_id, title, message,
        )
        notification_id = row["id"]
        await conn.execute(
            """INSERT INTO user_notifications (notification_id, user_id, is_read)
               SELECT $1, id, CASE WHEN id = $2 THEN TRUE ELSE FALSE END FROM users;""",
            notification_id, sender_id,
        )


async def get_user_notifications(conn: asyncpg.Connection, user_id: int, unread_only: bool = False) -> list[dict]:
    query = """
        SELECT n.id AS notification_id, n.created_by, n.title, n.message, un.is_read, n.created_at
        FROM notifications n
        JOIN user_notifications un ON n.id = un.notification_id
        WHERE un.user_id = $1
    """
    if unread_only:
        query += " AND un.is_read = FALSE"
    query += " ORDER BY n.created_at DESC;"
    rows = await conn.fetch(query, user_id)
    return records_to_list(rows)


async def mark_single_as_read(conn: asyncpg.Connection, notification_id: int, user_id: int) -> None:
    await conn.execute(
        "UPDATE user_notifications SET is_read = TRUE WHERE notification_id = $1 AND user_id = $2;",
        notification_id, user_id,
    )


async def mark_all_as_read(conn: asyncpg.Connection, user_id: int) -> None:
    await conn.execute(
        "UPDATE user_notifications SET is_read = TRUE WHERE user_id = $1 AND is_read = FALSE;",
        user_id,
    )


async def delete_expired_notifications(conn: asyncpg.Connection) -> int:
    result = await conn.execute(
        "DELETE FROM notifications WHERE created_at < NOW() - INTERVAL '7 days';"
    )
    parts = result.split()
    return int(parts[1]) if len(parts) == 2 else 0
