"""
Long-claim query methods.

Covers all database operations for the ``long_claims`` and
``long_claim_cars`` tables.
"""

from psycopg2.extras import RealDictCursor
from .base import ClaimFormBase


class LongClaimQueries(ClaimFormBase):
    """Mixin class that provides long-claim read/write queries."""

    # ------------------------------------------------------------------
    # Write helpers
    # ------------------------------------------------------------------

    def insert_long_claim(
        self,
        starting_date: str | None,
        ending_date: str | None,
        hirer_name: str | None = None,
    ) -> int:
        """
        Insert a new long-claim record.

        Args:
            starting_date: Contract start date (``YYYY-MM-DD``) or ``None``.
            ending_date: Contract end date (``YYYY-MM-DD``) or ``None``.
            hirer_name: Optional name of the hirer.

        Returns:
            The auto-generated long-claim ID.
        """
        query = """
            INSERT INTO long_claims (starting_date, ending_date, hirer_name)
            VALUES (%s, %s, %s)
            RETURNING id;
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (starting_date, ending_date, hirer_name))
                long_claim_id = cur.fetchone()[0]
                self.conn.commit()
            return long_claim_id
        except Exception as e:
            self.conn.rollback()
            raise e

    def update_long_claim(
        self,
        long_claim_id: str,
        starting_date: str | None,
        ending_date: str | None,
        hirer_name: str | None = None,
    ) -> None:
        """
        Update the dates and hirer name on a long claim.

        Args:
            long_claim_id: The long-claim ID.
            starting_date: New start date or ``None``.
            ending_date: New end date or ``None``.
            hirer_name: New hirer name or ``None``.
        """
        query = """
            UPDATE long_claims
            SET starting_date = %s,
                ending_date = %s,
                hirer_name = %s
            WHERE id = %s;
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (starting_date, ending_date, hirer_name, long_claim_id))
                self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e

    def add_car_to_long_claim(self, long_claim_id: str, car_id: int) -> bool:
        """
        Link a car to a long claim via the ``long_claim_cars`` junction table.

        Args:
            long_claim_id: The long-claim ID.
            car_id: The numeric car ID.

        Returns:
            ``True`` on success.
        """
        query = "INSERT INTO long_claim_cars (long_claim_id, car_id) VALUES (%s, %s);"
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (long_claim_id, car_id))
                self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            raise e

    def remove_car_from_long_claim(self, long_claim_id: str, car_id: int) -> bool:
        """
        Remove a car-to-long-claim link from the junction table.

        Args:
            long_claim_id: The long-claim ID.
            car_id: The numeric car ID.

        Returns:
            ``True`` on success.
        """
        query = "DELETE FROM long_claim_cars WHERE long_claim_id=%s AND car_id=%s;"
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (long_claim_id, car_id))
                self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            raise e

    def mark_invoice(self, long_claim_id: str) -> bool:
        """
        Mark a long claim's invoice as sent and record today's date.

        Args:
            long_claim_id: The long-claim ID.

        Returns:
            ``True`` if the row was updated, ``False`` if not found.
        """
        query = """
            UPDATE long_claims
            SET invoice_sent = TRUE,
                date_sent = CURRENT_DATE
            WHERE id = %s
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (long_claim_id,))
            self.conn.commit()
            return cur.rowcount > 0
        except Exception as e:
            self.conn.rollback()
            raise e

    def mark_as_recently_deleted(self, claim_id: str, deleted_by: str) -> int:
        """
        Soft-delete a long claim by setting ``recently_deleted = TRUE``.

        Args:
            claim_id: The long-claim ID.
            deleted_by: Username performing the deletion.

        Returns:
            Number of rows affected.
        """
        query = """
            UPDATE long_claims
            SET recently_deleted = TRUE,
                recently_deleted_date = NOW(),
                deleted_by = %s
            WHERE id = %s
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (deleted_by, claim_id))
            self.conn.commit()
            return cur.rowcount

    def restore_claim(self, claim_id: str) -> int:
        """
        Restore a soft-deleted long claim.

        Args:
            claim_id: The long-claim ID.

        Returns:
            Number of rows affected.
        """
        query = """
            UPDATE long_claims
            SET recently_deleted = FALSE,
                recently_deleted_date = NULL
            WHERE id = %s
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (claim_id,))
            self.conn.commit()
            return cur.rowcount

    def delete_long_claim(self, claim_id: str) -> bool:
        """
        Hard-delete a long claim.

        Args:
            claim_id: The long-claim ID.

        Returns:
            ``True`` if deleted, ``False`` if not found.
        """
        query = "DELETE FROM long_claims WHERE id = %s"
        with self.conn.cursor() as cur:
            cur.execute(query, (claim_id,))
            self.conn.commit()
            return cur.rowcount > 0

    def update_daily_rate(
        self, long_claim_id: str, car_id: int, daily_rate: float
    ) -> bool:
        """
        Update the daily hire rate for a specific car within a long claim.

        Args:
            long_claim_id: The long-claim ID.
            car_id: The numeric car ID.
            daily_rate: New daily rate value.

        Returns:
            ``True`` if the row was found and updated.
        """
        query = """
            UPDATE long_claim_cars
            SET daily_rate = %s
            WHERE long_claim_id = %s
            AND car_id = %s
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (daily_rate, long_claim_id, car_id))
            self.conn.commit()
            return cur.rowcount > 0

    # ------------------------------------------------------------------
    # Read helpers
    # ------------------------------------------------------------------

    def get_all_long_claims(self) -> list[dict]:
        """
        Retrieve all non-deleted long claims ordered by ID descending.

        Returns:
            List of long-claim dicts.
        """
        query = """
            SELECT id, starting_date, ending_date, invoice_sent, date_sent, hirer_name
            FROM long_claims
            WHERE recently_deleted = FALSE
            ORDER BY id DESC
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            return cur.fetchall()

    def get_long_claim_by_id(self, claim_id: str) -> dict | None:
        """
        Retrieve a single long claim by ID.

        Args:
            claim_id: The long-claim ID.

        Returns:
            The row as a dict, or ``None`` if not found.
        """
        query = """
            SELECT id, starting_date, ending_date, invoice_sent, hirer_name
            FROM long_claims
            WHERE id = %s
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (claim_id,))
            return cur.fetchone()

    def get_soft_deleted_long_claims(self) -> list[dict]:
        """
        Retrieve all long claims that have been soft-deleted.

        Returns:
            List of long-claim dicts including the ``deleted_by`` field.
        """
        query = """
            SELECT id, starting_date, ending_date, invoice_sent, date_sent,
                   hirer_name, deleted_by
            FROM long_claims
            WHERE recently_deleted = TRUE
            ORDER BY id DESC
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            return cur.fetchall()

    def get_cars_by_long_claim(self, long_claim_id: str) -> list[dict]:
        """
        Retrieve all cars linked to a given long claim.

        Args:
            long_claim_id: The long-claim ID.

        Returns:
            List of car dicts.
        """
        query = """
            SELECT c.*
            FROM long_claim_cars lcc
            JOIN cars c ON c.id = lcc.car_id
            WHERE lcc.long_claim_id = %s
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (long_claim_id,))
            return cur.fetchall()

    def get_daily_rates_for_claim(self, long_claim_id: str) -> list[dict]:
        """
        Retrieve the daily rate for every car linked to a long claim.

        Args:
            long_claim_id: The long-claim ID.

        Returns:
            List of dicts, each containing ``car_id`` and ``daily_rate``.
        """
        query = """
            SELECT car_id, daily_rate
            FROM long_claim_cars
            WHERE long_claim_id = %s
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (long_claim_id,))
            return cur.fetchall()
