from fastapi import APIRouter
from app.db.pool import get_pool
from app.db.queries import fleet_history as fh_q

router = APIRouter()


@router.get("/fleet-history", response_model=None)
async def get_all_fleet_history():
    pool = get_pool()
    async with pool.acquire() as conn:
        history = await fh_q.get_all_fleet_history(conn)
    return {"count": len(history), "data": history}
