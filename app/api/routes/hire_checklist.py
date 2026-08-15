from fastapi import APIRouter, HTTPException, Request
from typing import Any, Dict, List
from app.db.pool import get_pool
from app.db.queries import hire_checklist as hc_q

router = APIRouter()


@router.get("/hire-checklists/{long_claim_id}/{car_id}/{claimant_id}")
async def get_hire_checklists(
    long_claim_id: str, car_id: int, claimant_id: int
) -> List[Dict[str, Any]]:
    pool = get_pool()
    async with pool.acquire() as conn:
        results = await hc_q.get_hire_checklists(conn, long_claim_id, car_id, claimant_id)

    response_list = []
    for result in results:
        item = {f"condition_{i}": result.get(f"condition_{i}", "") for i in range(1, 31)}
        item.update({
            "date": result.get("date", ""),
            "customer": result.get("customer", ""),
            "detailer": result.get("detailer", ""),
            "order_number": result.get("order_number", ""),
            "year": result.get("year", ""),
            "make": result.get("make", ""),
            "model": result.get("model", ""),
            "notes": result.get("notes", ""),
            "recommendations": result.get("recommendations", ""),
            "customer_signature": result.get("customer_signature"),
            "detailer_signature": result.get("detailer_signature"),
            "base_vehicle_image": result.get("base_vehicle_image"),
            "annotated_vehicle_image": result.get("annotated_vehicle_image"),
            "long_claim_id": result["long_claim_id"],
            "car_id": result["car_id"],
            "claimant_id": result["claimant_id"],
            "inspection_id": result["inspection_id"],
        })
        response_list.append(item)
    return response_list


@router.post("/hire-checklists")
async def upsert_hire_checklist(request: Request) -> Dict[str, Any]:
    try:
        incoming_data: dict = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or missing JSON body")

    long_claim_id = incoming_data.get("long_claim_id")
    car_id = incoming_data.get("car_id")
    claimant_id = incoming_data.get("claimant_id")

    if not all([long_claim_id, car_id is not None, claimant_id is not None]):
        raise HTTPException(status_code=400, detail="long_claim_id, car_id, and claimant_id are required")

    data = {k: v for k, v in incoming_data.items() if k not in ("long_claim_id", "car_id", "claimant_id")}

    pool = get_pool()
    async with pool.acquire() as conn:
        result = await hc_q.upsert_hire_checklist(conn, long_claim_id, int(car_id), int(claimant_id), data)

    if not result:
        raise HTTPException(status_code=500, detail="Failed to save hire checklist")
    return result
