from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.db.pool import create_pool, close_pool

# Route imports — /api prefix (JWT-protected via router dependency)
from app.api.routes import (
    auth,
    accident_claims,
    inspection_forms,
    cancellation_forms,
    storage_forms,
    rental_agreements,
    claims,
    cars,
    long_claims,
    claimant,
    hire_checklist,
    users,
    invoice,
    notifications,
    fleet_history,
    post_forms,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_pool()
    yield
    await close_pool()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── /auth routes ─────────────────────────────────────────────────────────────
app.include_router(auth.router, prefix="/auth", tags=["auth"])

# ── /api routes (all JWT-protected at dependency level per route) ─────────────
API_PREFIX = "/api"
API_TAGS_FORMS = ["forms"]

app.include_router(claims.router,            prefix=API_PREFIX, tags=API_TAGS_FORMS)
app.include_router(accident_claims.router,   prefix=API_PREFIX, tags=API_TAGS_FORMS)
# Static sub-path registered before parameterized in inspection_forms.py
app.include_router(inspection_forms.router,  prefix=API_PREFIX, tags=API_TAGS_FORMS)
app.include_router(cancellation_forms.router,prefix=API_PREFIX, tags=API_TAGS_FORMS)
app.include_router(storage_forms.router,     prefix=API_PREFIX, tags=API_TAGS_FORMS)
app.include_router(rental_agreements.router, prefix=API_PREFIX, tags=API_TAGS_FORMS)
# Static car routes (free/count, free, available, availability/{reg_no}) registered
# before parameterized /cars/{car_id}/long inside cars.py
app.include_router(cars.router,              prefix=API_PREFIX, tags=["cars"])
app.include_router(long_claims.router,       prefix=API_PREFIX, tags=["long-claims"])
app.include_router(claimant.router,          prefix=API_PREFIX, tags=["claimant"])
app.include_router(hire_checklist.router,    prefix=API_PREFIX, tags=["hire-checklist"])
app.include_router(users.router,             prefix=API_PREFIX, tags=["users"])
app.include_router(invoice.router,           prefix=API_PREFIX, tags=["invoice"])
# Static notification routes before parameterized in notifications.py
app.include_router(notifications.router,     prefix=API_PREFIX, tags=["notifications"])
app.include_router(fleet_history.router,     prefix=API_PREFIX, tags=["fleet"])

# ── /post routes (no authentication) ─────────────────────────────────────────
app.include_router(post_forms.router, prefix="/post", tags=["post-claims"])