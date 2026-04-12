"""
Notification routes.

Routes:
    POST   /api/notifications/broadcast
    GET    /api/notifications/users/{user_id}
    PATCH  /api/notifications/{notification_id}/users/{user_id}/read
    PATCH  /api/notifications/users/{user_id}/read-all
    DELETE /api/notifications/expired
"""

from fastapi import APIRouter, HTTPException, Query

from api.models.schemas import BroadcastCreate
from db.connection import DBConnection
from sql.combinedQueries import Queries

router = APIRouter(tags=["notifications"])


@router.post("/notifications/broadcast")
async def create_broadcast(payload: BroadcastCreate):
    """
    Broadcast a notification to all users.

    The sender receives the notification in a pre-read state so they are not
    notified of their own message.

    Args:
        payload: Contains ``sender_id``, ``title``, and ``message``.

    Returns:
        Confirmation dict.

    Raises:
        HTTPException(400): On database error.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)
    try:
        queries.broadcast_notification(payload.sender_id, payload.title, payload.message)
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    return {"success": True, "message": "Notification broadcasted successfully"}


@router.get("/notifications/users/{user_id}")
async def get_notifications(
    user_id: int,
    unread_only: bool = Query(False, description="Fetch only unread notifications"),
):
    """
    Retrieve notifications for a specific user.

    Args:
        user_id: The user's numeric ID.
        unread_only: When ``True``, only unread notifications are returned.

    Returns:
        Dict with ``success`` and ``data`` (list of notification dicts).

    Raises:
        HTTPException(400): On database error.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)
    try:
        data = queries.get_user_notifications(user_id, unread_only)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"success": True, "data": data}


@router.patch("/notifications/{notification_id}/users/{user_id}/read")
async def mark_single_read(notification_id: int, user_id: int):
    """
    Mark a single notification as read for a specific user.

    Args:
        notification_id: The notification ID.
        user_id: The user's numeric ID.

    Returns:
        Confirmation dict.

    Raises:
        HTTPException(400): On database error.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)
    try:
        queries.mark_single_as_read(notification_id, user_id)
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    return {"success": True, "message": "Notification marked as read"}


@router.patch("/notifications/users/{user_id}/read-all")
async def mark_all_read(user_id: int):
    """
    Mark all unread notifications as read for a specific user.

    Args:
        user_id: The user's numeric ID.

    Returns:
        Confirmation dict.

    Raises:
        HTTPException(400): On database error.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)
    try:
        queries.mark_all_as_read(user_id)
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    return {"success": True, "message": f"All notifications marked as read for user {user_id}"}


@router.delete("/notifications/expired")
async def clean_expired_notifications():
    """
    Delete all notifications older than 7 days.

    Returns:
        Confirmation dict with the number of deleted rows.

    Raises:
        HTTPException(400): On database error.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)
    try:
        deleted_count = queries.delete_expired_notifications()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "success": True,
        "message": f"Successfully deleted {deleted_count} expired notifications",
    }
