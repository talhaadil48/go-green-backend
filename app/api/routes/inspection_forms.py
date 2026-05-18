from fastapi import APIRouter, HTTPException, Request
from typing import Any, Dict, List
from app.db.pool import get_pool
from app.db.queries import inspection_forms as insp_q

router = APIRouter()


# Static sub-path BEFORE parameterized /{claim_id}
@router.get("/pre-inspection-forms/inspection/{inspection_id}")
async def get_pre_inspection_form_by_inspection_id(inspection_id: str) -> Dict[str, Any]:
    pool = get_pool()
    async with pool.acquire() as conn:
        result = await insp_q.get_pre_inspection_form_by_inspection(conn, inspection_id)

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Pre-inspection form not found for this inspection_id",
        )

    response = {f"condition_{i}": result.get(f"condition_{i}", "") for i in range(1, 31)}
    response.update({
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
        "claim_id": result.get("claim_id"),
        "inspection_id": result.get("inspection_id"),
    })
    return response


@router.get("/pre-inspection-forms/{claim_id}")
async def get_pre_inspection_forms(claim_id: str) -> List[Dict[str, Any]]:
    pool = get_pool()
    async with pool.acquire() as conn:
        results = await insp_q.get_pre_inspection_form(conn, claim_id)

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
            "claim_id": result.get("claim_id"),
            "inspection_id": result.get("inspection_id"),
        })
        response_list.append(item)
    return response_list


@router.post("/pre-inspection-forms")
async def upsert_pre_inspection_form(request: Request) -> Dict[str, Any]:
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

    inspection_id = incoming_data.get("inspection_id")
    update_data = {k: v for k, v in incoming_data.items() if k not in ("claim_id", "inspection_id")}

    pool = get_pool()
    async with pool.acquire() as conn:
        result = await insp_q.upsert_pre_inspection_form(conn, claim_id, update_data, inspection_id)

    if not result:
        raise HTTPException(status_code=500, detail="Failed to save pre-inspection form")

    response = {f"condition_{i}": result.get(f"condition_{i}", "") for i in range(1, 31)}
    response.update({
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
        "claim_id": result["claim_id"],
        "inspection_id": result.get("inspection_id"),
    })
    return response
