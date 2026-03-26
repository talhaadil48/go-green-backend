"""JWT Bearer authentication dependency.

Usage in any router::

    from api.deps import get_current_user, CurrentUser
    from fastapi import Depends

    @router.get("/protected")
    async def protected(user: CurrentUser = Depends(get_current_user)):
        ...
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from utils.jwt_handler import decode_token

# HTTPBearer scheme – produces a padlock icon in the Swagger UI
security = HTTPBearer(
    scheme_name="Bearer",
    description="JWT Authorization header using the Bearer scheme",
)


class CurrentUser(BaseModel):
    """Parsed representation of the authenticated user from the JWT payload."""

    id: str
    username: str
    role: str
    permissions: dict = {}


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> CurrentUser:
    """Extract and validate the Bearer JWT, returning a :class:`CurrentUser`.

    Raises ``401 Unauthorized`` if the token is missing, invalid, or expired.
    """
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
