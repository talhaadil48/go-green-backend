from fastapi import APIRouter, HTTPException
from typing import Any, Dict
from app.db.pool import get_pool
from app.db.queries import claimant as cl_q
from app.models.schemas import ClaimantCreate, ClaimantUpdate

router = APIRouter()


@router.get("/claimants")
async def get_all_claimants():
    pool = get_pool()
    async with pool.acquire() as conn:
        data = await cl_q.get_all_claimants(conn)
    return {"success": True, "count": len(data), "data": data}


@router.post("/claimant")
async def create_claimant(payload: ClaimantCreate):
    pool = get_pool()
    async with pool.acquire() as conn:
        try:
            claimant_id = await cl_q.insert_claimant(
                conn,
                payload.long_claim_id,
                payload.car_id,
                payload.start_date,
                payload.end_date,
                payload.miles,
                payload.name,
                payload.location,
                payload.delivery_charges or 0,
                payload.claimant_id,
                payload.ref_no,
            )
            return {"success": True, "claimant_id": claimant_id}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))


@router.put("/claimant/{claimant_id}")
async def update_claimant(claimant_id: int, payload: ClaimantUpdate):
    pool = get_pool()
    async with pool.acquire() as conn:
        try:
            await cl_q.update_claimant(
                conn,
                claimant_id,
                new_claimant_id=payload.claimant_id,
                ref_no=payload.ref_no,
                start_date=payload.start_date,
                end_date=payload.end_date,
                miles=payload.miles,
                name=payload.name,
                location=payload.location,
                delivery_charges=payload.delivery_charges,
            )
            return {"success": True, "message": "Claimant updated successfully"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))


@router.delete("/claimant/{claimant_id}")
async def delete_claimant(claimant_id: int):
    pool = get_pool()
    async with pool.acquire() as conn:
        deleted = await cl_q.delete_claimant(conn, claimant_id)
    if deleted:
        return {"success": True, "message": "Claimant deleted successfully"}
    return {"success": False, "message": "Claimant not found"}


@router.get("/claimant/{claimant_id}")
async def get_claimant_by_id(claimant_id: int):
    pool = get_pool()
    async with pool.acquire() as conn:
        data = await cl_q.get_claimant(conn, claimant_id=claimant_id)
    return {"success": True, "count": len(data), "data": data}


@router.get("/car/{car_id}/claimants/{claim_id}")
async def get_claimants_for_car(car_id: int, claim_id: str):
    pool = get_pool()
    async with pool.acquire() as conn:
        data = await cl_q.get_claimants_by_car(conn, car_id, claim_id)
    return {"success": True, "count": len(data), "data": data}


@router.get("/long-hire/{long_claim_id}/claimants")
async def get_claimants_for_claim(long_claim_id: str):
    pool = get_pool()
    async with pool.acquire() as conn:
        data = await cl_q.get_claimants_for_claim(conn, long_claim_id)

    claimants_by_car: Dict[Any, list] = {}
    for claimant in data:
        car_id = claimant["car_id"]
        if car_id not in claimants_by_car:
            claimants_by_car[car_id] = []
        claimants_by_car[car_id].append(claimant)

    return {"success": True, "count": len(data), "data": claimants_by_car}
