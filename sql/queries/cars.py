"""Cars query mixin.

Covers: fleet car CRUD.
"""

from psycopg2.extras import RealDictCursor


class CarsQueries:
    """Mixin providing DB methods for the ``cars`` table."""

    def insert_car(self, model, name, reg_no) -> bool:
        """Insert a new car into the fleet."""
        query = "INSERT INTO cars (model, name, reg_no) VALUES (%s, %s, %s)"
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (model, name, reg_no))
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            raise e

    def update_car(self, car_id, model, name, reg_no) -> bool:
        """Update a car's details."""
        query = """
            UPDATE cars
            SET model=%s, name=%s, reg_no=%s
            WHERE id=%s
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (model, name, reg_no, car_id))
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            raise e

    def delete_car(self, car_id: str) -> bool:
        """Permanently delete a car."""
        query = "DELETE FROM cars WHERE id = %s"
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (car_id,))
            self.conn.commit()
            return cur.rowcount > 0
        except Exception as e:
            self.conn.rollback()
            raise e

    def get_car_by_id(self, car_id: int):
        """Return a single car row by ID."""
        query = "SELECT * FROM cars WHERE id=%s"
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (car_id,))
            return cur.fetchone()

    def get_all_cars(self):
        """Return all cars in the fleet."""
        query = "SELECT * FROM cars"
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            return cur.fetchall()

    def get_available_cars(self):
        """Return cars not currently assigned to an active claimant."""
        query = """
            SELECT *
            FROM cars
            WHERE id NOT IN (
                SELECT car_id
                FROM claimant
                WHERE end_date IS NULL
            )
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            return cur.fetchall()
