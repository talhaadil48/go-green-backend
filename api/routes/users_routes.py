"""
User-management routes.

Routes:
    GET    /api/users
    POST   /api/register
    PUT    /api/change-password
    DELETE /api/users/{user_id}
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from api.models.schemas import ChangePasswordRequest, CurrentUser, RegisterUserRequest
from db.connection import DBConnection
from sql.combinedQueries import Queries
from utils.hashing import hash_password
from utils.jwt_handler import decode_token

security = HTTPBearer(scheme_name="Bearer")


def _get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> CurrentUser:
    """Internal dependency to get the current user for this router."""
    token = credentials.credentials
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return CurrentUser(
        id=payload.get("sub"),
        username=payload.get("username", ""),
        role=payload.get("role", "user"),
        permissions=payload.get("permissions", {}),
    )


router = APIRouter(tags=["users"])


@router.get("/users")
async def get_all_users(
    current_user: CurrentUser = Depends(_get_current_user),
):
    """
    List all non-admin users.

    Admin access required.

    Args:
        current_user: The authenticated user (injected by dependency).

    Returns:
        Dict with ``users`` list.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )

    conn = DBConnection.get_connection()
    queries = Queries(conn)

    users = queries.get_all_non_admin_users()
    return {"users": users}


@router.post("/register")
async def register_user(
    data: RegisterUserRequest,
    current_user: CurrentUser = Depends(_get_current_user),
):
    """
    Register a new user account.

    Admin access required.

    Args:
        data: Registration payload with ``username``, ``password``, and ``role``.
        current_user: The authenticated user (injected by dependency).

    Returns:
        Confirmation message.

    Raises:
        HTTPException(403): When the caller is not an admin.
        HTTPException(400): When the username already exists.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )

    conn = DBConnection.get_connection()
    queries = Queries(conn)

    hashed_password = hash_password(data.password)
    user = queries.create_user(data.username, hashed_password, data.role)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists",
        )

    return {"message": "User created successfully"}


@router.put("/change-password")
async def change_password(
    data: ChangePasswordRequest,
    current_user: CurrentUser = Depends(_get_current_user),
):
    """
    Update the password for an existing user.

    Admin access required.

    Args:
        data: Payload with ``username`` and ``new_password``.
        current_user: The authenticated user (injected by dependency).

    Returns:
        Confirmation message.

    Raises:
        HTTPException(403): When the caller is not an admin.
        HTTPException(404): When the user is not found.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )

    conn = DBConnection.get_connection()
    queries = Queries(conn)

    hashed_password = hash_password(data.new_password)
    success = queries.change_user_password(data.username, hashed_password)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return {"message": "Password updated successfully"}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: CurrentUser = Depends(_get_current_user),
):
    """
    Delete a user account.

    Admin access required.

    Args:
        user_id: The numeric user ID.
        current_user: The authenticated user (injected by dependency).

    Returns:
        Confirmation message.

    Raises:
        HTTPException(403): When the caller is not an admin.
        HTTPException(404): When the user is not found.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )

    conn = DBConnection.get_connection()
    queries = Queries(conn)

    deleted = queries.delete_user(user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return {"message": "User deleted successfully"}
