"""Shared FastAPI dependencies (auth, database)."""
from .auth import get_current_user, CurrentUser
from .db import get_db

__all__ = ["get_current_user", "CurrentUser", "get_db"]
