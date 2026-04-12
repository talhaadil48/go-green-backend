"""
Claimants management routes.

Routes:
    GET    /api/claimants
    POST   /api/claimant
    GET    /api/claimant/{claimant_id}
    PUT    /api/claimant/{claimant_id}
    DELETE /api/claimant/{claimant_id}
    GET    /api/car/{car_id}/claimants/{claim_id}
"""

from fastapi import APIRouter, HTTPException

from api.models.schemas import ClaimantCreate, ClaimantUpdate
from db.connection import DBConnection
from sql.combinedQueries import Queries

router = APIRouter(tags=["claimants"])


@router.get("/claimants")
async def get_all_claimants():
    """
    Retrieve all claimant records.

    Returns:
        Dict with ``success``, ``count``, and ``data``.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)
    data = queries.get_all_claimants()
    return {"success": True, "count": len(data), "data": data}


@router.post("/claimant")
async def create_claimant(payload: ClaimantCreate):
    """
    Create a new claimant record.

    Args:
        payload: Claimant data (long_claim_id and car_id are required).

    Returns:
        Dict with ``success`` and ``claimant_id``.

    Raises:
        HTTPException(400): When ``claimant_id`` already exists.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    try:
        claimant_id = queries.insert_claimant(
            payload.long_claim_id,
            payload.car_id,
            payload.start_date,
            payload.end_date,
            payload.miles,
            payload.name,
            payload.location,
            payload.delivery_charges or 0,
            payload.claimant_id,
            payload.ref_no,
        )
        return {"success": True, "claimant_id": claimant_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/claimant/{claimant_id}")
async def get_claimant_by_id(claimant_id: int):
    """
    Retrieve claimant records for a given row ID.

    Args:
        claimant_id: The auto-generated row ID.

    Returns:
        Dict with ``success``, ``count``, and ``data``.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)
    data = queries.get_claimant(claimant_id=claimant_id)
    return {"success": True, "count": len(data), "data": data}


@router.put("/claimant/{claimant_id}")
async def update_claimant(claimant_id: int, payload: ClaimantUpdate):
    """
    Update fields on an existing claimant record.

    Args:
        claimant_id: The auto-generated row ID.
        payload: Fields to update (all optional).

    Returns:
        Confirmation dict.

    Raises:
        HTTPException(400): When ``claimant_id`` conflicts with an existing one.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    try:
        queries.update_claimant(
            claimant_id,
            new_claimant_id=payload.claimant_id,
            ref_no=payload.ref_no,
            start_date=payload.start_date,
            end_date=payload.end_date,
            miles=payload.miles,
            name=payload.name,
            location=payload.location,
            delivery_charges=payload.delivery_charges,
        )
        return {"success": True, "message": "Claimant updated successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/claimant/{claimant_id}")
async def delete_claimant(claimant_id: int):
    """
    Hard-delete a claimant record.

    Args:
        claimant_id: The auto-generated row ID.

    Returns:
        Dict indicating success or failure.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)
    deleted = queries.delete_claimant(claimant_id)
    if deleted:
        return {"success": True, "message": "Claimant deleted successfully"}
    return {"success": False, "message": "Claimant not found"}


@router.get("/car/{car_id}/claimants/{claim_id}")
async def get_claimants_for_car(car_id: int, claim_id: str):
    """
    Retrieve claimants for a specific car within a long claim.

    Args:
        car_id: The numeric car ID.
        claim_id: The long-claim ID.

    Returns:
        Dict with ``success``, ``count``, and ``data``.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)
    data = queries.get_claimants_by_car(car_id, claim_id)
    return {"success": True, "count": len(data), "data": data}
