from fastapi import APIRouter, HTTPException
from sql.combinedQueries import Queries
from db.connection import DBConnection
from utils.hashing import verify_password
from utils.jwt_utils import create_access_token, create_refresh_token

router = APIRouter(prefix="/auth", tags=["login"])

@router.post("/login")
async def login_user(username: str, password: str):
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    user = queries.get_user_by_username(username)
    if not user or not verify_password(password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    data = {
        "sub": user["id"],
        "role": user["role"],
        "permissions": user.get("permissions", {})
    }
    print(data)
    access_token = create_access_token({
        "sub": user["id"],
        "role": user["role"],
        "permissions": user.get("permissions", {})
    })
    refresh_token = create_refresh_token({"sub": user["id"]})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"],
            "permissions": user.get("permissions", {})
        }
    }
