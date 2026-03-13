"""Claim documents routes.

Covers uploading/updating, reading, and deleting documents attached to claims.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

from api.deps import get_db

router = APIRouter(tags=["documents"])


@router.put("/claim-documents/{claim_id}")
async def upsert_claim_documents(
    claim_id: str, payload: Dict[str, Any], queries=Depends(get_db)
):
    """Create or update the documents map for a claim.

    Body must contain ``documents`` as a JSON object where keys are document
    names and values are URLs or base64 strings.
    """
    documents = payload.get("documents")
    if not isinstance(documents, dict):
        raise HTTPException(status_code=400, detail="documents must be a JSON object")

    queries.upsert_claim_documents(claim_id, documents)

    return {
        "message": "Documents saved successfully",
        "claim_id": claim_id,
        "documents": documents,
    }


@router.get("/claim-documents/{claim_id}", response_model=Dict[str, Any])
async def get_claim_documents(claim_id: str, queries=Depends(get_db)):
    """Return all documents stored for a claim."""
    result = queries.get_claim_documents(claim_id)
    if not result:
        raise HTTPException(status_code=404, detail="Documents not found")
    return {"claim_id": result["claim_id"], "documents": result.get("documents", {})}


@router.delete("/claim-documents/{claim_id}/{doc_name}")
async def delete_claim_document(
    claim_id: str, doc_name: str, queries=Depends(get_db)
):
    """Remove a single document entry by name from a claim's document map."""
    success = queries.delete_claim_document(claim_id, doc_name)
    if not success:
        raise HTTPException(
            status_code=404, detail="Document not found for this claim"
        )
    return {
        "message": f"Document '{doc_name}' deleted successfully",
        "claim_id": claim_id,
    }
