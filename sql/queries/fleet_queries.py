"""
Fleet-history query methods.

Covers all database operations for the ``fleet_history`` table.
"""

from .base import ClaimFormBase


class FleetHistoryQueries(ClaimFormBase):
    """Mixin class that provides fleet-history read/write queries."""

    # ------------------------------------------------------------------
    # Write helpers
    # ------------------------------------------------------------------

    def insert_fleet_history(
        self,
        hire_start: str | None,
        hire_end: str | None,
        claim_id: str,
        car_reg: str,
        miles_in: str | None,
        miles_out: str | None,
    ) -> None:
        """
        Insert a new fleet-history record.

        Empty-string mile values are coerced to ``None`` so numeric columns
        remain valid.

        Args:
            hire_start: Hire start date string or ``None``.
            hire_end: Hire end date string or ``None``.
            claim_id: The associated claim ID.
            car_reg: The car's registration number.
            miles_in: Miles-in reading (empty string treated as ``None``).
            miles_out: Miles-out reading (empty string treated as ``None``).
        """
        if miles_in == "":
            miles_in = None
        if miles_out == "":
            miles_out = None

        query = """
            INSERT INTO fleet_history
            (hire_start, hire_end, claim_id, car_reg, miles_in, miles_out)
            VALUES (%s, %s, %s, %s, %s, %s);
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (hire_start, hire_end, claim_id, car_reg, miles_in, miles_out))
        self.conn.commit()

    def update_fleet_history_hire_end(
        self,
        hire_end: str,
        claim_id: str,
        car_reg: str,
        hire_start: str,
        miles_in: str | None,
        miles_out: str | None,
    ) -> None:
        """
        Update the hire-end date and mileage on an existing fleet-history record.

        The row is located by the composite key (``claim_id``, ``car_reg``,
        ``hire_start``).  Empty-string mile values are coerced to ``None``.

        Args:
            hire_end: New hire end date string.
            claim_id: The associated claim ID.
            car_reg: The car's registration number.
            hire_start: The hire start date used to locate the row.
            miles_in: Updated miles-in reading (empty string → ``None``).
            miles_out: Updated miles-out reading (empty string → ``None``).
        """
        if miles_in == "":
            miles_in = None
        if miles_out == "":
            miles_out = None

        query = """
            UPDATE fleet_history
            SET hire_end = %s,
                miles_in = %s,
                miles_out = %s
            WHERE claim_id = %s
            AND car_reg = %s
            AND hire_start = %s;
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (hire_end, miles_in, miles_out, claim_id, car_reg, hire_start))
        self.conn.commit()

    # ------------------------------------------------------------------
    # Read helpers
    # ------------------------------------------------------------------

    def get_all_fleet_history(self) -> list[dict]:
        """
        Retrieve all fleet-history records ordered by hire start date descending.

        Returns:
            List of fleet-history dicts.
        """
        query = "SELECT * FROM fleet_history ORDER BY hire_start DESC;"
        with self.conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()
            if not rows:
                return []
            col_names = [desc[0] for desc in cur.description]
            return [dict(zip(col_names, row)) for row in rows]
