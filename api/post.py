"""
Unauthenticated ``/post`` router — thin delegation module.

All route handlers have been moved into the ``api/post_routes/`` package.
This file re-exports the assembled ``post_router`` for backwards compatibility
with ``api/__init__.py``.

Import tree:
    api/post_routes/__init__.py
        ├── forms_post.py       – accident-claim, pre-inspection, cancellation,
        │                         storage, and rental upserts
        ├── documents_post.py   – claim-document upsert / read
        └── checklists_post.py  – hire-checklist upsert
"""

from api.post_routes import post_router as router  # noqa: F401 – re-exported for api/__init__.py
