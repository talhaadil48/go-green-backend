"""
SQL query package.

Exports the single :class:`~sql.queries.claimFormQueries.ClaimFormQueries`
class that combines every domain-specific query mixin.  The rest of the
application imports from here:

.. code-block:: python

    from sql.queries import ClaimFormQueries
"""

from .claimFormQueries import ClaimFormQueries

__all__ = ["ClaimFormQueries"]
