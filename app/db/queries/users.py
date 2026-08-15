import asyncpg
from app.db.base import record_to_dict, records_to_list


async def get_user_by_username(conn: asyncpg.Connection, username: str) -> dict | None:
    row = await conn.fetchrow(
        "SELECT * FROM users WHERE username = $1;", username
    )
    return record_to_dict(row)


async def get_user_by_id(conn: asyncpg.Connection, user_id: str) -> dict | None:
    row = await conn.fetchrow(
        "SELECT id, username, role, permissions FROM users WHERE id = $1;",
        int(user_id),
    )
    return record_to_dict(row)


async def create_user(conn: asyncpg.Connection, username: str, password: str, role: str) -> dict | None:
    try:
        row = await conn.fetchrow(
            "INSERT INTO users (username, password, role) VALUES ($1, $2, $3) RETURNING id, username, role;",
            username, password, role,
        )
        return record_to_dict(row)
    except asyncpg.UniqueViolationError:
        return None


async def delete_user(conn: asyncpg.Connection, user_id: int) -> bool:
    row = await conn.fetchrow("DELETE FROM users WHERE id = $1 RETURNING id;", user_id)
    return row is not None


async def change_user_password(conn: asyncpg.Connection, username: str, new_password: str) -> bool:
    row = await conn.fetchrow(
        "UPDATE users SET password = $1 WHERE username = $2 RETURNING id;",
        new_password, username,
    )
    return row is not None


async def get_all_non_admin_users(conn: asyncpg.Connection) -> list[dict]:
    rows = await conn.fetch(
        "SELECT id, username, role FROM users WHERE role != 'admin' ORDER BY id ASC;"
    )
    return records_to_list(rows)
