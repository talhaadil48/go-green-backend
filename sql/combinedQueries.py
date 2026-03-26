"""Thin wrapper kept for backward compatibility.

``main.py`` / route modules call::

    from sql.combinedQueries import Queries
    queries = Queries(conn)

That contract is preserved here by aliasing to the full
:class:`~sql.queries.ClaimFormQueries` composition class.
"""

from sql.queries import ClaimFormQueries


class Queries(ClaimFormQueries):
    """Full query class – alias of :class:`~sql.queries.ClaimFormQueries`."""

    def __init__(self, conn):
        ClaimFormQueries.__init__(self, conn)
