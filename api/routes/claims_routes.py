"""
Claims management routes.

All CRUD and lifecycle operations for the ``claims`` table, including
status, lock, dispute, updates (JSONB), payment, and hire dates.

Routes:
    GET    /api/claims
    POST   /api/claims
    GET    /api/claims/{claim_id}
    PUT    /api/claims/{claim_id}
    DELETE /api/claims/{claim_id}
    PUT    /api/claims/{claim_id}/soft-delete
    PUT    /api/claims/{claim_id}/restore
    PUT    /api/claims/{claim_id}/close
    PUT    /api/claims/{claim_id}/reopen
    PUT    /api/claims/{claim_id}/status
    PUT    /api/claims/{claim_id}/disputed
    GET    /api/claims/{claim_id}/lock
    PUT    /api/claims/{claim_id}/lock
    PUT    /api/claims/ref-no/{claim_id}
    PUT    /api/claims/{claim_id}/payment
    PUT    /api/claims/{claim_id}/hire-vehicle-dates
    GET    /api/claims/{claim_id}/updates
    POST   /api/claims/{claim_id}/updates
    PUT    /api/claims/{claim_id}/updates/{update_id}
    GET    /api/recently
"""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request, status
from psycopg2.errors import UniqueViolation

from api.models.schemas import (
    ClaimLockUpdate,
    CloseClaimRequest,
    CurrentUser,
    HireVehicleDatesUpdate,
    PaymentUpdate,
    SoftDeleteClaimRequest,
)
from db.connection import DBConnection
from sql.combinedQueries import Queries
from utils.jwt_handler import decode_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer(scheme_name="Bearer")


def _get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> CurrentUser:
    """Internal dependency to get the current user for this router."""
    token = credentials.credentials
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return CurrentUser(
        id=payload.get("sub"),
        username=payload.get("username", ""),
        role=payload.get("role", "user"),
        permissions=payload.get("permissions", {}),
    )


router = APIRouter(tags=["claims"])


# ---------------------------------------------------------------------------
# List / Create / Delete
# ---------------------------------------------------------------------------

@router.get("/claims")
async def get_all_claims() -> list[Dict[str, Any]]:
    """
    Retrieve all non-deleted claims enriched with invoice and hire date data.

    Returns:
        List of claim dicts.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)
    return queries.get_all_claims()


@router.post("/claims")
async def create_claim(payload: Dict[str, Any]):
    """
    Create a new claim.

    Required body fields: ``claimant_name``, ``claim_type``.
    Optional body fields: ``council``, ``claim_id``.

    Returns:
        Confirmation dict with the ``claim_id``.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)

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
        conn.rollback()
        raise HTTPException(status_code=409, detail="claim_id already exists")
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    return {"message": "Claim created successfully", "claim_id": claim_id or "auto-generated"}


@router.get("/claims/{claim_id}")
async def get_claim(claim_id: str) -> Dict[str, Any]:
    """
    Retrieve a single claim by ID.

    Args:
        claim_id: The unique claim identifier.

    Returns:
        Full claim row as a dict.

    Raises:
        HTTPException(404): When not found.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    result = queries.get_claim_by_id(claim_id)
    if not result:
        raise HTTPException(status_code=404, detail="Claim not found")
    return result


@router.put("/claims/{claim_id}")
async def update_claim(claim_id: str, payload: Dict[str, Any]):
    """
    Update allowed fields on a claim.

    Only ``claimant_name``, ``council``, ``claim_type``, ``pay_date``,
    ``claim_start_date``, and ``invoice_date`` are accepted.

    Returns:
        Confirmation message.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    valid_fields = ["claimant_name", "council", "claim_type", "pay_date", "claim_start_date", "invoice_date"]
    update_data = {k: payload[k] for k in valid_fields if k in payload}

    if not update_data:
        raise HTTPException(status_code=400, detail="At least one valid field must be provided")

    try:
        updated = queries.update_claim_dynamic(claim_id, update_data)
        if not updated:
            raise HTTPException(status_code=404, detail=f"Claim with id {claim_id} not found")
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    return {"message": "Claim updated successfully", "claim_id": claim_id}


@router.delete("/claims/{claim_id}")
async def delete_claim(claim_id: str):
    """
    Hard-delete a claim.

    Args:
        claim_id: The unique claim identifier.

    Returns:
        Confirmation dict.

    Raises:
        HTTPException(404): When not found.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    deleted = queries.delete_claim(claim_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Claim not found")

    return {"message": "Claim deleted successfully", "claim_id": claim_id}


# ---------------------------------------------------------------------------
# Lifecycle (soft-delete, restore, close, reopen)
# ---------------------------------------------------------------------------

@router.put("/claims/{claim_id}/soft-delete")
async def soft_delete_claim(claim_id: str, request: SoftDeleteClaimRequest):
    """
    Soft-delete a claim (sets ``recently_deleted = TRUE``).

    Returns:
        Confirmation dict.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    deleted = queries.soft_delete_claim(claim_id, request.deleted_by)
    if not deleted:
        raise HTTPException(status_code=404, detail="Claim not found")

    return {
        "message": "Claim soft deleted successfully",
        "claim_id": claim_id,
        "deleted_by": request.deleted_by,
    }


@router.put("/claims/{claim_id}/restore")
async def restore_claim(claim_id: str):
    """
    Restore a soft-deleted short claim.

    Returns:
        Confirmation dict.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    restored = queries.restore_short_claim(claim_id)
    if not restored:
        raise HTTPException(status_code=409, detail="Claim not found")

    return {"message": "Claim restored successfully", "claim_id": claim_id}


@router.put("/claims/{claim_id}/close")
async def close_claim(claim_id: str, request: CloseClaimRequest):
    """
    Close a claim.

    Returns:
        Confirmation dict.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    closed = queries.close_claim(claim_id, request.closed_by, request.reason)
    if not closed:
        raise HTTPException(status_code=404, detail="Claim not found")

    return {
        "message": "Claim closed successfully",
        "claim_id": claim_id,
        "closed_by": request.closed_by,
    }


@router.put("/claims/{claim_id}/reopen")
async def reopen_claim(claim_id: str):
    """
    Re-open a closed claim.

    Returns:
        Confirmation dict.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    reopened = queries.reopen_claim(claim_id)
    if not reopened:
        raise HTTPException(status_code=404, detail="Claim not found")

    return {"message": "Claim reopened successfully", "claim_id": claim_id}


@router.get("/recently")
async def recently_deleted_claims():
    """
    List all recently soft-deleted claims.

    Returns:
        Dict with ``count`` and ``claims`` list.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    claims = queries.get_recently_deleted_claims()
    return {"count": len(claims), "claims": claims}


# ---------------------------------------------------------------------------
# Status / disputed
# ---------------------------------------------------------------------------

@router.put("/claims/{claim_id}/status")
async def update_claim_status_api(claim_id: str, payload: Dict[str, str]):
    """
    Update the ``status`` field on a claim.

    Required body field: ``status`` (string).
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    status_val = payload.get("status")
    if not status_val:
        raise HTTPException(status_code=400, detail="status is required")

    try:
        updated = queries.update_claim_status(claim_id, status_val)
        if not updated:
            raise HTTPException(status_code=404, detail="claim_id not found")
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    return {"message": "Status updated successfully", "claim_id": claim_id, "status": status_val}


@router.put("/claims/{claim_id}/disputed")
async def update_claim_disputed_api(claim_id: str, payload: Dict[str, Any]):
    """
    Update the ``is_disputed`` and / or ``dispute_reason`` fields on a claim.

    At least one of ``is_disputed`` or ``dispute_reason`` must be present.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    is_disputed = payload.get("is_disputed")
    dispute_reason = payload.get("dispute_reason")

    if is_disputed is None and dispute_reason is None:
        raise HTTPException(
            status_code=400,
            detail="At least one of is_disputed or dispute_reason is required",
        )

    try:
        updated = queries.update_claim_disputed(claim_id, is_disputed, dispute_reason)
        if not updated:
            raise HTTPException(status_code=404, detail="claim_id not found")
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "message": "Claim updated successfully",
        "claim_id": claim_id,
        "is_disputed": is_disputed,
        "dispute_reason": dispute_reason,
    }


# ---------------------------------------------------------------------------
# Lock
# ---------------------------------------------------------------------------

@router.get("/claims/{claim_id}/lock")
async def get_claim_lock_status(claim_id: str):
    """
    Retrieve the lock status for a claim.

    Returns:
        Dict with ``claim_id``, ``locked``, and ``locked_by``.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    claim = queries.get_claim_lock(claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    return {
        "claim_id": claim_id,
        "locked": claim.get("locked", False),
        "locked_by": claim.get("locked_by"),
    }


@router.put("/claims/{claim_id}/lock")
async def update_claim_lock(
    claim_id: str,
    update: ClaimLockUpdate,
    current_user: CurrentUser = Depends(_get_current_user),
):
    """
    Update the lock status on a claim.

    Args:
        claim_id: The unique claim identifier.
        update: Lock update payload.
        current_user: The authenticated user making the request.

    Returns:
        Dict confirming the new lock state.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    queries.update_claim_lock(
        claim_id=claim_id,
        locked=update.locked,
        locked_by=update.locked_by if update.locked else None,
    )

    return {
        "claim_id": claim_id,
        "locked": update.locked,
        "locked_by": update.locked_by if update.locked else None,
    }


# ---------------------------------------------------------------------------
# Ref-no / payment / hire-vehicle dates
# ---------------------------------------------------------------------------

@router.put("/claims/ref-no/{claim_id}")
async def update_ref_no(claim_id: str, request: Request) -> Dict[str, Any]:
    """
    Update the reference number on a claim.

    Required body field: ``ref_no`` (non-empty string).
    """
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    ref_no = data.get("ref_no")
    if not ref_no:
        raise HTTPException(status_code=400, detail="ref_no is required")

    conn = DBConnection.get_connection()
    queries = Queries(conn)

    result = queries.update_ref_no(claim_id, ref_no)
    if not result:
        raise HTTPException(status_code=404, detail="Claim not found")

    return {"claim_id": claim_id, "ref_no": ref_no}


@router.put("/claims/{claim_id}/payment")
async def update_payment_details(claim_id: str, payment_update: PaymentUpdate):
    """
    Update payment reference and / or pay date on a claim.

    When ``pay_date`` is newly set the claim status is automatically
    updated to ``"client paid"``.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    updated = queries.update_payment_details(
        claim_id,
        payment_update.payment,
        payment_update.pay_date,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Claim not found")

    return {"message": "Payment details updated successfully"}


@router.put("/claims/{claim_id}/hire-vehicle-dates")
async def update_hire_vehicle_dates(claim_id: str, payload: HireVehicleDatesUpdate):
    """
    Update the hire-vehicle date fields on a rental agreement.

    At least one of ``date_in`` or ``date_out`` must be provided.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    if "date_in" not in payload.dict() and "date_out" not in payload.dict():
        raise HTTPException(status_code=400, detail="At least one field must be provided")

    updated = queries.update_hire_vehicle_dates(claim_id, payload.date_in, payload.date_out)
    if not updated:
        raise HTTPException(status_code=404, detail="Claim not found")

    return {"message": "Hire vehicle dates updated successfully"}


# ---------------------------------------------------------------------------
# Updates (JSONB array)
# ---------------------------------------------------------------------------

@router.get("/claims/{claim_id}/updates")
async def get_updates(claim_id: str):
    """
    Return all update entries stored in the ``claims.updates`` JSONB array.

    Returns:
        Dict with ``count`` and ``data`` (list of update objects).
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    updates = queries.get_updates(claim_id)
    return {"count": len(updates), "data": updates}


@router.post("/claims/{claim_id}/updates")
async def add_update(
    claim_id: str,
    payload: dict,
    current_user: CurrentUser = Depends(_get_current_user),
):
    """
    Append a new update to the ``claims.updates`` JSONB array.

    Required body structure::

        {
            "update": {
                "id":      <int>,
                "message": "<string>",
                "date":    "<ISO date string>",
                "user":    "<username>"
            }
        }

    A broadcast notification is sent to all users after the update is saved.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    new_update = payload.get("update")
    if not new_update:
        raise HTTPException(status_code=400, detail="update is required")

    for field in ("id", "message", "date", "user"):
        if field not in new_update:
            raise HTTPException(status_code=400, detail=f"{field} is required")

    updated = queries.add_update(claim_id, new_update, current_user.id)
    if not updated:
        raise HTTPException(status_code=404, detail="Claim not found")

    return {"message": "Update added successfully"}


@router.put("/claims/{claim_id}/updates/{update_id}")
async def edit_update(claim_id: str, update_id: int, payload: dict):
    """
    Edit an existing update entry in the ``claims.updates`` JSONB array.

    The entry to edit is located by its ``id`` field.

    Required body structure::

        { "update": { <fields to merge> } }
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    new_data = payload.get("update")
    if not new_data:
        raise HTTPException(status_code=400, detail="update is required")

    updated = queries.edit_update(claim_id, update_id, new_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Update not found")

    return {"message": "Update edited successfully"}
