from datetime import timedelta
import asyncpg
from app.db.queries import users as users_q
from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
from utils.hashing import verify_password, hash_password
from utils.jwt_handler import create_access_token, create_refresh_token, decode_token


async def login(conn: asyncpg.Connection, username: str, password: str) -> dict | None:
    user = await users_q.get_user_by_username(conn, username)
    if not user:
        return None
    if not verify_password(password, user["password"]):
        return None

    token_data = {
        "sub": str(user["id"]),
        "username": user["username"],
        "role": user["role"],
        "permissions": user.get("permissions") or {},
    }
    access_token = create_access_token(
        token_data, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = create_refresh_token(token_data)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "role": user["role"],
    }


def refresh_access_token(refresh_token: str) -> dict | None:
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        return None

    token_data = {
        "sub": payload.get("sub"),
        "username": payload.get("username"),
        "role": payload.get("role"),
        "permissions": payload.get("permissions", {}),
    }
    access_token = create_access_token(
        token_data, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }
