"""
Authenticated ``/api`` router — thin delegation module.

All route handlers have been moved into the ``api/routes/`` package so
that each domain area can be read, tested, and maintained independently.
This file re-exports the assembled ``api_router`` for backwards compatibility
with ``api/__init__.py``.

Import tree:
    api/routes/__init__.py
        ├── accident_claims.py
        ├── forms_routes.py
        ├── claims_routes.py
        ├── documents_routes.py
        ├── users_routes.py
        ├── cars_routes.py
        ├── long_claims_routes.py
        ├── claimants_routes.py
        ├── hire_checklists_routes.py
        ├── invoices_routes.py
        ├── fleet_routes.py
        ├── notifications_routes.py
        └── summaries_routes.py
"""

from api.routes import api_router as router  # noqa: F401 – re-exported for api/__init__.py
