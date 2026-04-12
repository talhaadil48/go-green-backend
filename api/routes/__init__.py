"""
Authenticated ``/api`` router.

Assembles every domain sub-router into a single ``api_router`` that is
mounted under the ``/api`` prefix with a global JWT-authentication dependency.

Sub-routers included:
    - :mod:`~api.routes.accident_claims`
    - :mod:`~api.routes.forms_routes`
    - :mod:`~api.routes.claims_routes`
    - :mod:`~api.routes.documents_routes`
    - :mod:`~api.routes.users_routes`
    - :mod:`~api.routes.cars_routes`
    - :mod:`~api.routes.long_claims_routes`
    - :mod:`~api.routes.claimants_routes`
    - :mod:`~api.routes.hire_checklists_routes`
    - :mod:`~api.routes.invoices_routes`
    - :mod:`~api.routes.fleet_routes`
    - :mod:`~api.routes.notifications_routes`
    - :mod:`~api.routes.summaries_routes`
"""

from fastapi import APIRouter

from .accident_claims import router as accident_claims_router
from .forms_routes import router as forms_router
from .claims_routes import router as claims_router
from .documents_routes import router as documents_router
from .users_routes import router as users_router
from .cars_routes import router as cars_router
from .long_claims_routes import router as long_claims_router
from .claimants_routes import router as claimants_router
from .hire_checklists_routes import router as hire_checklists_router
from .invoices_routes import router as invoices_router
from .fleet_routes import router as fleet_router
from .notifications_routes import router as notifications_router
from .summaries_routes import router as summaries_router

# Parent router — all routes mounted here will be served under /api
# and protected by the JWT dependency declared in each sub-router.
api_router = APIRouter(prefix="/api", tags=["api"])

api_router.include_router(accident_claims_router)
api_router.include_router(forms_router)
api_router.include_router(claims_router)
api_router.include_router(documents_router)
api_router.include_router(users_router)
api_router.include_router(cars_router)
api_router.include_router(long_claims_router)
api_router.include_router(claimants_router)
api_router.include_router(hire_checklists_router)
api_router.include_router(invoices_router)
api_router.include_router(fleet_router)
api_router.include_router(notifications_router)
api_router.include_router(summaries_router)

__all__ = ["api_router"]
