from fastapi import APIRouter, HTTPException, Request
from typing import Any, Dict
from app.db.pool import get_pool
from app.db.queries import long_claims as lc_q
from app.models.schemas import (
    LongClaimCreate, LongClaimUpdate, LongClaimCarAction
)

router = APIRouter()


# ── Static routes before parameterised /{claim_id} ───────────────────────────

@router.get("/long-claims")
async def get_all_long_claims():
    pool = get_pool()
    async with pool.acquire() as conn:
        claims = await lc_q.get_all_long_claims(conn)
    return {"success": True, "count": len(claims), "data": claims}


@router.get("/long/soft-deleted")
async def get_soft_deleted_long_claims():
    pool = get_pool()
    async with pool.acquire() as conn:
        claims = await lc_q.get_soft_deleted_long_claims(conn)
    return {"success": True, "count": len(claims), "data": claims}


@router.post("/long-claim")
async def create_long_claim(payload: LongClaimCreate):
    pool = get_pool()
    async with pool.acquire() as conn:
        if not payload.starting_date:
            payload.starting_date = None
        if not payload.ending_date:
            payload.ending_date = None
        long_claim_id = await lc_q.insert_long_claim(conn, payload.starting_date, payload.ending_date, payload.hirer_name)
    return {"success": True, "long_claim_id": long_claim_id}


@router.put("/long-claim")
async def update_long_claim(payload: LongClaimUpdate):
    pool = get_pool()
    async with pool.acquire() as conn:
        if not payload.starting_date:
            payload.starting_date = None
        if not payload.ending_date:
            payload.ending_date = None
        await lc_q.update_long_claim(conn, payload.long_claim_id, payload.starting_date, payload.ending_date, payload.hirer_name)
    return {"success": True, "message": "Long claim updated successfully"}


@router.put("/long-claim/{long_claim_id}/add-car")
async def add_car_to_long_claim_put(long_claim_id: str, payload: LongClaimCarAction):
    pool = get_pool()
    async with pool.acquire() as conn:
        await lc_q.add_car_to_long_claim(conn, long_claim_id, payload.car_id)
    return {"success": True, "message": "Car added to long claim"}


@router.post("/long-claim/{long_claim_id}/add-car")
async def add_car_to_long_claim(long_claim_id: str, payload: LongClaimCarAction):
    pool = get_pool()
    async with pool.acquire() as conn:
        await lc_q.add_car_to_long_claim(conn, long_claim_id, payload.car_id)
    return {"success": True, "message": "Car added to long claim"}


@router.delete("/long-claim/{long_claim_id}/remove-car/{car_id}")
async def remove_car_from_long_claim(long_claim_id: str, car_id: int):
    pool = get_pool()
    async with pool.acquire() as conn:
        await lc_q.remove_car_from_long_claim(conn, long_claim_id, car_id)
    return {"success": True, "message": "Car removed from long claim"}


@router.get("/long-claim/{long_claim_id}/cars")
async def get_cars_for_long_claim(long_claim_id: str):
    pool = get_pool()
    async with pool.acquire() as conn:
        data = await lc_q.get_cars_by_long_claim(conn, long_claim_id)
    return {"success": True, "count": len(data), "data": data}


@router.get("/long-claim/{long_claim_id}/daily-rates")
async def get_daily_rates(long_claim_id: str):
    pool = get_pool()
    async with pool.acquire() as conn:
        data = await lc_q.get_daily_rates_for_claim(conn, long_claim_id)
    rates = {item["car_id"]: item["daily_rate"] or 0 for item in data}
    return {"success": True, "data": rates}


@router.put("/long-claim/{long_claim_id}/daily-rate")
async def update_daily_rate(long_claim_id: str, body: Dict[str, Any]):
    from app.models.schemas import DailyRateUpdate
    car_id = body.get("car_id")
    daily_rate = body.get("daily_rate")
    pool = get_pool()
    async with pool.acquire() as conn:
        updated = await lc_q.update_daily_rate(conn, long_claim_id, car_id, daily_rate)
    return {"success": updated}


@router.put("/long-claim/{long_claim_id}/mark-invoice")
async def mark_invoice(long_claim_id: str):
    pool = get_pool()
    async with pool.acquire() as conn:
        updated = await lc_q.mark_invoice(conn, long_claim_id)
    if updated:
        return {"success": True, "message": "Invoice marked as true"}
    return {"success": False, "message": "Long claim not found"}


@router.get("/long-claims/{claim_id}")
async def get_long_claim_by_id(claim_id: str):
    pool = get_pool()
    async with pool.acquire() as conn:
        claim = await lc_q.get_long_claim_by_id(conn, claim_id)
    if not claim:
        return {"success": False, "message": f"Long claim with id {claim_id} not found"}
    return {"success": True, "data": claim}


@router.put("/long-claims/{claim_id}/restore")
async def restore_long_claim(claim_id: str):
    pool = get_pool()
    async with pool.acquire() as conn:
        restored = await lc_q.restore_claim(conn, claim_id)
    if restored == 0:
        return {"success": False, "message": "Claim not found"}
    return {"success": True, "message": f"Claim {claim_id} restored successfully."}


@router.delete("/long-claims/{claim_id}/delete")
async def delete_long_claim(claim_id: str):
    pool = get_pool()
    async with pool.acquire() as conn:
        deleted = await lc_q.delete_long_claim(conn, claim_id)
    if deleted == 0:
        return {"success": False, "message": "Claim not found"}
    return {"success": True, "message": f"Claim {claim_id} deleted permanently."}


@router.patch("/long-claims/{claim_id}/mark-deleted")
async def mark_recently_deleted(claim_id: str, payload: Dict[str, str]):
    deleted_by = payload.get("deleted_by")
    if not deleted_by:
        raise HTTPException(status_code=400, detail="deleted_by is required")

    pool = get_pool()
    async with pool.acquire() as conn:
        try:
            updated = await lc_q.mark_as_recently_deleted(conn, claim_id, deleted_by)
            if updated == 0:
                raise HTTPException(status_code=404, detail="Claim not found")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return {"success": True, "message": f"Claim {claim_id} marked as recently deleted by {deleted_by}."}
