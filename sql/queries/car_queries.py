"""
Cars query methods.

Covers all database operations for the ``cars`` table and the availability
flag used by the hire workflow.
"""

import psycopg2
from psycopg2.extras import RealDictCursor

from .base import ClaimFormBase


class CarQueries(ClaimFormBase):
    """Mixin class that provides car-fleet read/write queries."""

    # ------------------------------------------------------------------
    # Write helpers
    # ------------------------------------------------------------------

    def insert_car(
        self,
        model: str | None,
        name: str | None,
        reg_no: str | None,
        attributes: list | None = None,
    ) -> bool:
        """
        Insert a new car record.

        Args:
            model: Car model string.
            name: Display name for the car.
            reg_no: Unique registration number.
            attributes: Optional list of string attributes.

        Returns:
            ``True`` on success.

        Raises:
            Exception: Re-raises with a human-readable message on duplicate
                registration number; re-raises the raw exception otherwise.
        """
        query = """
            INSERT INTO cars (model, name, reg_no, attributes)
            VALUES (%s, %s, %s, %s)
        """
        if attributes is None:
            attributes = []
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (model, name, reg_no, attributes))
            self.conn.commit()
            return True
        except psycopg2.errors.UniqueViolation:
            self.conn.rollback()
            raise Exception("Car with this registration number already exists")
        except Exception as e:
            self.conn.rollback()
            raise e

    def update_car(
        self,
        car_id: int,
        model: str | None,
        name: str | None,
        service_time: str | None,
        attributes: list | None = None,
    ) -> bool:
        """
        Update an existing car record.

        Args:
            car_id: The numeric car ID.
            model: New model string.
            name: New display name.
            service_time: New service-time value.
            attributes: New list of string attributes.

        Returns:
            ``True`` on success.

        Raises:
            Exception: Re-raises with a human-readable message on duplicate
                registration number; re-raises the raw exception otherwise.
        """
        query = """
            UPDATE cars
            SET model=%s, name=%s, service_time=%s, attributes=%s
            WHERE id=%s
        """
        if attributes is None:
            attributes = []
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (model, name, service_time, attributes, car_id))
            self.conn.commit()
            return True
        except psycopg2.errors.UniqueViolation:
            self.conn.rollback()
            raise Exception("Car with this registration number already exists")
        except Exception as e:
            self.conn.rollback()
            raise e

    def delete_car(self, car_id: str) -> bool:
        """
        Hard-delete a car record.

        Args:
            car_id: The car ID (string or int).

        Returns:
            ``True`` if deleted, ``False`` if not found.
        """
        query = "DELETE FROM cars WHERE id = %s"
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (car_id,))
            self.conn.commit()
            return cur.rowcount > 0
        except Exception as e:
            self.conn.rollback()
            raise e

    def update_is_long_hire(self, car_id: int, value: bool) -> dict | None:
        """
        Toggle the ``is_long_hire`` flag on a car.

        Args:
            car_id: The numeric car ID.
            value: ``True`` to mark as long-hire, ``False`` to clear.

        Returns:
            The updated row as a dict, or ``None`` if not found.
        """
        query = """
            UPDATE cars
            SET is_long_hire = %s
            WHERE id = %s
            RETURNING *;
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (value, car_id))
            self.conn.commit()
            return cur.fetchone()

    def update_is_available(self, reg_no: str, value: bool) -> dict | None:
        """
        Update the ``is_available`` flag on a car identified by registration number.

        Args:
            reg_no: The car's registration number.
            value: ``True`` to mark as available, ``False`` to mark as in-use.

        Returns:
            The updated row as a dict, or ``None`` if not found.
        """
        query = """
            UPDATE cars
            SET is_available = %s
            WHERE reg_no = %s
            RETURNING *;
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (value, reg_no))
            self.conn.commit()
            return cur.fetchone()

    # ------------------------------------------------------------------
    # Read helpers
    # ------------------------------------------------------------------

    def get_car_by_id(self, car_id: int) -> dict | None:
        """
        Retrieve a single car by its numeric ID.

        Args:
            car_id: The numeric car ID.

        Returns:
            The car row as a dict, or ``None`` if not found.
        """
        query = "SELECT * FROM cars WHERE id=%s"
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (car_id,))
            return cur.fetchone()

    def get_all_cars(self) -> list[dict]:
        """
        Retrieve all cars enriched with current holder and last mileage.

        Joins with ``rental_agreements`` (lateral) to find which claim
        currently holds each car, and with ``fleet_history`` (lateral) to
        compute the last recorded miles-in value.

        Returns:
            List of car dicts with added ``current_holder_claim_id`` and
            ``last_miles_in`` fields.
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    c.*,
                    ra.claim_id AS current_holder_claim_id,
                    fh.miles_list
                FROM cars c

                LEFT JOIN LATERAL (
                    SELECT r.claim_id
                    FROM rental_agreements r
                    WHERE (
                        r.hire_vehicle_reg = c.reg_no
                        AND r.hire_vehicle_date_out IS NOT NULL
                        AND r.hire_vehicle_date_in IS NULL
                    )
                    OR EXISTS (
                        SELECT 1
                        FROM jsonb_array_elements(r.change_vehicle_history) AS ch
                        WHERE ch->>'vehicle_reg' = c.reg_no
                        AND ch->>'date_out' IS NOT NULL
                        AND (ch->>'date_in' = '' OR ch->>'date_in' IS NULL)
                    )
                    ORDER BY r.rental_agreement_id DESC
                    LIMIT 1
                ) ra ON TRUE

                LEFT JOIN LATERAL (
                    SELECT ARRAY_AGG(f.miles_in) AS miles_list
                    FROM fleet_history f
                    WHERE f.car_reg = c.reg_no
                ) fh ON TRUE

                ORDER BY c.id ASC
            """)
            cars = cur.fetchall()

        for car in cars:
            miles_list = car.get("miles_list") or []
            valid_miles = []
            for m in miles_list:
                try:
                    if m is not None and str(m).isdigit():
                        valid_miles.append(int(m))
                except Exception:
                    pass
            car["last_miles_in"] = max(valid_miles) if valid_miles else None

        return cars

    def get_free_cars(self) -> list[dict]:
        """
        Retrieve all cars that are **not** long-hire vehicles.

        Returns:
            List of car dicts ordered by ID ascending.
        """
        query = "SELECT * FROM cars WHERE is_long_hire = FALSE ORDER BY id ASC"
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            return cur.fetchall()

    def get_non_long_hire_cars_count(self) -> int:
        """
        Count cars that are not marked as long-hire.

        Returns:
            Integer count.
        """
        with self.conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM cars WHERE is_long_hire = FALSE")
            return cur.fetchone()[0]

    def get_available_cars(self) -> list[dict]:
        """
        Retrieve long-hire cars that are not currently assigned to a claimant.

        A car is considered available when it has ``is_long_hire = TRUE`` and
        its ID does not appear in the ``claimant`` table with a ``NULL`` end_date.

        Returns:
            List of available car dicts.
        """
        query = """
            SELECT *
            FROM cars
            WHERE is_long_hire = TRUE
            AND id NOT IN (
                SELECT car_id
                FROM claimant
                WHERE end_date IS NULL
            )
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            return cur.fetchall()
