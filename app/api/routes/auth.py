from fastapi import APIRouter, HTTPException, status, Query
from app.db.pool import get_pool
from app.services.auth import login, refresh_access_token

router = APIRouter()


@router.post("/login")
async def login_user(username: str, password: str):
    pool = get_pool()
    async with pool.acquire() as conn:
        result = await login(conn, username, password)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    return result


@router.post("/refresh")
async def refresh_access_token_route(refresh_token: str = Query(...)):
    result = refresh_access_token(refresh_token)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    return result
