"""
API package.

Exports the three top-level FastAPI routers that are registered in
``main.py``:

- ``forms_router``  – authenticated ``/api/*`` routes
  (delegated to :mod:`api.routes`)
- ``login_router``  – authentication ``/auth/*`` routes
  (defined in :mod:`api.login`)
- ``post_router``   – unauthenticated ``/post/*`` upsert routes
  (delegated to :mod:`api.post_routes`)
"""

from .forms import router as forms_router
from .login import router as login_router
from .post import router as post_router

__all__ = ["forms_router", "login_router", "post_router"]
