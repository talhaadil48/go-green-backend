# go-green-backend

FastAPI backend for the Go Green fleet management system.

---

## Refactor Summary

This project was refactored from a flat, single-file structure using **psycopg2** (synchronous) to a **fully async architecture** using **asyncpg** with a clean, domain-separated module layout.

---

## Architecture

```
app/
├── core/
│   └── config.py              # Environment variable loading
│
├── db/
│   ├── pool.py                # asyncpg connection pool (create/close/get)
│   ├── base.py                # record_to_dict / records_to_list helpers
│   └── queries/               # Raw SQL — one file per domain
│       ├── accident_claims.py
│       ├── cancellation_forms.py
│       ├── cars.py
│       ├── claims.py
│       ├── claimant.py
│       ├── fleet_history.py
│       ├── hire_checklist.py
│       ├── inspection_forms.py
│       ├── invoice.py
│       ├── long_claims.py
│       ├── notifications.py
│       ├── rental_agreements.py
│       ├── storage_forms.py
│       └── users.py
│
├── models/
│   └── schemas.py             # All Pydantic request/response models
│
├── services/
│   ├── auth.py                # Login + token refresh
│   ├── invoice.py             # Invoice creation with status side-effects
│   ├── notifications.py       # Broadcast notification on claim update
│   └── rental_agreements.py   # Transactional rental upsert with fleet history
│
└── api/
    ├── dependencies.py        # JWT bearer auth dependency
    └── routes/
        ├── auth.py
        ├── accident_claims.py
        ├── cancellation_forms.py
        ├── cars.py
        ├── claims.py
        ├── claimant.py
        ├── fleet_history.py
        ├── hire_checklist.py
        ├── inspection_forms.py
        ├── invoice.py
        ├── long_claims.py
        ├── notifications.py
        ├── post_forms.py      # /post prefix — no auth
        ├── rental_agreements.py
        ├── storage_forms.py
        └── users.py
```

---

## Files Changed

| File | Change |
|---|---|
| `main.py` | Replaced with async lifespan + new route imports |
| `requirements.txt` | Replaced `psycopg2-binary` with `asyncpg>=0.29.0` |
| `app/` (entire directory) | **New** — all refactored code lives here |
| `api/`, `db/connection.py`, `sql/` | **Kept unchanged** — old code preserved for reference |

---

## Bug Fixes

| Bug | Fix |
|---|---|
| Singleton DB connection (`DBConnection.get_connection()`) | Replaced with `asyncpg.create_pool()` — each request acquires its own connection |
| psycopg2 sync calls blocking the event loop | All DB calls are now `async/await` with asyncpg |
| Connection never closed on errors | Pool's `acquire()` context manager ensures automatic release |
| Route shadowing risk (`/cars/free/count`, `/cars/free`, `/cars/available` vs `/cars/{car_id}/long`) | Static routes registered before parameterized routes within each router file |

---

## Breaking Changes

**None.** All API routes, request body structures, and JSON response formats are unchanged.

---

## Migration Notes

### For the frontend — no changes required.

Every route path, HTTP method, request body field, and JSON response key is identical to the previous version.

### For deployment

1. **Install new dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   `asyncpg` replaces `psycopg2-binary`.

2. **Database URL format** — `asyncpg` expects a standard PostgreSQL DSN:
   ```
   DATABASE_URL=postgresql://user:password@host:port/dbname
   ```
   If your existing `DATABASE_URL` starts with `postgresql+psycopg2://`, update it to `postgresql://`.

3. **Start the server** (unchanged):
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

---

## Environment Variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | JWT signing secret |

Loaded from `.env.local` in the project root.
