"""Long-hire query mixin.

Covers: long_claims, long_claim_cars, claimant, hire_checklist, daily rates.
"""

from psycopg2.extras import RealDictCursor


class LongHireQueries:
    """Mixin providing DB methods for all long-hire-related tables."""

    # ── Long Claims ───────────────────────────────────────────────────────────

    def insert_long_claim(self, starting_date, ending_date, hirer_name=None):
        """Create a new long-hire claim and return its ID."""
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
        self, long_claim_id, starting_date, ending_date, hirer_name=None
    ):
        """Update a long-hire claim's dates and hirer name."""
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

    def get_all_long_claims(self):
        """Return all active (non-soft-deleted) long-hire claims."""
        query = """
            SELECT id, starting_date, ending_date, invoice_sent, date_sent, hirer_name
            FROM long_claims
            WHERE recently_deleted = FALSE
            ORDER BY id DESC
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            return cur.fetchall()

    def get_long_claim_by_id(self, claim_id):
        """Return a single long-hire claim by ID."""
        query = """
            SELECT id, starting_date, ending_date, invoice_sent, hirer_name
            FROM long_claims
            WHERE id = %s
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (claim_id,))
            return cur.fetchone()

    def mark_invoice(self, long_claim_id: str):
        """Mark a long claim as invoice sent."""
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

    def mark_as_recently_deleted(self, claim_id: str, deleted_by: str):
        """Soft-delete a long-hire claim."""
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

    def delete_long_claim(self, claim_id: str):
        """Permanently delete a long-hire claim."""
        query = "DELETE FROM long_claims WHERE id = %s"
        with self.conn.cursor() as cur:
            cur.execute(query, (claim_id,))
            self.conn.commit()
            return cur.rowcount > 0

    def restore_claim(self, claim_id: str):
        """Restore a soft-deleted long-hire claim."""
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

    def get_soft_deleted_long_claims(self):
        """Return all soft-deleted long-hire claims."""
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

    # ── Long Claim ↔ Car ──────────────────────────────────────────────────────

    def add_car_to_long_claim(self, long_claim_id: str, car_id: int):
        """Link a car to a long-hire claim."""
        query = "INSERT INTO long_claim_cars (long_claim_id, car_id) VALUES (%s, %s);"
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (long_claim_id, car_id))
                self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            raise e

    def remove_car_from_long_claim(self, long_claim_id: str, car_id: int):
        """Unlink a car from a long-hire claim."""
        query = "DELETE FROM long_claim_cars WHERE long_claim_id=%s AND car_id=%s;"
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (long_claim_id, car_id))
                self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            raise e

    def get_cars_by_long_claim(self, long_claim_id):
        """Return cars assigned to a long-hire claim."""
        query = """
            SELECT c.*
            FROM long_claim_cars lcc
            JOIN cars c ON c.id = lcc.car_id
            WHERE lcc.long_claim_id = %s
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (long_claim_id,))
            return cur.fetchall()

    # ── Claimants ─────────────────────────────────────────────────────────────

    def insert_claimant(
        self,
        long_claim_id,
        car_id,
        start_date=None,
        end_date=None,
        miles=None,
        name=None,
        location=None,
        delivery_charges=0,
    ):
        """Create a new claimant record."""
        query = """
            INSERT INTO claimant
            (long_claim_id, car_id, start_date, end_date, miles, name, location, delivery_charges)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    query,
                    (long_claim_id, car_id, start_date, end_date, miles, name,
                     location, delivery_charges),
                )
                claimant_id = cur.fetchone()[0]
            self.conn.commit()
            return claimant_id
        except Exception as e:
            self.conn.rollback()
            raise e

    def update_claimant(
        self,
        claimant_id,
        start_date=None,
        end_date=None,
        miles=None,
        name=None,
        location=None,
        delivery_charges=None,
    ):
        """Update non-None fields on a claimant record."""
        fields = []
        values = []

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
        except Exception as e:
            self.conn.rollback()
            raise e

    def delete_claimant(self, claimant_id: int):
        """Delete a claimant record."""
        query = "DELETE FROM claimant WHERE id=%s"
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (claimant_id,))
            self.conn.commit()
            return cur.rowcount > 0
        except Exception as e:
            self.conn.rollback()
            raise e

    def get_claimant(self, claimant_id=None, long_claim_id=None, car_id=None):
        """Flexible claimant lookup – any combination of filters can be supplied."""
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

    def get_all_claimants(self):
        """Return all claimant records."""
        query = "SELECT * FROM claimant ORDER BY id DESC"
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            return cur.fetchall()

    def get_claimants_by_car(self, car_id, claim_id):
        """Return claimants for a specific car within a long-hire claim."""
        query = "SELECT * FROM claimant WHERE car_id = %s AND long_claim_id = %s"
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (car_id, claim_id))
            return cur.fetchall()

    def get_claimants_for_claim(self, long_claim_id: str):
        """Return all claimants for a long-hire claim."""
        query = "SELECT * FROM claimant WHERE long_claim_id = %s"
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (long_claim_id,))
            return cur.fetchall()

    # ── Hire Checklist ────────────────────────────────────────────────────────

    def upsert_hire_checklist(
        self,
        long_claim_id: str,
        car_id: int,
        claimant_id: int,
        data: dict,
    ) -> dict | None:
        """Insert or update a hire checklist keyed by (long_claim_id, car_id, claimant_id)."""
        updatable_columns = [
            *[f"condition_{i}" for i in range(1, 31)],
            "date", "customer", "detailer", "order_number",
            "year", "make", "model",
            "notes", "recommendations",
            "customer_signature", "detailer_signature",
            "base_vehicle_image", "annotated_vehicle_image",
        ]

        fields_to_update = [col for col in updatable_columns if col in data]

        try:
            with self.conn.cursor() as cur:
                columns = ["long_claim_id", "car_id", "claimant_id"] + fields_to_update
                values_placeholders = ", ".join(f"%({col})s" for col in columns)
                set_clause = ", ".join(
                    f"{col} = EXCLUDED.{col}" for col in fields_to_update
                )

                query = f"""
                INSERT INTO hire_checklist ({', '.join(columns)})
                VALUES ({values_placeholders})
                ON CONFLICT (long_claim_id, car_id, claimant_id)
                DO UPDATE SET {set_clause}
                RETURNING *;
                """

                params = {
                    "long_claim_id": long_claim_id,
                    "car_id": car_id,
                    "claimant_id": claimant_id,
                    **{col: data[col] for col in fields_to_update},
                }

                cur.execute(query, params)
                row = cur.fetchone()

                if not row:
                    self.conn.commit()
                    return None

                cols_list = [desc[0] for desc in cur.description]
                self.conn.commit()
                return dict(zip(cols_list, row))

        except Exception as e:
            self.conn.rollback()
            print("Error in upsert_hire_checklist:", e)
            return None

    def get_hire_checklists(
        self, long_claim_id: str, car_id: int, claimant_id: int
    ) -> list[dict]:
        """Return all hire checklists for the given (claim, car, claimant) triplet."""
        query = """
        SELECT * FROM hire_checklist
        WHERE long_claim_id = %s
        AND car_id = %s
        AND claimant_id = %s
        ORDER BY inspection_id ASC;
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (long_claim_id, car_id, claimant_id))
            rows = cur.fetchall()
            if rows:
                cols = [desc[0] for desc in cur.description]
                return [dict(zip(cols, row)) for row in rows]
        return []

    # ── Daily Rates ───────────────────────────────────────────────────────────

    def update_daily_rate(
        self, long_claim_id: str, car_id: int, daily_rate: float
    ) -> bool:
        """Set the daily rate for a car within a long-hire claim."""
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

    def get_daily_rates_for_claim(self, long_claim_id: str):
        """Return a list of ``{car_id, daily_rate}`` for a long-hire claim."""
        query = """
            SELECT car_id, daily_rate
            FROM long_claim_cars
            WHERE long_claim_id = %s
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (long_claim_id,))
            return cur.fetchall()
