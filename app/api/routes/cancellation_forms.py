from fastapi import APIRouter, HTTPException, Request
from typing import Any, Dict
from app.db.pool import get_pool
from app.db.queries import cancellation_forms as cf_q

router = APIRouter()


@router.get("/cancellation-forms/{claim_id}")
async def get_cancellation_form(claim_id: str) -> Dict[str, Any]:
    pool = get_pool()
    async with pool.acquire() as conn:
        result = await cf_q.get_cancellation_form(conn, claim_id)
    if not result:
        raise HTTPException(status_code=404, detail="Cancellation form not found")
    return {
        "name": result.get("name", ""),
        "address": result.get("address", ""),
        "postcode": result.get("postcode", ""),
        "email": result.get("email", ""),
        "cancellation_date": result.get("cancellation_date", ""),
        "cancellation_signature": result.get("cancellation_signature"),
        "claim_id": result["claim_id"],
    }


@router.post("/cancellation-forms")
async def upsert_cancellation_form(request: Request) -> Dict[str, Any]:
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
        result = await cf_q.upsert_cancellation_form(conn, claim_id, update_data)

    if not result:
        raise HTTPException(status_code=500, detail="Failed to save cancellation form")

    return {
        "name": result.get("name", ""),
        "address": result.get("address", ""),
        "postcode": result.get("postcode", ""),
        "email": result.get("email", ""),
        "cancellation_date": result.get("cancellation_date", ""),
        "cancellation_signature": result.get("cancellation_signature"),
        "claim_id": result["claim_id"],
    }
