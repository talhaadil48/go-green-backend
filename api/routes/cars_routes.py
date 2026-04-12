"""
Cars management routes.

Routes:
    GET    /api/cars
    GET    /api/cars/count
    GET    /api/cars/free
    GET    /api/cars/available
    POST   /api/car
    GET    /api/car/{car_id}
    PUT    /api/car/{car_id}
    DELETE /api/car/{car_id}
    PUT    /api/cars/{car_id}/long
    PUT    /api/cars/availability/{reg_no}
"""

from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request

from api.models.schemas import CarCreate, CarUpdate
from db.connection import DBConnection
from sql.combinedQueries import Queries

router = APIRouter(tags=["cars"])


@router.get("/cars")
async def get_all_cars():
    """
    Retrieve all cars with current holder and last mileage data.

    Returns:
        Dict with ``success``, ``count``, and ``data`` (list of car dicts).
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)
    cars = queries.get_all_cars()
    return {"success": True, "count": len(cars), "data": cars}


@router.get("/cars/count")
async def get_non_long_hire_cars_count():
    """
    Return the count of cars not marked as long-hire.

    Returns:
        Dict with ``success`` and ``count``.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)
    count = queries.get_non_long_hire_cars_count()
    return {"success": True, "count": count}


@router.get("/cars/free")
async def get_free_cars():
    """
    Return all cars that are not long-hire vehicles.

    Returns:
        Dict with ``success``, ``count``, and ``data``.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)
    cars = queries.get_free_cars()
    return {"success": True, "count": len(cars), "data": cars}


@router.get("/cars/available")
async def get_available_cars():
    """
    Return long-hire cars that are not currently assigned to a claimant.

    Returns:
        Dict with ``success``, ``count``, and ``data``.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)
    cars = queries.get_available_cars()
    return {"success": True, "count": len(cars), "data": cars}


@router.post("/car")
async def create_car(payload: CarCreate):
    """
    Create a new car record.

    Args:
        payload: Car creation data (model, name, reg_no, attributes).

    Returns:
        Confirmation dict.

    Raises:
        HTTPException(400): When registration number already exists.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)
    try:
        queries.insert_car(
            payload.model,
            payload.name,
            payload.reg_no,
            payload.attributes if payload.attributes is not None else [],
        )
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    return {"success": True, "message": "Car created successfully"}


@router.get("/car/{car_id}")
async def get_car_by_id(car_id: int):
    """
    Retrieve a single car by its ID.

    Args:
        car_id: The numeric car ID.

    Returns:
        Dict with ``success`` and ``data`` (car row).

    Raises:
        HTTPException(404): When the car is not found.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)
    car = queries.get_car_by_id(car_id)
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    return {"success": True, "data": car}


@router.put("/car/{car_id}")
async def update_car(car_id: int, payload: CarUpdate):
    """
    Update an existing car record.

    Args:
        car_id: The numeric car ID.
        payload: Fields to update.

    Returns:
        Confirmation dict.

    Raises:
        HTTPException(400): When the update violates a unique constraint.
        HTTPException(404): When the car is not found.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)
    try:
        updated = queries.update_car(
            car_id,
            payload.model,
            payload.name,
            payload.service_time,
            payload.attributes if payload.attributes is not None else [],
        )
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    if not updated:
        raise HTTPException(status_code=404, detail="Car not found")

    return {"success": True, "message": "Car updated successfully"}


@router.delete("/car/{car_id}")
async def delete_car(car_id: str):
    """
    Hard-delete a car record.

    Args:
        car_id: The car ID.

    Returns:
        Dict indicating success or failure.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)
    deleted = queries.delete_car(car_id)
    if deleted:
        return {"success": True, "message": "Car deleted successfully"}
    return {"success": False, "message": f"No car found with id {car_id}"}


@router.put("/cars/{car_id}/long")
async def update_long_hire(car_id: int, request: Request) -> Dict[str, Any]:
    """
    Toggle the ``is_long_hire`` flag on a car.

    Required body field: ``value`` (boolean).
    """
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    value = data.get("value")
    if value not in (True, False):
        raise HTTPException(status_code=400, detail="value must be true or false")

    conn = DBConnection.get_connection()
    queries = Queries(conn)
    result = queries.update_is_long_hire(car_id, value)
    if not result:
        raise HTTPException(status_code=404, detail="Car not found")

    return {"car_id": car_id, "is_long_hire": value}


@router.put("/cars/availability/{reg_no}")
async def update_availability(reg_no: str, request: Request) -> Dict[str, Any]:
    """
    Update the ``is_available`` flag on a car identified by registration number.

    Required body field: ``value`` (boolean).
    """
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    value = data.get("value")
    if value not in (True, False):
        raise HTTPException(status_code=400, detail="value must be true or false")

    conn = DBConnection.get_connection()
    queries = Queries(conn)
    result = queries.update_is_available(reg_no, value)
    if not result:
        raise HTTPException(status_code=404, detail="Car not found")

    return {"reg_no": reg_no, "is_available": value}
