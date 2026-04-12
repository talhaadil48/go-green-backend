"""
Long-claims management routes.

Routes:
    GET    /api/long-claims
    POST   /api/long-claim
    PUT    /api/long-claim
    GET    /api/long-claims/{claim_id}
    PUT    /api/long-claim/{long_claim_id}/mark-invoice
    PUT    /api/long-claims/{claim_id}/restore
    DELETE /api/long-claims/{claim_id}/delete
    PATCH  /api/long-claims/{claim_id}/mark-deleted
    GET    /api/long/soft-deleted
    POST   /api/long-claim/{long_claim_id}/add-car
    DELETE /api/long-claim/{long_claim_id}/remove-car/{car_id}
    GET    /api/long-claim/{long_claim_id}/cars
    GET    /api/long-claim/{long_claim_id}/daily-rates
    PUT    /api/long-claim/{long_claim_id}/daily-rate
    GET    /api/long-hire/{long_claim_id}/claimants
"""

from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from api.models.schemas import DailyRateUpdate, LongClaimCarAction, LongClaimCreate, LongClaimUpdate
from db.connection import DBConnection
from sql.combinedQueries import Queries

router = APIRouter(tags=["long-claims"])


@router.get("/long-claims")
async def get_all_long_claims():
    """
    Retrieve all non-deleted long claims.

    Returns:
        Dict with ``success``, ``count``, and ``data``.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)
    claims = queries.get_all_long_claims()
    return {"success": True, "count": len(claims), "data": claims}


@router.post("/long-claim")
async def create_long_claim(payload: LongClaimCreate):
    """
    Create a new long claim.

    Args:
        payload: Start date, end date, and optional hirer name.

    Returns:
        Dict with ``success`` and ``long_claim_id``.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    starting_date = payload.starting_date or None
    ending_date = payload.ending_date or None

    long_claim_id = queries.insert_long_claim(starting_date, ending_date, payload.hirer_name)
    return {"success": True, "long_claim_id": long_claim_id}


@router.put("/long-claim")
async def update_long_claim(payload: LongClaimUpdate):
    """
    Update date and hirer name fields on a long claim.

    Args:
        payload: Long claim ID plus optional updated fields.

    Returns:
        Confirmation dict.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    starting_date = payload.starting_date or None
    ending_date = payload.ending_date or None

    queries.update_long_claim(
        payload.long_claim_id, starting_date, ending_date, payload.hirer_name
    )
    return {"success": True, "message": "Long claim updated successfully"}


@router.get("/long-claims/{claim_id}")
async def get_long_claim_by_id(claim_id: str):
    """
    Retrieve a single long claim by ID.

    Args:
        claim_id: The long-claim ID.

    Returns:
        Dict with ``success`` and ``data`` (claim row).
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)
    claim = queries.get_long_claim_by_id(claim_id)
    if not claim:
        return {"success": False, "message": f"Long claim with id {claim_id} not found"}
    return {"success": True, "data": claim}


@router.put("/long-claim/{long_claim_id}/mark-invoice")
async def mark_invoice(long_claim_id: str):
    """
    Mark a long claim's invoice as sent.

    Args:
        long_claim_id: The long-claim ID.

    Returns:
        Dict indicating success or failure.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)
    updated = queries.mark_invoice(long_claim_id)
    if updated:
        return {"success": True, "message": "Invoice marked as true"}
    return {"success": False, "message": "Long claim not found"}


@router.put("/long-claims/{claim_id}/restore")
async def restore_long_claim(claim_id: str):
    """
    Restore a soft-deleted long claim.

    Args:
        claim_id: The long-claim ID.

    Returns:
        Dict indicating success or failure.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)
    restored = queries.restore_claim(claim_id)
    if restored == 0:
        return {"success": False, "message": "Claim not found"}
    return {"success": True, "message": f"Claim {claim_id} restored successfully."}


@router.delete("/long-claims/{claim_id}/delete")
async def delete_long_claim(claim_id: str):
    """
    Hard-delete a long claim.

    Args:
        claim_id: The long-claim ID.

    Returns:
        Dict indicating success or failure.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)
    deleted = queries.delete_long_claim(claim_id)
    if not deleted:
        return {"success": False, "message": "Claim not found"}
    return {"success": True, "message": f"Claim {claim_id} deleted permanently."}


@router.patch("/long-claims/{claim_id}/mark-deleted")
async def mark_recently_deleted(claim_id: str, payload: Dict[str, str]):
    """
    Soft-delete a long claim by marking it as recently deleted.

    Required body field: ``deleted_by`` (username).
    """
    deleted_by = payload.get("deleted_by")
    if not deleted_by:
        raise HTTPException(status_code=400, detail="deleted_by is required")

    conn = DBConnection.get_connection()
    queries = Queries(conn)

    try:
        updated = queries.mark_as_recently_deleted(claim_id, deleted_by)
        if updated == 0:
            raise HTTPException(status_code=404, detail="Claim not found")
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "success": True,
        "message": f"Claim {claim_id} marked as recently deleted by {deleted_by}.",
    }


@router.get("/long/soft-deleted")
async def get_soft_deleted_long_claims():
    """
    Retrieve all soft-deleted long claims.

    Returns:
        Dict with ``success``, ``count``, and ``data``.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)
    claims = queries.get_soft_deleted_long_claims()
    return {"success": True, "count": len(claims), "data": claims}


# ---------------------------------------------------------------------------
# Car associations
# ---------------------------------------------------------------------------

@router.post("/long-claim/{long_claim_id}/add-car")
async def add_car_to_long_claim(long_claim_id: str, payload: LongClaimCarAction):
    """
    Link a car to a long claim.

    Args:
        long_claim_id: The long-claim ID.
        payload: Contains ``car_id``.

    Returns:
        Confirmation dict.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)
    queries.add_car_to_long_claim(long_claim_id, payload.car_id)
    return {"success": True, "message": "Car added to long claim"}


@router.delete("/long-claim/{long_claim_id}/remove-car/{car_id}")
async def remove_car_from_long_claim(long_claim_id: str, car_id: int):
    """
    Remove a car from a long claim.

    Args:
        long_claim_id: The long-claim ID.
        car_id: The numeric car ID.

    Returns:
        Confirmation dict.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)
    queries.remove_car_from_long_claim(long_claim_id, car_id)
    return {"success": True, "message": "Car removed from long claim"}


@router.get("/long-claim/{long_claim_id}/cars")
async def get_cars_for_long_claim(long_claim_id: str):
    """
    Retrieve all cars linked to a given long claim.

    Returns:
        Dict with ``success``, ``count``, and ``data``.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)
    data = queries.get_cars_by_long_claim(long_claim_id)
    return {"success": True, "count": len(data), "data": data}


# ---------------------------------------------------------------------------
# Daily rates
# ---------------------------------------------------------------------------

@router.get("/long-claim/{long_claim_id}/daily-rates")
async def get_daily_rates(long_claim_id: str):
    """
    Retrieve the daily hire rate for every car in a long claim.

    Returns:
        Dict with ``success`` and ``data`` ({car_id: daily_rate}).
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)
    data = queries.get_daily_rates_for_claim(long_claim_id)
    rates = {item["car_id"]: item["daily_rate"] or 0 for item in data}
    return {"success": True, "data": rates}


@router.put("/long-claim/{long_claim_id}/daily-rate")
async def update_daily_rate(long_claim_id: str, body: DailyRateUpdate):
    """
    Update the daily hire rate for a specific car within a long claim.

    Args:
        long_claim_id: The long-claim ID.
        body: Contains ``car_id`` and ``daily_rate``.

    Returns:
        Dict with ``success`` boolean.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)
    updated = queries.update_daily_rate(long_claim_id, body.car_id, body.daily_rate)
    return {"success": updated}


# ---------------------------------------------------------------------------
# Claimants (grouped by car)
# ---------------------------------------------------------------------------

@router.get("/long-hire/{long_claim_id}/claimants")
async def get_claimants_for_claim(long_claim_id: str):
    """
    Retrieve all claimants for a long claim, grouped by ``car_id``.

    Args:
        long_claim_id: The long-claim ID.

    Returns:
        Dict with ``success``, ``count`` (total claimants), and ``data``
        ({car_id: [claimant, ...]}).
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)
    data = queries.get_claimants_for_claim(long_claim_id)

    claimants_by_car: Dict[Any, list] = {}
    for claimant in data:
        car_id = claimant["car_id"]
        claimants_by_car.setdefault(car_id, []).append(claimant)

    return {"success": True, "count": len(data), "data": claimants_by_car}
