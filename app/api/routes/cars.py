from fastapi import APIRouter, HTTPException, Request
from typing import Any, Dict
from app.db.pool import get_pool
from app.db.queries import cars as cars_q
from app.models.schemas import CarCreate, CarUpdate

router = APIRouter()


# ── Static / non-parameterized routes first ──────────────────────────────────

@router.get("/cars")
async def get_all_cars():
    pool = get_pool()
    async with pool.acquire() as conn:
        cars = await cars_q.get_all_cars(conn)
    return {"success": True, "count": len(cars), "data": cars}


@router.get("/cars/free/count")
async def get_non_long_hire_cars_count():
    pool = get_pool()
    async with pool.acquire() as conn:
        count = await cars_q.get_non_long_hire_cars_count(conn)
    return {"success": True, "count": count}


@router.get("/cars/free")
async def get_free_cars():
    pool = get_pool()
    async with pool.acquire() as conn:
        cars = await cars_q.get_free_cars(conn)
    return {"success": True, "count": len(cars), "data": cars}


@router.get("/cars/available")
async def get_available_cars():
    pool = get_pool()
    async with pool.acquire() as conn:
        cars = await cars_q.get_available_cars(conn)
    return {"success": True, "count": len(cars), "data": cars}


# PUT /api/cars/availability/{reg_no} — static "availability" segment, must come before /cars/{car_id}/long
@router.put("/cars/availability/{reg_no}")
async def update_availability(reg_no: str, request: Request) -> Dict[str, Any]:
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    value = data.get("value")
    if value not in [True, False]:
        raise HTTPException(status_code=400, detail="value must be true or false")

    pool = get_pool()
    async with pool.acquire() as conn:
        result = await cars_q.update_is_available(conn, reg_no, value)

    if not result:
        raise HTTPException(status_code=404, detail="Car not found")
    return {"reg_no": reg_no, "is_available": value}


# PUT /api/cars/{car_id}/long — parameterized, after static "availability" route
@router.put("/cars/{car_id}/long")
async def update_long_hire(car_id: int, request: Request) -> Dict[str, Any]:
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    value = data.get("value")
    if value not in [True, False]:
        raise HTTPException(status_code=400, detail="value must be true or false")

    pool = get_pool()
    async with pool.acquire() as conn:
        result = await cars_q.update_is_long_hire(conn, car_id, value)

    if not result:
        raise HTTPException(status_code=404, detail="Car not found")
    return {"car_id": car_id, "is_long_hire": value}


# ── Single-car routes (singular /car path) ───────────────────────────────────

@router.post("/car")
async def create_car(payload: CarCreate):
    pool = get_pool()
    async with pool.acquire() as conn:
        try:
            await cars_q.insert_car(conn, payload.model, payload.name, payload.reg_no, payload.attributes or [])
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    return {"success": True, "message": "Car created successfully"}


@router.put("/car/{car_id}")
async def update_car(car_id: int, payload: CarUpdate):
    pool = get_pool()
    async with pool.acquire() as conn:
        try:
            updated = await cars_q.update_car(conn, car_id, payload.model, payload.name, payload.service_time, payload.attributes or [])
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    if not updated:
        raise HTTPException(status_code=404, detail="Car not found")
    return {"success": True, "message": "Car updated successfully"}


@router.delete("/car/{car_id}")
async def delete_car(car_id: str):
    pool = get_pool()
    async with pool.acquire() as conn:
        deleted = await cars_q.delete_car(conn, car_id)
    if deleted:
        return {"success": True, "message": "Car deleted successfully"}
    return {"success": False, "message": f"No car found with id {car_id}"}


@router.get("/car/{car_id}")
async def get_car_by_id(car_id: int):
    pool = get_pool()
    async with pool.acquire() as conn:
        car = await cars_q.get_car_by_id(conn, car_id)
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    return {"success": True, "data": car}
