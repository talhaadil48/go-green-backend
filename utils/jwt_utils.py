from datetime import datetime, timedelta
from jose import JWTError, jwt
import os
from dotenv import load_dotenv
from datetime import timezone
from fastapi import Depends, HTTPException, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException, status

security = HTTPBearer()

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env.local'))

SECRET_KEY = 'my_key'
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7
print(SECRET_KEY)
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    print(SECRET_KEY)
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    print("Received credentials:", credentials)
    if not credentials:
        raise HTTPException(status_code=401, detail="No credentials passed")
    token = credentials.credentials
    print("Token received:", token)
    payload = verify_token(token)
    print("Payload:", payload)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")



if __name__ == "__main__":
    # Test token creation and verification
    sample_data = {"sub": "123", "role": "user" , "permissions": {}}
    access_token = create_access_token(sample_data)
    print("Access Token:", access_token)

    verified_payload = verify_token(access_token)
    print("Verified Payload:", verified_payload)