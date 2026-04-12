"""
Composite query class.

``ClaimFormQueries`` assembles all domain-specific mixin classes into a single
object that the API layer can instantiate with one database connection.

Each mixin is defined in its own module under ``sql/queries/`` and covers a
focused area of the schema:

- :mod:`~sql.queries.accident_queries`   – accident-claim CRUD
- :mod:`~sql.queries.inspection_queries` – pre-inspection forms
- :mod:`~sql.queries.form_queries`       – cancellation & storage forms
- :mod:`~sql.queries.rental_queries`     – rental agreements + fleet side-effects
- :mod:`~sql.queries.claim_queries`      – claims CRUD, status, lock, updates
- :mod:`~sql.queries.document_queries`   – claim documents
- :mod:`~sql.queries.user_queries`       – user management
- :mod:`~sql.queries.car_queries`        – car fleet
- :mod:`~sql.queries.long_claim_queries` – long claims
- :mod:`~sql.queries.claimant_queries`   – claimants
- :mod:`~sql.queries.checklist_queries`  – hire checklists
- :mod:`~sql.queries.invoice_queries`    – invoices
- :mod:`~sql.queries.fleet_queries`      – fleet history
- :mod:`~sql.queries.notification_queries` – notifications
"""

from .accident_queries import AccidentClaimQueries
from .inspection_queries import PreInspectionQueries
from .form_queries import CancellationFormQueries, StorageFormQueries
from .rental_queries import RentalAgreementQueries
from .claim_queries import ClaimsQueries
from .document_queries import DocumentQueries
from .user_queries import UserQueries
from .car_queries import CarQueries
from .long_claim_queries import LongClaimQueries
from .claimant_queries import ClaimantQueries
from .checklist_queries import HireChecklistQueries
from .invoice_queries import InvoiceQueries
from .fleet_queries import FleetHistoryQueries
from .notification_queries import NotificationQueries


class ClaimFormQueries(
    AccidentClaimQueries,
    PreInspectionQueries,
    CancellationFormQueries,
    StorageFormQueries,
    RentalAgreementQueries,
    ClaimsQueries,
    DocumentQueries,
    UserQueries,
    CarQueries,
    LongClaimQueries,
    ClaimantQueries,
    HireChecklistQueries,
    InvoiceQueries,
    FleetHistoryQueries,
    NotificationQueries,
):
    """
    Unified query class that exposes every database operation via a single object.

    Instantiate once per request with an active psycopg2 connection:

    .. code-block:: python

        conn = DBConnection.get_connection()
        queries = Queries(conn)          # Queries inherits ClaimFormQueries
        result  = queries.get_claim_by_id(claim_id)

    The class uses Python multiple-inheritance (mixin pattern) so that each
    domain area can be maintained, tested, and read independently without
    needing to navigate a 2 000-line file.
    """

    def __init__(self, conn):
        """
        Initialise all mixin classes with the same database connection.

        Args:
            conn: A live psycopg2 database connection.
        """
        # All mixins ultimately inherit from ClaimFormBase which sets self.conn
        super().__init__(conn)
