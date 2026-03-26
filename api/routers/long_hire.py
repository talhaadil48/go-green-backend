"""Long-hire routes.

Covers:
- Long-claim CRUD, soft-delete / restore / permanent delete
- Claimant management
- Hire checklists
- Daily rate management
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional
from fastapi import Request

from api.deps import get_db
from api.schemas import (
    LongClaimCreate,
    LongClaimUpdate,
    LongClaimCarAction,
    ClaimantCreate,
    ClaimantUpdate,
    DailyRateUpdate,
)

router = APIRouter(tags=["long-hire"])


# ─────────────────────────────────────────────────────────────────────────────
# Long Claims CRUD
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/long-claim")
async def create_long_claim(payload: LongClaimCreate, queries=Depends(get_db)):
    """Create a new long-hire claim."""
    long_claim_id = queries.insert_long_claim(
        payload.starting_date or None,
        payload.ending_date or None,
        payload.hirer_name,
    )
    return {"success": True, "long_claim_id": long_claim_id}


@router.put("/long-claim")
async def update_long_claim(payload: LongClaimUpdate, queries=Depends(get_db)):
    """Update dates and hirer name on an existing long-hire claim."""
    queries.update_long_claim(
        payload.long_claim_id,
        payload.starting_date or None,
        payload.ending_date or None,
        payload.hirer_name,
    )
    return {"success": True, "message": "Long claim updated successfully"}


@router.get("/long-claims")
async def get_all_long_claims(queries=Depends(get_db)):
    """Return all active (non-soft-deleted) long-hire claims."""
    claims = queries.get_all_long_claims()
    return {"success": True, "count": len(claims), "data": claims}


@router.get("/long-claims/{claim_id}")
async def get_long_claim_by_id(claim_id: str, queries=Depends(get_db)):
    """Return a single long-hire claim by its ID."""
    claim = queries.get_long_claim_by_id(claim_id)
    if not claim:
        return {"success": False, "message": f"Long claim with id {claim_id} not found"}
    return {"success": True, "data": claim}


@router.put("/long-claims/{claim_id}/restore")
async def restore_long_claim(claim_id: str, queries=Depends(get_db)):
    """Restore a soft-deleted long-hire claim."""
    restored = queries.restore_claim(claim_id)
    if restored == 0:
        return {"success": False, "message": "Claim not found"}
    return {"success": True, "message": f"Claim {claim_id} restored successfully."}


@router.delete("/long-claims/{claim_id}/delete")
async def delete_long_claim(claim_id: str, queries=Depends(get_db)):
    """Permanently delete a long-hire claim."""
    deleted = queries.delete_long_claim(claim_id)
    if deleted == 0:
        return {"success": False, "message": "Claim not found"}
    return {"success": True, "message": f"Claim {claim_id} deleted permanently."}


@router.patch("/long-claims/{claim_id}/mark-deleted")
async def mark_recently_deleted(
    claim_id: str, payload: Dict[str, str], queries=Depends(get_db)
):
    """Soft-delete a long-hire claim.

    Required body field: ``deleted_by``.
    """
    deleted_by = payload.get("deleted_by")
    if not deleted_by:
        raise HTTPException(status_code=400, detail="deleted_by is required")

    try:
        updated = queries.mark_as_recently_deleted(claim_id, deleted_by)
        if updated == 0:
            raise HTTPException(status_code=404, detail="Claim not found")
    except Exception as e:
        queries.conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "success": True,
        "message": f"Claim {claim_id} marked as recently deleted by {deleted_by}.",
    }


@router.get("/long/soft-deleted")
async def get_soft_deleted_long_claims(queries=Depends(get_db)):
    """Return all soft-deleted long-hire claims."""
    claims = queries.get_soft_deleted_long_claims()
    return {"success": True, "count": len(claims), "data": claims}


# ─────────────────────────────────────────────────────────────────────────────
# Long Claim → Car assignment
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/long-claim/{long_claim_id}/add-car")
async def add_car_to_long_claim(
    long_claim_id: str, payload: LongClaimCarAction, queries=Depends(get_db)
):
    """Assign a car to a long-hire claim."""
    queries.add_car_to_long_claim(long_claim_id, payload.car_id)
    return {"success": True, "message": "Car added to long claim"}


@router.delete("/long-claim/{long_claim_id}/remove-car/{car_id}")
async def remove_car_from_long_claim(
    long_claim_id: str, car_id: int, queries=Depends(get_db)
):
    """Remove a car from a long-hire claim."""
    queries.remove_car_from_long_claim(long_claim_id, car_id)
    return {"success": True, "message": "Car removed from long claim"}


@router.get("/long-claim/{long_claim_id}/cars")
async def get_cars_for_long_claim(long_claim_id: str, queries=Depends(get_db)):
    """Return all cars currently assigned to a long-hire claim."""
    data = queries.get_cars_by_long_claim(long_claim_id)
    return {"success": True, "count": len(data), "data": data}


@router.put("/long-claim/{long_claim_id}/mark-invoice")
async def mark_invoice(long_claim_id: str, queries=Depends(get_db)):
    """Mark a long-hire claim as invoiced."""
    updated = queries.mark_invoice(long_claim_id)
    if updated:
        return {"success": True, "message": "Invoice marked as true"}
    return {"success": False, "message": "Long claim not found"}


# ─────────────────────────────────────────────────────────────────────────────
# Claimants
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/claimant")
async def create_claimant(payload: ClaimantCreate, queries=Depends(get_db)):
    """Create a new claimant record inside a long-hire claim."""
    claimant_id = queries.insert_claimant(
        payload.long_claim_id,
        payload.car_id,
        payload.start_date or None,
        payload.end_date or None,
        payload.miles,
        payload.name,
        payload.location,
        payload.delivery_charges or 0,
    )
    return {"success": True, "claimant_id": claimant_id}


@router.put("/claimant/{claimant_id}")
async def update_claimant(
    claimant_id: int, payload: ClaimantUpdate, queries=Depends(get_db)
):
    """Update a claimant's fields."""
    queries.update_claimant(
        claimant_id,
        start_date=payload.start_date,
        end_date=payload.end_date,
        miles=payload.miles,
        name=payload.name,
        location=payload.location,
        delivery_charges=payload.delivery_charges,
    )
    return {"success": True, "message": "Claimant updated successfully"}


@router.delete("/claimant/{claimant_id}")
async def delete_claimant(claimant_id: int, queries=Depends(get_db)):
    """Delete a claimant record."""
    deleted = queries.delete_claimant(claimant_id)
    if deleted:
        return {"success": True, "message": "Claimant deleted successfully"}
    return {"success": False, "message": "Claimant not found"}


@router.get("/claimant/{claimant_id}")
async def get_claimant_by_id(claimant_id: int, queries=Depends(get_db)):
    """Return claimant record(s) for a given claimant ID."""
    data = queries.get_claimant(claimant_id=claimant_id)
    return {"success": True, "count": len(data), "data": data}


@router.get("/claimants")
async def get_all_claimants(queries=Depends(get_db)):
    """Return all claimant records."""
    data = queries.get_all_claimants()
    return {"success": True, "count": len(data), "data": data}


@router.get("/car/{car_id}/claimants/{claim_id}")
async def get_claimants_for_car(
    car_id: int, claim_id: str, queries=Depends(get_db)
):
    """Return all claimants for a specific car within a long-hire claim."""
    data = queries.get_claimants_by_car(car_id, claim_id)
    return {"success": True, "count": len(data), "data": data}


@router.get("/long-hire/{long_claim_id}/claimants")
async def get_claimants_for_claim(long_claim_id: str, queries=Depends(get_db)):
    """Return all claimants for a long-hire claim, grouped by ``car_id``."""
    data = queries.get_claimants_for_claim(long_claim_id)
    claimants_by_car: Dict[int, list] = {}
    for claimant in data:
        cid = claimant["car_id"]
        claimants_by_car.setdefault(cid, []).append(claimant)
    return {"success": True, "count": len(data), "data": claimants_by_car}


# ─────────────────────────────────────────────────────────────────────────────
# Hire Checklists
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/hire-checklists")
async def upsert_hire_checklist(request: Request, queries=Depends(get_db)) -> Dict[str, Any]:
    """Create or update a hire checklist.

    Required body fields: ``long_claim_id`` (str), ``car_id`` (int), ``claimant_id`` (int).

    All other fields are optional and support partial updates.
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


    update_data = {
        k: v
        for k, v in incoming_data.items()
        if k not in ("long_claim_id", "car_id", "claimant_id", "inspection_id")
    }

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


@router.get("/hire-checklists/{long_claim_id}/{car_id}/{claimant_id}")
async def get_hire_checklists(
    long_claim_id: str,
    car_id: int,
    claimant_id: int,
    queries=Depends(get_db),
) -> List[Dict[str, Any]]:
    """Return all hire checklists for the given claim + car + claimant combination."""
    results = queries.get_hire_checklists(
        long_claim_id=long_claim_id, car_id=car_id, claimant_id=claimant_id
    )

    return [
        {
            **{f"condition_{i}": r.get(f"condition_{i}", "") for i in range(1, 31)},
            "date": r.get("date", ""),
            "customer": r.get("customer", ""),
            "detailer": r.get("detailer", ""),
            "order_number": r.get("order_number", ""),
            "year": r.get("year", ""),
            "make": r.get("make", ""),
            "model": r.get("model", ""),
            "notes": r.get("notes", ""),
            "recommendations": r.get("recommendations", ""),
            "customer_signature": r.get("customer_signature"),
            "detailer_signature": r.get("detailer_signature"),
            "base_vehicle_image": r.get("base_vehicle_image"),
            "annotated_vehicle_image": r.get("annotated_vehicle_image"),
            "long_claim_id": r["long_claim_id"],
            "car_id": r["car_id"],
            "claimant_id": r["claimant_id"],
            "inspection_id": r["inspection_id"],
        }
        for r in results
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Daily Rates
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/long-claim/{long_claim_id}/daily-rates")
async def get_daily_rates(long_claim_id: str, queries=Depends(get_db)):
    """Return a ``{car_id: daily_rate}`` map for a long-hire claim."""
    data = queries.get_daily_rates_for_claim(long_claim_id)
    rates = {item["car_id"]: item["daily_rate"] or 0 for item in data}
    return {"success": True, "data": rates}


@router.put("/long-claim/{long_claim_id}/daily-rate")
async def update_daily_rate(
    long_claim_id: str, body: DailyRateUpdate, queries=Depends(get_db)
):
    """Set the daily rate for a specific car in a long-hire claim."""
    updated = queries.update_daily_rate(long_claim_id, body.car_id, body.daily_rate)
    return {"success": updated}
