"""
Notification query methods.

Covers all database operations for the ``notifications`` and
``user_notifications`` tables.
"""

from psycopg2.extras import RealDictCursor
from .base import ClaimFormBase


class NotificationQueries(ClaimFormBase):
    """Mixin class that provides notification read/write queries."""

    # ------------------------------------------------------------------
    # Write helpers
    # ------------------------------------------------------------------

    def broadcast_notification(
        self, sender_id: int, title: str, message: str
    ) -> bool:
        """
        Create a notification and link it to every user in the system.

        The sender automatically receives the notification in a
        read (``is_read = TRUE``) state so they are not notified of their
        own broadcast.

        Args:
            sender_id: The ID of the user sending the notification.
            title: Notification title (used as the claim/subject identifier).
            message: Body text of the notification.

        Returns:
            ``True`` on success.

        Raises:
            Exception: Re-raises any database error after rolling back.
        """
        notif_query = """
            INSERT INTO notifications (created_by, title, message)
            VALUES (%s, %s, %s) RETURNING id
        """
        mapping_query = """
            INSERT INTO user_notifications (notification_id, user_id, is_read)
            SELECT %s, id, CASE WHEN id = %s THEN TRUE ELSE FALSE END
            FROM users
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(notif_query, (sender_id, title, message))
                notification_id = cur.fetchone()[0]

            with self.conn.cursor() as cur:
                cur.execute(mapping_query, (notification_id, sender_id))

            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            raise e

    def mark_single_as_read(self, notification_id: int, user_id: int) -> bool:
        """
        Mark a single notification as read for a specific user.

        Args:
            notification_id: The notification ID.
            user_id: The user's ID.

        Returns:
            ``True`` on success.
        """
        query = """
            UPDATE user_notifications
            SET is_read = TRUE
            WHERE notification_id = %s AND user_id = %s
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (notification_id, user_id))
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            raise e

    def mark_all_as_read(self, user_id: int) -> bool:
        """
        Mark all unread notifications as read for a specific user.

        Args:
            user_id: The user's ID.

        Returns:
            ``True`` on success.
        """
        query = """
            UPDATE user_notifications
            SET is_read = TRUE
            WHERE user_id = %s AND is_read = FALSE
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (user_id,))
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            raise e

    def delete_expired_notifications(self) -> int:
        """
        Hard-delete notifications older than 7 days.

        Cascades to ``user_notifications`` via the foreign key.

        Returns:
            Number of notification rows deleted.
        """
        query = """
            DELETE FROM notifications
            WHERE created_at < NOW() - INTERVAL '7 days'
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(query)
                deleted_count = cur.rowcount
            self.conn.commit()
            return deleted_count
        except Exception as e:
            self.conn.rollback()
            raise e

    # ------------------------------------------------------------------
    # Read helpers
    # ------------------------------------------------------------------

    def get_user_notifications(
        self, user_id: int, unread_only: bool = False
    ) -> list[dict]:
        """
        Retrieve notifications for a user, optionally filtered to unread only.

        Args:
            user_id: The user's ID.
            unread_only: When ``True``, only unread notifications are returned.

        Returns:
            List of notification dicts ordered by creation time descending.
        """
        query = """
            SELECT n.id AS notification_id, n.created_by, n.title,
                   n.message, un.is_read, n.created_at
            FROM notifications n
            JOIN user_notifications un ON n.id = un.notification_id
            WHERE un.user_id = %s
        """
        if unread_only:
            query += " AND un.is_read = FALSE"
        query += " ORDER BY n.created_at DESC"

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (user_id,))
                return cur.fetchall()
        except Exception as e:
            self.conn.rollback()
            print("get_user_notifications ERROR:", e)
            raise e
