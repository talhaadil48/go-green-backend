"""Cars CRUD routes."""

from fastapi import APIRouter, HTTPException, Depends
from typing import Any

from api.deps import get_db
from api.schemas import CarCreate, CarUpdate

router = APIRouter(tags=["cars"])


@router.post("/car")
async def create_car(payload: CarCreate, queries=Depends(get_db)):
    """Add a new car to the fleet."""
    queries.insert_car(payload.model, payload.name, payload.reg_no)
    return {"success": True, "message": "Car created successfully"}


@router.delete("/car/{car_id}")
async def delete_car(car_id: str, queries=Depends(get_db)):
    """Permanently delete a car from the fleet."""
    deleted = queries.delete_car(car_id)
    if deleted:
        return {"success": True, "message": "Car deleted successfully"}
    return {"success": False, "message": f"No car found with id {car_id}"}


@router.put("/car/{car_id}")
async def update_car(car_id: int, payload: CarUpdate, queries=Depends(get_db)):
    """Update a car's model, name, and registration number."""
    updated = queries.update_car(car_id, payload.model, payload.name, payload.reg_no)
    if not updated:
        raise HTTPException(status_code=404, detail="Car not found")
    return {"success": True, "message": "Car updated successfully"}


@router.get("/car/{car_id}")
async def get_car_by_id(car_id: int, queries=Depends(get_db)):
    """Return a single car by its ID."""
    car = queries.get_car_by_id(car_id)
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    return {"success": True, "data": car}


@router.get("/cars")
async def get_all_cars(queries=Depends(get_db)):
    """Return all cars in the fleet."""
    cars = queries.get_all_cars()
    return {"success": True, "count": len(cars), "data": cars}


@router.get("/cars/available")
async def get_available_cars(queries=Depends(get_db)):
    """Return cars that are not currently assigned to an active claimant."""
    cars = queries.get_available_cars()
    return {"success": True, "count": len(cars), "data": cars}
