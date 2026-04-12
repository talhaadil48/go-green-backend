"""
Shared FastAPI dependencies.

Provides the ``get_current_user`` dependency that guards authenticated routes,
and the ``CurrentUser`` dataclass that is injected into route handlers.
"""

from dataclasses import dataclass
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from utils.jwt_handler import decode_token
from db.connection import DBConnection
from sql.combinedQueries import Queries

# OAuth2 bearer scheme – token is obtained via POST /auth/login
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


@dataclass
class CurrentUser:
    """
    Lightweight representation of the currently authenticated user.

    Attributes:
        id: Numeric user ID.
        username: Unique username string.
        role: Role string (e.g. ``"admin"`` or ``"user"``).
    """

    id: int
    username: str
    role: str


def get_current_user(token: str = Depends(oauth2_scheme)) -> CurrentUser:
    """
    Decode and validate a JWT bearer token, returning the authenticated user.

    This function is intended to be used as a FastAPI dependency:

    .. code-block:: python

        @router.get("/protected")
        async def protected_route(user: CurrentUser = Depends(get_current_user)):
            ...

    Args:
        token: JWT access token extracted from the ``Authorization`` header.

    Returns:
        A :class:`CurrentUser` instance for the token's subject.

    Raises:
        HTTPException(401): When the token is missing, expired, or invalid.
        HTTPException(401): When the user referenced by the token no longer exists.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    conn = DBConnection.get_connection()
    queries = Queries(conn)
    user = queries.get_user_by_id(user_id)

    if user is None:
        raise credentials_exception

    return CurrentUser(id=user["id"], username=user["username"], role=user["role"])
