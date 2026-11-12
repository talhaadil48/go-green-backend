from fastapi import APIRouter, HTTPException, Request
from typing import Any, Dict
from app.db.pool import get_pool
from app.db.queries import rental_agreements as ra_q
from app.services.rental_agreements import upsert_rental_agreement as svc_upsert

router = APIRouter()


@router.get("/rental-agreements/{claim_id}")
async def get_rental_agreement(claim_id: str) -> Dict[str, Any]:
    pool = get_pool()
    async with pool.acquire() as conn:
        result = await ra_q.get_rental_agreement(conn, claim_id)
    if not result:
        raise HTTPException(status_code=404, detail="Rental agreement not found")
    return result


@router.post("/rental-agreements")
async def upsert_rental_agreement(request: Request) -> Dict[str, Any]:
    try:
        incoming_data: dict = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or missing JSON body")

    claim_id = incoming_data.get("claim_id")
    if not claim_id or not isinstance(claim_id, str) or not claim_id.strip():
        raise HTTPException(
            status_code=400,
            detail="claim_id is required and must be a non-empty string in the request body",
        )

    update_data = {k: v for k, v in incoming_data.items() if k != "claim_id"}

    pool = get_pool()
    async with pool.acquire() as conn:
        result = await svc_upsert(conn, claim_id, update_data)

    if not result:
        raise HTTPException(status_code=500, detail="Failed to save rental agreement")
    return result
