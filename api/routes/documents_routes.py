"""
Claim-document routes.

Routes:
    GET    /api/claim-documents/{claim_id}
    DELETE /api/claim-documents/{claim_id}/{doc_name}
"""

from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from db.connection import DBConnection
from sql.combinedQueries import Queries

router = APIRouter(tags=["claim-documents"])


@router.get("/claim-documents/{claim_id}", response_model=Dict[str, Any])
async def get_claim_documents(claim_id: str):
    """
    Retrieve the document store for a claim.

    Args:
        claim_id: The unique claim identifier.

    Returns:
        Dict with ``claim_id`` and ``documents`` (a JSONB object).

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


@router.delete("/claim-documents/{claim_id}/{doc_name}")
async def delete_claim_document(claim_id: str, doc_name: str):
    """
    Remove a single document entry from a claim's document store.

    Args:
        claim_id: The unique claim identifier.
        doc_name: The key of the document to remove.

    Returns:
        Confirmation dict.

    Raises:
        HTTPException(404): When the document or claim is not found.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    success = queries.delete_claim_document(claim_id, doc_name)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found for this claim")

    return {
        "message": f"Document '{doc_name}' deleted successfully",
        "claim_id": claim_id,
    }
