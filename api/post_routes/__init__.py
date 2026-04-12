"""
Unauthenticated ``/post`` router.

Assembles the form-upsert sub-routers into a single ``post_router`` that
is mounted under the ``/post`` prefix with no authentication dependency.

Sub-routers included:
    - :mod:`~api.post_routes.forms_post`      – accident-claim, pre-inspection,
      cancellation, storage, and rental upserts
    - :mod:`~api.post_routes.documents_post`  – claim-document upsert / read
    - :mod:`~api.post_routes.checklists_post` – hire-checklist upsert
"""

from fastapi import APIRouter

from .forms_post import router as forms_post_router
from .documents_post import router as documents_post_router
from .checklists_post import router as checklists_post_router

# Parent router — routes are served under /post with no auth dependency.
post_router = APIRouter(prefix="/post", tags=["post-claims"])

post_router.include_router(forms_post_router)
post_router.include_router(documents_post_router)
post_router.include_router(checklists_post_router)

__all__ = ["post_router"]
