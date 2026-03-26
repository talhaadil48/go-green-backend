"""SQL query layer.

:class:`ClaimFormQueries` is the single class that composes all domain
query mixins so existing usage ``Queries(conn)`` continues to work:

    from sql.combinedQueries import Queries
    queries = Queries(conn)
    queries.get_all_claims()
"""

from .forms import FormQueries
from .claims import ClaimsQueries
from .documents import DocumentsQueries
from .users import UsersQueries
from .cars import CarsQueries
from .invoices import InvoicesQueries
from .long_hire import LongHireQueries


class ClaimFormQueries(
    FormQueries,
    ClaimsQueries,
    DocumentsQueries,
    UsersQueries,
    CarsQueries,
    InvoicesQueries,
    LongHireQueries,
):
    """Full query class composed from all domain mixins.

    Instantiate with a live psycopg2 connection::

        queries = ClaimFormQueries(conn)
    """

    def __init__(self, conn):
        self.conn = conn
