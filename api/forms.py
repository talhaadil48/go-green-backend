"""Main API router (/api prefix).

This module is the **single source of truth** that :pyfile:`api/__init__.py`
imports as ``forms_router``.  All route handlers live in the sub-routers
under :mod:`api.routers`; this file simply assembles them.

``main.py`` usage (unchanged)::

    from api import forms_router
    app.include_router(forms_router)
"""

from fastapi import APIRouter, Depends

from api.deps.auth import get_current_user
from api.routers import claims, documents, forms_data, cars, invoices, long_hire, users

# Top-level router – preserves the original /api prefix and JWT guard
router = APIRouter(
    prefix="/api",
    tags=["claims"],
    dependencies=[Depends(get_current_user)],
)

# ── Domain sub-routers ────────────────────────────────────────────────────────
router.include_router(forms_data.router)
router.include_router(claims.router)
router.include_router(documents.router)
router.include_router(cars.router)
router.include_router(invoices.router)
router.include_router(long_hire.router)
router.include_router(users.router)
