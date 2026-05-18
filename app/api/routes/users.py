from fastapi import APIRouter, HTTPException, Depends
from app.db.pool import get_pool
from app.db.queries import users as users_q
from app.api.dependencies import get_current_user
from app.models.schemas import CurrentUser, RegisterUserRequest, ChangePasswordRequest
from utils.hashing import hash_password

router = APIRouter()


@router.post("/register")
async def register_user(payload: RegisterUserRequest):
    hashed = hash_password(payload.password)
    pool = get_pool()
    async with pool.acquire() as conn:
        user = await users_q.create_user(conn, payload.username, hashed, payload.role)
    if not user:
        raise HTTPException(status_code=400, detail="Username already exists")
    return {"message": "User registered successfully", "user": user}


@router.put("/change-password")
async def change_password(payload: ChangePasswordRequest):
    hashed = hash_password(payload.new_password)
    pool = get_pool()
    async with pool.acquire() as conn:
        success = await users_q.change_user_password(conn, payload.username, hashed)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "Password changed successfully"}


@router.get("/users")
async def get_all_users(current_user: CurrentUser = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    pool = get_pool()
    async with pool.acquire() as conn:
        users = await users_q.get_all_non_admin_users(conn)
    return {"success": True, "count": len(users), "data": users}


@router.delete("/users/{user_id}")
async def delete_user(user_id: int, current_user: CurrentUser = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    pool = get_pool()
    async with pool.acquire() as conn:
        deleted = await users_q.delete_user(conn, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}
