"""
Document and recently-deleted routes for the ``/post`` prefix.

Routes:
    GET  /post/claim-documents/{claim_id}
    PUT  /post/claim-documents/{claim_id}
    GET  /post/recently
"""

from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from db.connection import DBConnection
from sql.combinedQueries import Queries

router = APIRouter(tags=["post-documents"])


@router.put("/claim-documents/{claim_id}")
async def upsert_claim_documents(
    claim_id: str,
    payload: Dict[str, Any],
):
    """
    Merge documents into a claim's document store.

    On conflict the new ``documents`` object is merged with the existing one,
    preserving previously stored keys.

    Args:
        claim_id: The unique claim identifier.
        payload: Must contain a ``documents`` key with a JSON object as its value.

    Returns:
        Confirmation dict with ``claim_id`` and the saved ``documents``.

    Raises:
        HTTPException(400): When ``documents`` is not a JSON object.
    """
    documents = payload.get("documents")
    if not isinstance(documents, dict):
        raise HTTPException(status_code=400, detail="documents must be a JSON object")

    conn = DBConnection.get_connection()
    queries = Queries(conn)
    queries.upsert_claim_documents(claim_id, documents)

    return {
        "message": "Documents saved successfully",
        "claim_id": claim_id,
        "documents": documents,
    }


@router.get("/claim-documents/{claim_id}", response_model=Dict[str, Any])
async def get_claim_documents(claim_id: str):
    """
    Retrieve the document store for a claim (unauthenticated read for form workflow).

    Args:
        claim_id: The unique claim identifier.

    Returns:
        Dict with ``claim_id`` and ``documents``.

    Raises:
        HTTPException(404): When no documents exist for the claim.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    result = queries.get_claim_documents(claim_id)
    if not result:
        raise HTTPException(status_code=404, detail="Documents not found")

    return {
        "claim_id": result["claim_id"],
        "documents": result.get("documents", {}),
    }


@router.get("/recently")
async def delete_recently_deleted_claims():
    """
    Permanently purge all claims that were soft-deleted more than 30 days ago.

    Returns:
        Dict with ``success`` and ``deleted_count``.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    deleted_count = queries.permanently_delete_recently_deleted_claims()
    return {"success": True, "deleted_count": deleted_count}
