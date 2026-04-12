"""
Claim summary route.

Routes:
    GET /api/summary/{claim_id}
"""

from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from db.connection import DBConnection
from sql.combinedQueries import Queries

router = APIRouter(tags=["summaries"])


@router.get("/summary/{claim_id}", response_model=Dict[str, Any])
async def get_claim_summary(claim_id: str):
    """
    Retrieve a comprehensive summary for a claim.

    The summary combines the claim itself with its accident data, rental
    agreement, storage form, and invoices in a single response.

    Args:
        claim_id: The unique claim identifier.

    Returns:
        Dict with keys ``claim``, ``accident_claim``, ``rental_agreement``,
        ``storage_form``, and ``invoices``.

    Raises:
        HTTPException(404): When the claim is not found.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)
    result = queries.get_claim_summary(claim_id)
    if not result:
        raise HTTPException(status_code=404, detail="Claim not found")
    return result
