"""
Claimant query methods.

Covers all database operations for the ``claimant`` table.
"""

from psycopg2 import errors
from psycopg2.extras import RealDictCursor
from fastapi import HTTPException

from .base import ClaimFormBase


class ClaimantQueries(ClaimFormBase):
    """Mixin class that provides claimant read/write queries."""

    # ------------------------------------------------------------------
    # Write helpers
    # ------------------------------------------------------------------

    def insert_claimant(
        self,
        long_claim_id: str,
        car_id: int,
        start_date: str | None = None,
        end_date: str | None = None,
        miles: float | None = None,
        name: str | None = None,
        location: str | None = None,
        delivery_charges: float = 0,
        claimant_id: str | None = None,
        ref_no: str | None = None,
    ) -> int:
        """
        Insert a new claimant record and return its auto-generated ID.

        Args:
            long_claim_id: The long-claim this claimant belongs to.
            car_id: The car assigned to this claimant.
            start_date: Hire start date (``YYYY-MM-DD``) or ``None``.
            end_date: Hire end date (``YYYY-MM-DD``) or ``None``.
            miles: Mileage or ``None``.
            name: Claimant display name or ``None``.
            location: Collection/delivery location or ``None``.
            delivery_charges: Delivery charge amount (defaults to 0).
            claimant_id: Optional explicit claimant ID.
            ref_no: Optional reference number.

        Returns:
            The auto-generated integer row ID.

        Raises:
            HTTPException(400): When *claimant_id* already exists.
        """
        query = """
            INSERT INTO claimant
            (claimant_id, ref_no, long_claim_id, car_id, start_date,
             end_date, miles, name, location, delivery_charges)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    query,
                    (
                        claimant_id, ref_no, long_claim_id, car_id,
                        start_date, end_date, miles, name, location,
                        delivery_charges,
                    ),
                )
                new_id = cur.fetchone()[0]
            self.conn.commit()
            return new_id
        except errors.UniqueViolation:
            self.conn.rollback()
            raise HTTPException(status_code=400, detail="Claimant ID already exists")
        except Exception as e:
            self.conn.rollback()
            raise e

    def update_claimant(
        self,
        claimant_id: int,
        new_claimant_id: str | None = None,
        ref_no: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        miles: float | None = None,
        name: str | None = None,
        location: str | None = None,
        delivery_charges: float | None = None,
    ) -> bool:
        """
        Update fields on an existing claimant record.

        Only non-``None`` arguments are included in the update query.

        Args:
            claimant_id: The auto-generated row ID of the claimant.
            new_claimant_id: New explicit claimant ID or ``None``.
            ref_no: New reference number or ``None``.
            start_date: New start date or ``None``.
            end_date: New end date or ``None``.
            miles: New mileage value or ``None``.
            name: New name or ``None``.
            location: New location or ``None``.
            delivery_charges: New delivery charge or ``None``.

        Returns:
            ``True`` if updated, ``False`` if nothing to update.

        Raises:
            HTTPException(400): When *new_claimant_id* already exists.
        """
        fields = []
        values = []

        if new_claimant_id is not None:
            fields.append("claimant_id=%s")
            values.append(new_claimant_id)
        if ref_no is not None:
            fields.append("ref_no=%s")
            values.append(ref_no)
        if start_date is not None:
            fields.append("start_date=%s")
            values.append(start_date)
        if end_date is not None:
            fields.append("end_date=%s")
            values.append(end_date)
        if miles is not None:
            fields.append("miles=%s")
            values.append(miles)
        if name is not None:
            fields.append("name=%s")
            values.append(name)
        if location is not None:
            fields.append("location=%s")
            values.append(location)
        if delivery_charges is not None:
            fields.append("delivery_charges=%s")
            values.append(delivery_charges)

        if not fields:
            return False

        query = f"UPDATE claimant SET {', '.join(fields)} WHERE id=%s"
        values.append(claimant_id)

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, tuple(values))
            self.conn.commit()
            return True
        except errors.UniqueViolation:
            self.conn.rollback()
            raise HTTPException(status_code=400, detail="Claimant ID already exists")
        except Exception as e:
            self.conn.rollback()
            raise e

    def delete_claimant(self, claimant_id: int) -> bool:
        """
        Hard-delete a claimant record.

        Args:
            claimant_id: The auto-generated row ID of the claimant.

        Returns:
            ``True`` if deleted, ``False`` if not found.
        """
        query = "DELETE FROM claimant WHERE id=%s"
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (claimant_id,))
            self.conn.commit()
            return cur.rowcount > 0
        except Exception as e:
            self.conn.rollback()
            raise e

    # ------------------------------------------------------------------
    # Read helpers
    # ------------------------------------------------------------------

    def get_claimant(
        self,
        claimant_id: int | None = None,
        long_claim_id: str | None = None,
        car_id: int | None = None,
    ) -> list[dict]:
        """
        Retrieve claimant rows filtered by one or more criteria.

        All supplied arguments are combined with ``AND``.

        Args:
            claimant_id: Filter by auto-generated row ID.
            long_claim_id: Filter by long-claim ID.
            car_id: Filter by car ID.

        Returns:
            List of matching claimant dicts.
        """
        query = "SELECT * FROM claimant WHERE 1=1"
        params = []

        if claimant_id:
            query += " AND id=%s"
            params.append(claimant_id)
        if long_claim_id:
            query += " AND long_claim_id=%s"
            params.append(long_claim_id)
        if car_id:
            query += " AND car_id=%s"
            params.append(car_id)

        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            return cur.fetchall()

    def get_all_claimants(self) -> list[dict]:
        """
        Retrieve all claimant records ordered by ID descending.

        Returns:
            List of claimant dicts.
        """
        query = "SELECT * FROM claimant ORDER BY id DESC"
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            return cur.fetchall()

    def get_claimants_by_car(self, car_id: int, claim_id: str) -> list[dict]:
        """
        Retrieve claimants for a specific car within a long claim.

        Args:
            car_id: The numeric car ID.
            claim_id: The long-claim ID.

        Returns:
            List of claimant dicts.
        """
        query = """
            SELECT *
            FROM claimant
            WHERE car_id = %s AND long_claim_id = %s
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (car_id, claim_id))
            return cur.fetchall()

    def get_claimants_for_claim(self, long_claim_id: str) -> list[dict]:
        """
        Retrieve all claimants associated with a long claim.

        Args:
            long_claim_id: The long-claim ID.

        Returns:
            List of claimant dicts.
        """
        query = "SELECT * FROM claimant WHERE long_claim_id = %s"
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (long_claim_id,))
            return cur.fetchall()
