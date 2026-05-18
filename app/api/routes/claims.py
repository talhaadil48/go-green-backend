from fastapi import APIRouter, HTTPException, Depends, Request, Query
from typing import Any, Dict, List
from app.db.pool import get_pool
from app.db.queries import claims as claims_q
from app.db.queries import rental_agreements as ra_q
from app.db.queries import storage_forms as sf_q
from app.api.dependencies import get_current_user
from app.models.schemas import (
    CurrentUser, SoftDeleteClaimRequest, CloseClaimRequest,
    ClaimLockUpdate, PaymentUpdate, HireVehicleDatesUpdate
)
from app.services.notifications import add_update_and_notify

router = APIRouter()


@router.post("/claims")
async def create_claim(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    claimant_name = body.get("claimant_name")
    claim_type = body.get("claim_type")
    council = body.get("council")
    claim_id = body.get("claim_id")

    if not all([claimant_name, claim_type]):
        raise HTTPException(status_code=400, detail="claimant_name, claim_type and council are required")

    pool = get_pool()
    async with pool.acquire() as conn:
        await claims_q.insert_claim(conn, claimant_name, claim_type, council, claim_id)

    return {
        "message": "Claim created successfully",
        "claim_id": claim_id or "auto-generated",
    }


@router.get("/claims")
async def get_all_claims() -> List[Dict[str, Any]]:
    pool = get_pool()
    async with pool.acquire() as conn:
        claims = await claims_q.get_all_claims(conn)
    return claims


@router.get("/recently")
async def recently_deleted_claims():
    pool = get_pool()
    async with pool.acquire() as conn:
        claims = await claims_q.get_recently_deleted_claims(conn)
    return {"count": len(claims), "data": claims}


@router.get("/summary/{claim_id}", response_model=None)
async def get_claim_summary(claim_id: str):
    pool = get_pool()
    async with pool.acquire() as conn:
        result = await claims_q.get_claim_summary(conn, claim_id)
    if not result:
        raise HTTPException(status_code=404, detail="Claim not found")
    return result


# Static sub-path routes BEFORE parameterized /{claim_id}
@router.put("/claims/ref-no/{claim_id}")
async def update_ref_no(claim_id: str, request: Request) -> Dict[str, Any]:
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    ref_no = data.get("ref_no")
    if not ref_no:
        raise HTTPException(status_code=400, detail="ref_no is required")

    pool = get_pool()
    async with pool.acquire() as conn:
        result = await claims_q.update_ref_no(conn, claim_id, ref_no)

    if not result:
        raise HTTPException(status_code=404, detail="Claim not found")
    return {"claim_id": claim_id, "ref_no": ref_no}


@router.get("/claims/{claim_id}")
async def get_claim_by_id(claim_id: str):
    pool = get_pool()
    async with pool.acquire() as conn:
        claim = await claims_q.get_claim_by_id(conn, claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    return claim


@router.put("/claims/{claim_id}")
async def update_claim(claim_id: str, request: Request):
    try:
        update_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    pool = get_pool()
    async with pool.acquire() as conn:
        updated = await claims_q.update_claim_dynamic(conn, claim_id, update_data)

    if not updated:
        raise HTTPException(status_code=404, detail="Claim not found")
    return {"message": "Claim updated successfully", "claim_id": claim_id}


@router.delete("/claims/{claim_id}")
async def delete_claim(claim_id: str):
    pool = get_pool()
    async with pool.acquire() as conn:
        deleted = await claims_q.delete_claim(conn, claim_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Claim not found")
    return {"message": "Claim deleted successfully", "claim_id": claim_id}


@router.put("/claims/{claim_id}/soft-delete")
async def soft_delete_claim(claim_id: str, payload: SoftDeleteClaimRequest):
    pool = get_pool()
    async with pool.acquire() as conn:
        deleted = await claims_q.soft_delete_claim(conn, claim_id, payload.deleted_by)
    if not deleted:
        raise HTTPException(status_code=404, detail="Claim not found")
    return {"message": "Claim soft-deleted successfully", "claim_id": claim_id}


@router.put("/claims/{claim_id}/close")
async def close_claim(claim_id: str, payload: CloseClaimRequest):
    pool = get_pool()
    async with pool.acquire() as conn:
        closed = await claims_q.close_claim(conn, claim_id, payload.closed_by, payload.reason)
    if not closed:
        raise HTTPException(status_code=404, detail="Claim not found")
    return {"message": "Claim closed successfully", "claim_id": claim_id}


@router.put("/claims/{claim_id}/reopen")
async def reopen_claim(claim_id: str):
    pool = get_pool()
    async with pool.acquire() as conn:
        reopened = await claims_q.reopen_claim(conn, claim_id)
    if not reopened:
        raise HTTPException(status_code=404, detail="Claim not found")
    return {"message": "Claim reopened successfully", "claim_id": claim_id}


@router.put("/claims/{claim_id}/restore")
async def restore_claim(claim_id: str):
    pool = get_pool()
    async with pool.acquire() as conn:
        restored = await claims_q.restore_short_claim(conn, claim_id)
    if not restored:
        raise HTTPException(status_code=409, detail="Claim not found")
    return {"message": "Claim restored successfully", "claim_id": claim_id}


@router.put("/claims/{claim_id}/status")
async def update_claim_status_api(claim_id: str, payload: Dict[str, str]):
    status = payload.get("status")
    if not status:
        raise HTTPException(status_code=400, detail="status is required")

    pool = get_pool()
    async with pool.acquire() as conn:
        try:
            updated = await claims_q.update_claim_status(conn, claim_id, status)
            if not updated:
                raise HTTPException(status_code=404, detail="claim_id not found")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return {"message": "Status updated successfully", "claim_id": claim_id, "status": status}


@router.put("/claims/{claim_id}/disputed")
async def update_claim_disputed_api(claim_id: str, payload: Dict[str, Any]):
    is_disputed = payload.get("is_disputed")
    dispute_reason = payload.get("dispute_reason")
    if is_disputed is None and dispute_reason is None:
        raise HTTPException(
            status_code=400,
            detail="At least one of is_disputed or dispute_reason is required",
        )

    pool = get_pool()
    async with pool.acquire() as conn:
        try:
            updated = await claims_q.update_claim_disputed(conn, claim_id, is_disputed, dispute_reason)
            if not updated:
                raise HTTPException(status_code=404, detail="claim_id not found")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return {
        "message": "Claim updated successfully",
        "claim_id": claim_id,
        "is_disputed": is_disputed,
        "dispute_reason": dispute_reason,
    }


@router.put("/claims/{claim_id}/lock", response_model=None)
async def update_claim_lock(
    claim_id: str,
    update: ClaimLockUpdate,
    current_user: CurrentUser = Depends(get_current_user),
):
    pool = get_pool()
    async with pool.acquire() as conn:
        await claims_q.update_claim_lock(
            conn,
            claim_id=claim_id,
            locked=update.locked,
            locked_by=update.locked_by if update.locked else None,
        )
    return {
        "claim_id": claim_id,
        "locked": update.locked,
        "locked_by": update.locked_by if update.locked else None,
    }


@router.get("/claims/{claim_id}/lock", response_model=None)
async def get_claim_lock_status(claim_id: str):
    pool = get_pool()
    async with pool.acquire() as conn:
        claim = await claims_q.get_claim_lock(conn, claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    return {
        "claim_id": claim_id,
        "locked": claim.get("locked", False),
        "locked_by": claim.get("locked_by"),
    }


@router.put("/claims/{claim_id}/payment")
async def update_payment_details(claim_id: str, payment_update: PaymentUpdate):
    pool = get_pool()
    async with pool.acquire() as conn:
        updated = await claims_q.update_payment_details(conn, claim_id, payment_update.payment, payment_update.pay_date)
    if not updated:
        raise HTTPException(status_code=404, detail="Claim not found")
    return {"message": "Payment details updated successfully"}


@router.put("/claims/{claim_id}/hire-vehicle-dates")
async def update_hire_vehicle_dates(claim_id: str, payload: HireVehicleDatesUpdate):
    if payload.date_in is None and payload.date_out is None:
        raise HTTPException(status_code=400, detail="At least one field must be provided")

    pool = get_pool()
    async with pool.acquire() as conn:
        updated = await claims_q.update_hire_vehicle_dates(conn, claim_id, payload.date_in, payload.date_out)
    if not updated:
        raise HTTPException(status_code=404, detail="Claim not found")
    return {"message": "Hire vehicle dates updated successfully"}


@router.post("/claims/{claim_id}/updates")
async def add_update(
    claim_id: str,
    payload: dict,
    current_user: CurrentUser = Depends(get_current_user),
):
    new_update = payload.get("update")
    if not new_update:
        raise HTTPException(status_code=400, detail="update is required")

    required_fields = ["id", "message", "date", "user"]
    for field in required_fields:
        if field not in new_update:
            raise HTTPException(status_code=400, detail=f"{field} is required")

    pool = get_pool()
    async with pool.acquire() as conn:
        updated = await add_update_and_notify(conn, claim_id, new_update, int(current_user.id))

    if not updated:
        raise HTTPException(status_code=404, detail="Claim not found")
    return {"message": "Update added successfully"}


@router.get("/claims/{claim_id}/updates")
async def get_updates(claim_id: str):
    pool = get_pool()
    async with pool.acquire() as conn:
        updates = await claims_q.get_updates(conn, claim_id)
    return {"count": len(updates), "data": updates}


@router.put("/claims/{claim_id}/updates/{update_id}")
async def edit_update(claim_id: str, update_id: int, payload: dict):
    new_data = payload.get("update")
    if not new_data:
        raise HTTPException(status_code=400, detail="update is required")

    pool = get_pool()
    async with pool.acquire() as conn:
        updated = await claims_q.edit_update(conn, claim_id, update_id, new_data)

    if not updated:
        raise HTTPException(status_code=404, detail="Update not found")
    return {"message": "Update edited successfully"}


@router.get("/claim-documents/{claim_id}")
async def get_claim_documents(claim_id: str):
    pool = get_pool()
    async with pool.acquire() as conn:
        result = await claims_q.get_claim_documents(conn, claim_id)
    if not result:
        raise HTTPException(status_code=404, detail="No documents found for this claim")
    return result


@router.put("/claim-documents/{claim_id}")
async def upsert_claim_documents(claim_id: str, request: Request):
    try:
        documents = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    pool = get_pool()
    async with pool.acquire() as conn:
        await claims_q.upsert_claim_documents(conn, claim_id, documents)
    return {"message": "Documents updated successfully", "claim_id": claim_id}


@router.delete("/claim-documents/{claim_id}/{doc_name}")
async def delete_claim_document(claim_id: str, doc_name: str):
    pool = get_pool()
    async with pool.acquire() as conn:
        deleted = await claims_q.delete_claim_document(conn, claim_id, doc_name)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": "Document deleted successfully", "claim_id": claim_id, "doc_name": doc_name}


@router.get("/claim-bill/{claim_id}")
async def get_claim_bill(claim_id: str) -> Dict[str, Any]:
    pool = get_pool()
    async with pool.acquire() as conn:
        rental = await ra_q.get_rental_by_claim(conn, claim_id)
        storage = await sf_q.get_storage_by_claim(conn, claim_id)
    return {"rental": rental, "storage": storage}
