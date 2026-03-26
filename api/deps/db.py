"""Database dependency.

Returns a ready-to-use :class:`~sql.combinedQueries.Queries` instance
bound to the active connection.

Usage in any router::

    from api.deps import get_db
    from fastapi import Depends

    @router.get("/example")
    async def example(queries = Depends(get_db)):
        return queries.get_all_claims()
"""

from db.connection import DBConnection
from sql.combinedQueries import Queries


def get_db() -> Queries:
    """Return a ``Queries`` object connected to the database."""
    conn = DBConnection.get_connection()
    return Queries(conn)
