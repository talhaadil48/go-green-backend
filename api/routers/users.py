"""User management routes (admin-only).

All endpoints here require the caller to be an *admin* user.
"""

from fastapi import APIRouter, HTTPException, Depends, status

from pydantic import BaseModel
from api.deps import get_db, get_current_user, CurrentUser
from utils.hashing import hash_password

router = APIRouter(tags=["users"])


class RegisterUserRequest(BaseModel):
    username: str
    password: str
    role: str


class ChangePasswordRequest(BaseModel):
    username: str
    new_password: str


def _require_admin(current_user: CurrentUser) -> None:
    """Raise 403 if the caller is not an admin."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )


@router.post("/register")
async def register_user(
    data: RegisterUserRequest,
    current_user: CurrentUser = Depends(get_current_user),
    queries=Depends(get_db),
):
    """Create a new user account (admin only)."""
    _require_admin(current_user)
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
    current_user: CurrentUser = Depends(get_current_user),
    queries=Depends(get_db),
):
    """Change another user's password (admin only)."""
    _require_admin(current_user)
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
    current_user: CurrentUser = Depends(get_current_user),
    queries=Depends(get_db),
):
    """Delete a user account by ID (admin only)."""
    _require_admin(current_user)
    deleted = queries.delete_user(user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return {"message": "User deleted successfully"}


@router.get("/users")
async def get_all_users(
    current_user: CurrentUser = Depends(get_current_user),
    queries=Depends(get_db),
):
    """Return all non-admin user accounts (admin only)."""
    _require_admin(current_user)
    users = queries.get_all_non_admin_users()
    return {"users": users}
