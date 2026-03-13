"""Users query mixin.

Covers: user CRUD and password management.
"""


class UsersQueries:
    """Mixin providing DB methods for the ``users`` table."""

    def create_user(self, username: str, password: str, role: str) -> dict | None:
        """Insert a new user and return the created row."""
        query = """
            INSERT INTO users (username, password, role)
            VALUES (%s, %s, %s)
            RETURNING id, username, role;
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (username, password, role))
                row = cur.fetchone()
                self.conn.commit()
                if row:
                    cols = [desc[0] for desc in cur.description]
                    return dict(zip(cols, row))
            return None
        except Exception as e:
            print(f"Error in create_user: {e}")
            self.conn.rollback()
            return None

    def delete_user(self, user_id: int) -> bool:
        """Delete a user by ID, return True if a row was removed."""
        query = "DELETE FROM users WHERE id = %s RETURNING id;"
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (user_id,))
                row = cur.fetchone()
                self.conn.commit()
                return row is not None
        except Exception as e:
            print(f"Error in delete_user: {e}")
            self.conn.rollback()
            return False

    def get_all_non_admin_users(self) -> list[dict]:
        """Return all users whose role is not ``admin``."""
        query = """
            SELECT id, username, role
            FROM users
            WHERE role != 'admin'
            ORDER BY id ASC;
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()
                cols = [desc[0] for desc in cur.description]
                return [dict(zip(cols, row)) for row in rows]
        except Exception as e:
            print(f"Error in get_all_non_admin_users: {e}")
            return []

    def get_user_by_username(self, username: str) -> dict | None:
        """Fetch a user row by username (used for authentication)."""
        query = "SELECT * FROM users WHERE username = %s;"
        with self.conn.cursor() as cur:
            cur.execute(query, (username,))
            row = cur.fetchone()
            if row:
                cols = [desc[0] for desc in cur.description]
                return dict(zip(cols, row))
        return None

    def change_user_password(self, username: str, new_password: str) -> bool:
        """Update the hashed password for a user."""
        query = """
            UPDATE users
            SET password = %s
            WHERE username = %s
            RETURNING id;
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (new_password, username))
                row = cur.fetchone()
                self.conn.commit()
                return row is not None
        except Exception as e:
            print(f"Error in change_user_password: {e}")
            self.conn.rollback()
            return False
