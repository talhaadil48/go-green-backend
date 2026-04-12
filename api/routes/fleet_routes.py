"""
Fleet-history read routes.

Routes:
    GET /api/fleet-history
"""

from fastapi import APIRouter

from db.connection import DBConnection
from sql.combinedQueries import Queries

router = APIRouter(tags=["fleet"])


@router.get("/fleet-history")
async def get_all_fleet_history():
    """
    Retrieve all fleet-history records ordered by hire start date descending.

    Returns:
        Dict with ``count`` and ``data`` (list of fleet-history dicts).
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)
    history = queries.get_all_fleet_history()
    return {"count": len(history), "data": history}
