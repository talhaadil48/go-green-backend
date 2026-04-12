"""
User-management query methods.

Covers all database operations for the ``users`` table.
"""

from .base import ClaimFormBase


class UserQueries(ClaimFormBase):
    """Mixin class that provides user-management read/write queries."""

    # ------------------------------------------------------------------
    # Write helpers
    # ------------------------------------------------------------------

    def create_user(self, username: str, password: str, role: str) -> dict | None:
        """
        Insert a new user record.

        Args:
            username: Unique username.
            password: Pre-hashed password string.
            role: Role identifier (e.g. ``"admin"`` or ``"user"``).

        Returns:
            Dict with ``id``, ``username``, and ``role`` on success,
            or ``None`` if creation failed (e.g. duplicate username).
        """
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
                    columns = [desc[0] for desc in cur.description]
                    return dict(zip(columns, row))
            return None
        except Exception as e:
            print(f"Error in create_user: {e}")
            self.conn.rollback()
            return None

    def delete_user(self, user_id: int) -> bool:
        """
        Hard-delete a user record.

        Args:
            user_id: The numeric user ID.

        Returns:
            ``True`` if deleted, ``False`` if not found.
        """
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

    def change_user_password(self, username: str, new_password: str) -> bool:
        """
        Update the hashed password for a user.

        Args:
            username: The user's username.
            new_password: Pre-hashed new password string.

        Returns:
            ``True`` if updated, ``False`` if not found.
        """
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

    # ------------------------------------------------------------------
    # Read helpers
    # ------------------------------------------------------------------

    def get_user_by_username(self, username: str) -> dict | None:
        """
        Retrieve a user record by username.

        Args:
            username: The username to look up.

        Returns:
            The full user row as a dict, or ``None`` if not found.
        """
        query = "SELECT * FROM users WHERE username = %s;"
        with self.conn.cursor() as cur:
            cur.execute(query, (username,))
            row = cur.fetchone()
            if row:
                columns = [desc[0] for desc in cur.description]
                return dict(zip(columns, row))
        return None

    def get_user_by_id(self, user_id: str) -> dict | None:
        """
        Retrieve a user record by ID.

        Args:
            user_id: The user's numeric ID (accepts string for JWT compatibility).

        Returns:
            Dict with ``id``, ``username``, ``role``, and ``permissions``,
            or ``None`` if not found.
        """
        query = """
            SELECT id, username, role, permissions
            FROM users
            WHERE id = %(user_id)s;
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, {"user_id": user_id})
                row = cur.fetchone()
                if row:
                    columns = [desc[0] for desc in cur.description]
                    return dict(zip(columns, row))
            return None
        except Exception as e:
            print(f"Error in get_user_by_id: {e}")
            return None

    def get_all_non_admin_users(self) -> list[dict]:
        """
        Retrieve all users whose role is not ``"admin"``.

        Returns:
            List of user dicts containing ``id``, ``username``, and ``role``.
        """
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
                columns = [desc[0] for desc in cur.description]
                return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            print(f"Error in get_all_non_admin_users: {e}")
            return []
