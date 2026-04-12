"""
Hire-checklist upsert route for the ``/post`` prefix.

Routes:
    POST /post/hire-checklists
"""

from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request

from db.connection import DBConnection
from sql.combinedQueries import Queries

router = APIRouter(tags=["post-checklists"])


@router.post("/hire-checklists")
async def upsert_hire_checklist(request: Request) -> Dict[str, Any]:
    """
    Create or update a hire checklist.

    Required body fields:
        - ``long_claim_id`` (str)
        - ``car_id`` (int)
        - ``claimant_id`` (int)

    Optional body fields (any subset of the 30 condition columns and metadata):
        - ``inspection_id`` — when provided the corresponding existing row is
          updated rather than a new one being inserted.

    Returns:
        Flat dict of all hire-checklist columns.

    Raises:
        HTTPException(400): For invalid JSON or missing / wrong-typed required fields.
        HTTPException(500): When the upsert fails.
    """
    try:
        incoming_data: dict = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or missing JSON body")

    long_claim_id = incoming_data.get("long_claim_id")
    car_id = incoming_data.get("car_id")
    claimant_id = incoming_data.get("claimant_id")

    if not long_claim_id or not isinstance(long_claim_id, str) or not long_claim_id.strip():
        raise HTTPException(
            status_code=400,
            detail="long_claim_id is required and must be a non-empty string",
        )
    if not isinstance(car_id, int):
        raise HTTPException(status_code=400, detail="car_id must be an integer")
    if not isinstance(claimant_id, int):
        raise HTTPException(status_code=400, detail="claimant_id must be an integer")

    # Strip identifier fields from the update payload
    update_data = {
        k: v
        for k, v in incoming_data.items()
        if k not in ("long_claim_id", "car_id", "claimant_id", "inspection_id")
    }

    conn = DBConnection.get_connection()
    queries = Queries(conn)

    result = queries.upsert_hire_checklist(
        long_claim_id=long_claim_id,
        car_id=car_id,
        claimant_id=claimant_id,
        data=update_data,
    )

    if not result:
        raise HTTPException(status_code=500, detail="Failed to save hire checklist")

    return {
        "inspection_id": result["inspection_id"],
        "long_claim_id": result["long_claim_id"],
        "car_id": result["car_id"],
        "claimant_id": result["claimant_id"],
        **{f"condition_{i}": result.get(f"condition_{i}", "") for i in range(1, 31)},
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
    }
