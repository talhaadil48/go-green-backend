"""Claims CRUD and lifecycle routes.

Covers:
- Creating, deleting, and updating claims
- Soft-delete, close, reopen, restore, and status update
- Listing all claims and recently-deleted claims
- Short-claim bill summary (rental + storage totals)
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
from psycopg2.errors import UniqueViolation

from api.deps import get_db, get_current_user, CurrentUser

router = APIRouter(tags=["claims"])


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic request models
# ─────────────────────────────────────────────────────────────────────────────

from pydantic import BaseModel  # noqa: E402


class SoftDeleteClaimRequest(BaseModel):
    deleted_by: str


class CloseClaimRequest(BaseModel):
    closed_by: str


# ─────────────────────────────────────────────────────────────────────────────
# CRUD
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/claims")
async def create_claim(payload: Dict[str, Any], queries=Depends(get_db)):
    """Create a new short claim.

    Required body fields: ``claimant_name``, ``claim_type``.
    Optional: ``council``, ``claim_id``.
    """
    claimant_name = payload.get("claimant_name")
    claim_type = payload.get("claim_type")
    council = payload.get("council")
    claim_id = payload.get("claim_id")

    if not all([claimant_name, claim_type]):
        raise HTTPException(
            status_code=400,
            detail="claimant_name, claim_type and council are required",
        )

    try:
        queries.insert_claim(
            claimant_name=claimant_name,
            claim_type=claim_type,
            council=council,
            claim_id=claim_id,
        )
    except UniqueViolation:
        queries.conn.rollback()
        raise HTTPException(status_code=409, detail="claim_id already exists")
    except Exception as e:
        queries.conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    return {"message": "Claim created successfully", "claim_id": claim_id or "auto-generated"}


@router.delete("/claims/{claim_id}")
async def delete_claim(claim_id: str, queries=Depends(get_db)):
    """Permanently delete a claim by its ID."""
    deleted = queries.delete_claim(claim_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Claim not found")
    return {"message": "Claim deleted successfully", "claim_id": claim_id}


@router.get("/claims")
async def get_all_claims(queries=Depends(get_db)) -> List[Dict[str, Any]]:
    """Return all active (non-soft-deleted) claims with their latest invoice summary."""
    return queries.get_all_claims()


@router.get("/claims/{claim_id}")
async def get_claim(claim_id: str, queries=Depends(get_db)) -> Dict[str, Any]:
    """Return a single claim by its ID."""
    result = queries.get_claim_by_id(claim_id)
    if not result:
        raise HTTPException(status_code=404, detail="Claim not found")
    return result


@router.put("/claims/{claim_id}")
async def update_claimant_name(
    claim_id: str, payload: Dict[str, Any], queries=Depends(get_db)
):
    """Update the claimant name on a claim.

    Required body field: ``claimant_name``.
    """
    new_name = payload.get("claimant_name")
    if not new_name:
        raise HTTPException(status_code=400, detail="claimant_name is required")

    try:
        updated = queries.update_claimant_name(claim_id=claim_id, new_name=new_name)
        if not updated:
            raise HTTPException(
                status_code=404, detail=f"Claim with id {claim_id} not found"
            )
    except Exception as e:
        queries.conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    return {"message": "Claimant name updated successfully", "claim_id": claim_id}


# ─────────────────────────────────────────────────────────────────────────────
# Claim lifecycle
# ─────────────────────────────────────────────────────────────────────────────

@router.put("/claims/{claim_id}/soft-delete")
async def soft_delete_claim(
    claim_id: str, request: SoftDeleteClaimRequest, queries=Depends(get_db)
):
    """Soft-delete a claim (marks it as recently deleted without removing it)."""
    deleted = queries.soft_delete_claim(claim_id, request.deleted_by)
    if not deleted:
        raise HTTPException(status_code=404, detail="Claim not found")
    return {
        "message": "Claim soft deleted successfully",
        "claim_id": claim_id,
        "deleted_by": request.deleted_by,
    }


@router.put("/claims/{claim_id}/close")
async def close_claim(
    claim_id: str, request: CloseClaimRequest, queries=Depends(get_db)
):
    """Close a claim and record who closed it."""
    closed = queries.close_claim(claim_id, request.closed_by)
    if not closed:
        raise HTTPException(status_code=404, detail="Claim not found")
    return {
        "message": "Claim closed successfully",
        "claim_id": claim_id,
        "closed_by": request.closed_by,
    }


@router.put("/claims/{claim_id}/reopen")
async def reopen_claim(claim_id: str, queries=Depends(get_db)):
    """Reopen a previously closed claim."""
    reopened = queries.reopen_claim(claim_id)
    if not reopened:
        raise HTTPException(status_code=404, detail="Claim not found")
    return {"message": "Claim reopened successfully", "claim_id": claim_id}


@router.put("/claims/{claim_id}/restore")
async def restore_claim(claim_id: str, queries=Depends(get_db)):
    """Restore a soft-deleted short claim."""
    restored = queries.restore_short_claim(claim_id)
    if not restored:
        raise HTTPException(status_code=409, detail="Claim not found")
    return {"message": "Claim restored successfully", "claim_id": claim_id}


@router.put("/claims/{claim_id}/status")
async def update_claim_status_api(
    claim_id: str, payload: Dict[str, str], queries=Depends(get_db)
):
    """Manually override the status field of a claim.

    Required body field: ``status`` (string).
    """
    status_value = payload.get("status")
    if not status_value:
        raise HTTPException(status_code=400, detail="status is required")

    try:
        updated = queries.update_claim_status(claim_id, status_value)
        if not updated:
            raise HTTPException(status_code=404, detail="claim_id not found")
    except Exception as e:
        queries.conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "message": "Status updated successfully",
        "claim_id": claim_id,
        "status": status_value,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Recently deleted claims
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/recently")
async def recently_deleted_claims(queries=Depends(get_db)):
    """Return all claims that have been soft-deleted."""
    claims = queries.get_recently_deleted_claims()
    if not claims:
        return {"count": 0, "claims": []}
    return {"count": len(claims), "claims": claims}


# ─────────────────────────────────────────────────────────────────────────────
# Bill summary
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/claim-bill/{claim_id}")
async def get_claim_bill(claim_id: str, queries=Depends(get_db)) -> Dict[str, Any]:
    """Return rental total and storage total for a short claim."""
    rental = queries.get_rental_by_claim(claim_id)
    storage = queries.get_storage_by_claim(claim_id)
    return {"rental": rental, "storage": storage}
