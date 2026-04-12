"""
Base module for all SQL query classes.

Provides the shared connection holder and utility helpers used
across all query mixin classes.
"""

from datetime import datetime


def parse_date(d):
    """
    Convert a date value to a Python date object.

    Accepts a string in ``YYYY-MM-DD`` format, a ``datetime`` instance,
    or ``None`` / empty string (returns ``None`` in those cases).
    """
    if d and isinstance(d, str) and d.strip():
        return datetime.strptime(d, "%Y-%m-%d").date()
    elif isinstance(d, datetime):
        return d.date()
    return None


class ClaimFormBase:
    """
    Base class for all query mixin classes.

    Stores the psycopg2 connection and exposes ``self.conn`` to every mixin
    that inherits from it.
    """

    def __init__(self, conn):
        """
        Initialise with an active psycopg2 connection.

        Args:
            conn: A live psycopg2 database connection instance.
        """
        self.conn = conn
