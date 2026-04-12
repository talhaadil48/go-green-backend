"""
Authentication routes.

Routes:
    POST /auth/login   – exchange credentials for JWT access + refresh tokens
    POST /auth/refresh – exchange a refresh token for a new access token pair
"""

from fastapi import APIRouter, HTTPException, Query, status
from sql.combinedQueries import Queries
from db.connection import DBConnection
from utils.hashing import verify_password
from utils.jwt_handler import create_access_token, create_refresh_token, decode_token

router = APIRouter(prefix="/auth", tags=["login"])


@router.post("/login")
async def login_user(username: str, password: str):
    """
    Authenticate a user and return a JWT access / refresh token pair.

    Args:
        username: The user's username (query parameter).
        password: The plain-text password (query parameter).

    Returns:
        Dict with ``access_token``, ``refresh_token``, ``token_type``,
        and ``user`` (id, username, role, permissions).

    Raises:
        HTTPException(400): When credentials are invalid.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    user = queries.get_user_by_username(username)

    if not user or not verify_password(password, user["password"]):
        raise HTTPException(status_code=400, detail="Invalid username or password")

    token_data = {
        "sub": str(user["id"]),
        "username": user["username"],
        "role": user["role"],
        "permissions": user.get("permissions", {}),
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token({"sub": str(user["id"])})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"],
            "permissions": user.get("permissions", {}),
        },
    }


@router.post("/refresh")
async def refresh_access_token(refresh_token: str = Query(...)):
    """
    Exchange a valid refresh token for a new access / refresh token pair.

    Args:
        refresh_token: A valid JWT refresh token (query parameter).

    Returns:
        Dict with ``access_token``, ``refresh_token``, and ``token_type``.

    Raises:
        HTTPException(401): When the token is invalid, expired, or not a
            refresh token.
        HTTPException(404): When the user referenced by the token no longer
            exists.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    payload = decode_token(refresh_token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user = queries.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    new_access_token = create_access_token({
        "sub": str(user["id"]),
        "username": user["username"],
        "role": user["role"],
        "permissions": user.get("permissions", {}),
    })

    new_refresh_token = create_refresh_token({"sub": str(user["id"])})

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }
