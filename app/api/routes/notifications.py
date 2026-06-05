from fastapi import APIRouter, HTTPException, Query
from app.db.pool import get_pool
from app.db.queries import notifications as notif_q
from app.models.schemas import BroadcastCreate

router = APIRouter()


# Static routes BEFORE parameterised /{notification_id} routes

@router.post("/notifications/broadcast")
async def create_broadcast(payload: BroadcastCreate):
    pool = get_pool()
    async with pool.acquire() as conn:
        try:
            await notif_q.broadcast_notification(conn, payload.sender_id, payload.title, payload.message)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    return {"success": True, "message": "Notification broadcasted successfully"}


@router.get("/notifications/users/{user_id}")
async def get_notifications(user_id: int, unread_only: bool = Query(False, description="Fetch only unread notifications")):
    pool = get_pool()
    async with pool.acquire() as conn:
        try:
            data = await notif_q.get_user_notifications(conn, user_id, unread_only)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    return {"success": True, "data": data}


@router.patch("/notifications/users/{user_id}/read-all")
async def mark_all_read(user_id: int):
    pool = get_pool()
    async with pool.acquire() as conn:
        try:
            await notif_q.mark_all_as_read(conn, user_id)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    return {"success": True, "message": f"All notifications marked as read for user {user_id}"}


@router.delete("/notifications/expired")
async def clean_expired_notifications():
    pool = get_pool()
    async with pool.acquire() as conn:
        try:
            deleted_count = await notif_q.delete_expired_notifications(conn)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    return {"success": True, "message": f"Successfully deleted {deleted_count} expired notifications"}


# Parameterised route AFTER static routes above
@router.patch("/notifications/{notification_id}/users/{user_id}/read")
async def mark_single_read(notification_id: int, user_id: int):
    pool = get_pool()
    async with pool.acquire() as conn:
        try:
            await notif_q.mark_single_as_read(conn, notification_id, user_id)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    return {"success": True, "message": "Notification marked as read"}
