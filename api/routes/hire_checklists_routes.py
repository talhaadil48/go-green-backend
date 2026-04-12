"""
Hire-checklist read routes.

Routes:
    GET /api/hire-checklists/{long_claim_id}/{car_id}/{claimant_id}
"""

from typing import Any, Dict, List

from fastapi import APIRouter

from db.connection import DBConnection
from sql.combinedQueries import Queries

router = APIRouter(tags=["hire-checklists"])


@router.get("/hire-checklists/{long_claim_id}/{car_id}/{claimant_id}")
async def get_hire_checklists(
    long_claim_id: str,
    car_id: int,
    claimant_id: int,
) -> List[Dict[str, Any]]:
    """
    Retrieve all hire checklists for a given long-claim / car / claimant combination.

    Multiple checklist rows may exist (e.g. pre-hire and post-hire inspections).

    Args:
        long_claim_id: The owning long-claim ID.
        car_id: The numeric car ID.
        claimant_id: The numeric claimant row ID.

    Returns:
        List of checklist dicts ordered by ``inspection_id`` ascending
        (empty list if none exist).
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    results = queries.get_hire_checklists(
        long_claim_id=long_claim_id,
        car_id=car_id,
        claimant_id=claimant_id,
    )

    response_list = []
    for result in results:
        item = {
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
            "long_claim_id": result["long_claim_id"],
            "car_id": result["car_id"],
            "claimant_id": result["claimant_id"],
            "inspection_id": result["inspection_id"],
        }
        response_list.append(item)

    return response_list
