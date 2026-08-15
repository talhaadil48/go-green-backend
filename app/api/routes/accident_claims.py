from fastapi import APIRouter, HTTPException, Request
from typing import Any, Dict
from app.db.pool import get_pool
from app.db.queries import accident_claims as ac_q

router = APIRouter()


@router.get("/accident-claims/{claim_id}")
async def get_accident_claim(claim_id: str) -> Dict[str, Any]:
    pool = get_pool()
    async with pool.acquire() as conn:
        result = await ac_q.get_accident_claim(conn, claim_id)
    if not result:
        raise HTTPException(status_code=404, detail="Accident claim not found")
    return result


@router.post("/accident-claims/{claim_id}")
async def upsert_accident_claim(claim_id: str, request: Request) -> Dict[str, Any]:
    try:
        incoming_data: dict = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or missing JSON body")

    if not claim_id or not claim_id.strip():
        raise HTTPException(status_code=400, detail="claim_id is required")

    update_data = {k: v for k, v in incoming_data.items() if k != "claim_id"}

    pool = get_pool()
    async with pool.acquire() as conn:
        result = await ac_q.upsert_accident_claim(conn, claim_id, update_data)

    if not result:
        raise HTTPException(status_code=500, detail="Failed to save accident claim")
    return result


@router.put("/accident-claims/{claim_id}/direction")
async def update_drawing_direction(claim_id: str, request: Request) -> Dict[str, Any]:
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    direction_type = data.get("type")
    value = data.get("value")
    json_data = data.get("json_data")

    if direction_type not in ["before", "after"]:
        raise HTTPException(status_code=400, detail="type must be 'before' or 'after'")
    if value is None:
        raise HTTPException(status_code=400, detail="value is required")

    value_column = "direction_before_drawing" if direction_type == "before" else "direction_after_drawing"
    json_column = "json_before" if direction_type == "before" else "json_after"

    pool = get_pool()
    async with pool.acquire() as conn:
        result = await ac_q.upsert_accident_claim_with_json(conn, claim_id, value_column, value, json_column, json_data)

    return {
        "claim_id": claim_id,
        "updated_value_column": value_column,
        "value": value,
    }
