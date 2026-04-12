"""
Claims query methods.

Covers all database operations for the main ``claims`` table: CRUD, soft
deletes, status/lock/disputed updates, claim updates (JSON array), and the
bill aggregation helper.
"""

import json
from psycopg2.extras import RealDictCursor
from typing import Any, Dict

from .base import ClaimFormBase


class ClaimsQueries(ClaimFormBase):
    """Mixin class that provides claims read/write queries."""

    # ------------------------------------------------------------------
    # Create / Delete
    # ------------------------------------------------------------------

    def insert_claim(
        self,
        claimant_name: str | None,
        claim_type: str | None,
        council: str | None,
        claim_id: str | None = None,
    ) -> bool:
        """
        Insert a new claim record.

        Args:
            claimant_name: Full name of the claimant.
            claim_type: Category of the claim (e.g. ``"accident"``).
            council: Associated council identifier.
            claim_id: Optional explicit claim ID; auto-generated if omitted.

        Returns:
            ``True`` on success.

        Raises:
            psycopg2.errors.UniqueViolation: When *claim_id* already exists.
        """
        query = """
            INSERT INTO claims (claim_id, claimant_name, claim_type, council)
            VALUES (%s, %s, %s, %s);
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (claim_id, claimant_name, claim_type, council))
            self.conn.commit()
        return True

    def delete_claim(self, claim_id: str) -> bool:
        """
        Hard-delete a claim record.

        Args:
            claim_id: The unique claim identifier.

        Returns:
            ``True`` if a row was deleted, ``False`` if not found.
        """
        query = "DELETE FROM claims WHERE claim_id = %s;"
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (claim_id,))
                if cur.rowcount == 0:
                    return False
                self.conn.commit()
            return True
        except Exception as e:
            print(f"Error in delete_claim: {e}")
            self.conn.rollback()
            return False

    # ------------------------------------------------------------------
    # Update helpers
    # ------------------------------------------------------------------

    def update_claim_dynamic(self, claim_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Update one or more fields on a claim using a dynamic query.

        Args:
            claim_id: The unique claim identifier.
            update_data: Dict of ``{column_name: value}`` pairs to update.

        Returns:
            ``True`` if the row was updated, ``False`` if not found or empty dict.
        """
        fields = []
        values = []

        for field, value in update_data.items():
            fields.append(f"{field} = %s")
            values.append(value)

        if not fields:
            return False

        query = f"UPDATE claims SET {', '.join(fields)} WHERE claim_id = %s;"
        values.append(claim_id)

        with self.conn.cursor() as cur:
            cur.execute(query, tuple(values))
            self.conn.commit()
            return cur.rowcount > 0

    def soft_delete_claim(self, claim_id: str, deleted_by: str) -> bool:
        """
        Mark a claim as recently deleted (soft delete).

        Args:
            claim_id: The unique claim identifier.
            deleted_by: Username of the user performing the deletion.

        Returns:
            ``True`` if updated, ``False`` if not found.
        """
        query = """
            UPDATE claims
            SET recently_deleted = TRUE,
                recently_deleted_date = NOW(),
                deleted_by = %s
            WHERE claim_id = %s;
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (deleted_by, claim_id))
                if cur.rowcount == 0:
                    return False
                self.conn.commit()
            return True
        except Exception as e:
            print(f"Error in soft_delete_claim: {e}")
            self.conn.rollback()
            return False

    def restore_short_claim(self, claim_id: str) -> bool:
        """
        Restore a soft-deleted short claim.

        Args:
            claim_id: The unique claim identifier.

        Returns:
            ``True`` on success.
        """
        query = """
            UPDATE claims
            SET recently_deleted = FALSE,
                recently_deleted_date = NOW(),
                deleted_by = NULL
            WHERE claim_id = %s;
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (claim_id,))
                self.conn.commit()
            return True
        except Exception as e:
            print(f"Error in restore_claim: {e}")
            self.conn.rollback()
            return False

    def close_claim(self, claim_id: str, closed_by: str, reason: str | None) -> bool:
        """
        Mark a claim as closed.

        Args:
            claim_id: The unique claim identifier.
            closed_by: Username of the closer.
            reason: Optional reason for closure.

        Returns:
            ``True`` if updated, ``False`` if not found.
        """
        query = """
            UPDATE claims
            SET closed_by = %s,
                closed_date = NOW(),
                reason = %s
            WHERE claim_id = %s;
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (closed_by, reason, claim_id))
                if cur.rowcount == 0:
                    return False
                self.conn.commit()
            return True
        except Exception as e:
            print(f"Error in close_claim: {e}")
            self.conn.rollback()
            return False

    def reopen_claim(self, claim_id: str) -> bool:
        """
        Re-open a previously closed claim by clearing closure fields.

        Args:
            claim_id: The unique claim identifier.

        Returns:
            ``True`` if updated, ``False`` if not found.
        """
        query = """
            UPDATE claims
            SET closed_by = NULL,
                closed_date = NULL,
                reason = NULL
            WHERE claim_id = %s;
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (claim_id,))
                if cur.rowcount == 0:
                    return False
                self.conn.commit()
            return True
        except Exception as e:
            print(f"Error in reopen_claim: {e}")
            self.conn.rollback()
            return False

    def update_claim_status(self, claim_id: str, status: str) -> bool:
        """
        Update the ``status`` column of a claim.

        Args:
            claim_id: The unique claim identifier.
            status: New status string.

        Returns:
            ``True`` if updated, ``False`` if not found.
        """
        query = "UPDATE claims SET status = %s WHERE claim_id = %s;"
        with self.conn.cursor() as cur:
            cur.execute(query, (status, claim_id))
            if cur.rowcount == 0:
                return False
            self.conn.commit()
        return True

    def update_claim_disputed(
        self,
        claim_id: str,
        is_disputed=None,
        dispute_reason=None,
    ) -> bool:
        """
        Update disputed fields on a claim.

        Args:
            claim_id: The unique claim identifier.
            is_disputed: Boolean flag, or ``None`` to leave unchanged.
            dispute_reason: Reason string, or ``None`` to leave unchanged.

        Returns:
            ``True`` if updated, ``False`` if nothing to update or not found.
        """
        fields = []
        values = []

        if is_disputed is not None:
            fields.append("is_disputed = %s")
            values.append(is_disputed)

        if dispute_reason is not None:
            fields.append("dispute_reason = %s")
            values.append(dispute_reason)

        if not fields:
            return False

        query = f"UPDATE claims SET {', '.join(fields)} WHERE claim_id = %s;"
        values.append(claim_id)

        with self.conn.cursor() as cur:
            cur.execute(query, tuple(values))
            if cur.rowcount == 0:
                return False
            self.conn.commit()
        return True

    def update_claim_lock(
        self, claim_id: str, locked: bool, locked_by: str | None
    ) -> None:
        """
        Update the lock status on a claim.

        Args:
            claim_id: The unique claim identifier.
            locked: ``True`` to lock, ``False`` to unlock.
            locked_by: Username of the locker (or ``None`` when unlocking).
        """
        query = "UPDATE claims SET locked = %s, locked_by = %s WHERE claim_id = %s;"
        with self.conn.cursor() as cur:
            cur.execute(query, (locked, locked_by, claim_id))
        self.conn.commit()

    def update_ref_no(self, claim_id: str, ref_no: str) -> dict | None:
        """
        Update the ``ref_no`` field on a claim.

        Args:
            claim_id: The unique claim identifier.
            ref_no: The new reference number.

        Returns:
            The updated row as a dict, or ``None`` if not found.
        """
        query = """
            UPDATE claims
            SET ref_no = %s
            WHERE claim_id = %s
            RETURNING *;
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (ref_no, claim_id))
            self.conn.commit()
            return cur.fetchone()

    def update_payment_details(
        self,
        claim_id: str,
        payment: str | None,
        pay_date: str | None,
    ) -> dict | None:
        """
        Update payment-related fields on a claim.

        If ``pay_date`` transitions from ``NULL`` to a real value the claim
        status is automatically updated to ``"client paid"``.

        Args:
            claim_id: The unique claim identifier.
            payment: Payment reference string, or ``None`` to leave unchanged.
            pay_date: Payment date string (``YYYY-MM-DD``), or ``None``.

        Returns:
            The updated row as a dict, or ``None`` if not found or nothing changed.
        """
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT payment, pay_date FROM claims WHERE claim_id = %s;",
                (claim_id,),
            )
            old = cur.fetchone()
            if not old:
                return None

            _, old_pay_date = old

            fields = []
            values = []

            if payment is not None:
                fields.append("payment = %s")
                values.append(payment)
            if pay_date is not None:
                fields.append("pay_date = %s")
                values.append(pay_date)

            if not fields:
                return None

            values.append(claim_id)
            query = f"UPDATE claims SET {', '.join(fields)} WHERE claim_id = %s RETURNING *;"
            cur.execute(query, tuple(values))
            self.conn.commit()

            row = cur.fetchone()
            if row:
                columns = [desc[0] for desc in cur.description]
                if old_pay_date is None and pay_date is not None:
                    self.update_claim_status(claim_id, "client paid")
                return dict(zip(columns, row))
        return None

    def update_invoice_date(self, claim_id: str, invoice_date: str) -> dict | None:
        """
        Update the ``invoice_date`` field on a claim.

        Args:
            claim_id: The unique claim identifier.
            invoice_date: New invoice date value.

        Returns:
            The updated row as a dict, or ``None`` if not found.
        """
        query = """
            UPDATE claims
            SET invoice_date = %s
            WHERE claim_id = %s
            RETURNING *;
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (invoice_date, claim_id))
            self.conn.commit()
            row = cur.fetchone()
            if row:
                columns = [desc[0] for desc in cur.description]
                return dict(zip(columns, row))
        return None

    # ------------------------------------------------------------------
    # Updates (JSON array on claims.updates column)
    # ------------------------------------------------------------------

    def add_update(self, claim_id: str, new_update: dict, user_id: int) -> bool:
        """
        Append a new update object to the ``claims.updates`` JSONB array.

        A broadcast notification is sent to all users after the update is saved.

        Args:
            claim_id: The unique claim identifier.
            new_update: Dict containing at minimum ``id``, ``message``, ``date``,
                and ``user`` keys.
            user_id: The ID of the user adding the update (used as notification sender).

        Returns:
            ``True`` if the row was found and updated, ``False`` otherwise.
        """
        query = """
            UPDATE claims
            SET updates = COALESCE(updates, '[]'::jsonb) || %s::jsonb
            WHERE claim_id = %s;
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (json.dumps([new_update]), claim_id))
            self.conn.commit()

            message = new_update.get("message", "New update added")
            self.broadcast_notification(user_id, claim_id, message)

            return cur.rowcount > 0

    def edit_update(self, claim_id: str, update_id: int, new_data: dict) -> bool:
        """
        Edit an existing entry inside the ``claims.updates`` JSONB array.

        The entry is located by its ``id`` field.

        Args:
            claim_id: The unique claim identifier.
            update_id: The ``id`` value of the update object to modify.
            new_data: Dict of fields to merge into the existing update object.

        Returns:
            ``True`` if the update was found and saved, ``False`` otherwise.
        """
        select_query = "SELECT updates FROM claims WHERE claim_id = %s;"
        update_query = "UPDATE claims SET updates = %s WHERE claim_id = %s;"

        with self.conn.cursor() as cur:
            cur.execute(select_query, (claim_id,))
            row = cur.fetchone()

            if not row or not row[0]:
                return False

            updates = row[0]
            found = False
            for i, item in enumerate(updates):
                if item.get("id") == update_id:
                    updates[i] = {**item, **new_data}
                    found = True
                    break

            if not found:
                return False

            cur.execute(update_query, (json.dumps(updates), claim_id))
            self.conn.commit()
            return True

    def get_updates(self, claim_id: str) -> list[dict]:
        """
        Return the ``updates`` JSONB array for a claim.

        Args:
            claim_id: The unique claim identifier.

        Returns:
            List of update dicts (empty list if none exist).
        """
        query = "SELECT updates FROM claims WHERE claim_id = %s;"
        with self.conn.cursor() as cur:
            cur.execute(query, (claim_id,))
            row = cur.fetchone()
            if not row or not row[0]:
                return []
            return row[0]

    # ------------------------------------------------------------------
    # Read helpers
    # ------------------------------------------------------------------

    def get_all_claims(self) -> list[dict]:
        """
        Retrieve all non-deleted claims with their latest invoice and hire dates.

        Returns a joined dataset combining ``claims``, the most recent
        ``invoice`` row, and hire start/end dates derived from
        ``rental_agreements``.

        Returns:
            List of claim dicts.
        """
        query = """
            SELECT
                c.*,
                i.id AS invoice_id,
                i.invoice_datetime,
                i.info,

                CASE
                    WHEN ra.hire_vehicle_date_in IS NOT NULL
                        AND EXISTS (
                            SELECT 1
                            FROM jsonb_array_elements(ra.change_vehicle_history::jsonb) AS j
                            WHERE NULLIF(j->>'date_out','') IS NOT NULL
                        )
                        AND NOT EXISTS (
                            SELECT 1
                            FROM jsonb_array_elements(ra.change_vehicle_history::jsonb) AS j
                            WHERE NULLIF(j->>'date_in','') IS NOT NULL
                        )
                    THEN NULL
                    ELSE GREATEST(
                        ra.hire_vehicle_date_in,
                        (
                            SELECT MAX((NULLIF(j->>'date_in',''))::date)
                            FROM jsonb_array_elements(ra.change_vehicle_history::jsonb) AS j
                            WHERE NULLIF(j->>'date_in','') IS NOT NULL
                        )
                    )
                END AS hire_end_date,

                LEAST(
                    ra.hire_vehicle_date_out,
                    (
                        SELECT MIN((NULLIF(j->>'date_out',''))::date)
                        FROM jsonb_array_elements(ra.change_vehicle_history::jsonb) AS j
                        WHERE NULLIF(j->>'date_out','') IS NOT NULL
                    )
                ) AS hire_start_date

            FROM claims c

            LEFT JOIN (
                SELECT DISTINCT ON (claim_id)
                    id, claim_id, invoice_datetime, info
                FROM invoice
                ORDER BY claim_id, invoice_datetime DESC
            ) i ON c.claim_id = i.claim_id

            LEFT JOIN rental_agreements ra ON c.claim_id = ra.claim_id

            WHERE c.recently_deleted = FALSE;
        """
        with self.conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in rows]

    def get_claim_by_id(self, claim_id: str) -> dict | None:
        """
        Retrieve a single claim by its ID.

        Args:
            claim_id: The unique claim identifier.

        Returns:
            The row as a dict, or ``None`` if not found.
        """
        query = "SELECT * FROM claims WHERE claim_id = %s;"
        with self.conn.cursor() as cur:
            cur.execute(query, (claim_id,))
            row = cur.fetchone()
            if row:
                columns = [desc[0] for desc in cur.description]
                return dict(zip(columns, row))
        return None

    def get_claim_lock(self, claim_id: str) -> dict | None:
        """
        Retrieve the full claim row (used to inspect ``locked`` / ``locked_by``).

        Args:
            claim_id: The unique claim identifier.

        Returns:
            The row as a dict, or ``None`` if not found.
        """
        query = "SELECT * FROM claims WHERE claim_id = %s;"
        with self.conn.cursor() as cur:
            cur.execute(query, (claim_id,))
            row = cur.fetchone()
            if row:
                columns = [desc[0] for desc in cur.description]
                return dict(zip(columns, row))
        return None

    def get_recently_deleted_claims(self) -> list[dict]:
        """
        Retrieve all claims marked as recently deleted.

        Returns:
            List of claim dicts.
        """
        query = "SELECT * FROM claims WHERE recently_deleted = TRUE;"
        try:
            with self.conn.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()
                columns = [desc[0] for desc in cur.description]
                return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            print(f"Error fetching recently deleted claims: {e}")
            return []

    def permanently_delete_recently_deleted_claims(self) -> int:
        """
        Hard-delete claims that have been soft-deleted for more than 3 days.

        Returns:
            Number of rows deleted.
        """
        query = """
            DELETE FROM claims
            WHERE recently_deleted = TRUE
            AND recently_deleted_date < NOW() - INTERVAL '3 days';
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(query)
                deleted_count = cur.rowcount
                self.conn.commit()
                return deleted_count
        except Exception as e:
            print(f"Error deleting recently deleted claims: {e}")
            return 0

    def get_claim_summary(self, claim_id: str) -> dict | None:
        """
        Build a summary dict combining claim info, accident data, rental,
        storage, and invoice records in a single response.

        Args:
            claim_id: The unique claim identifier.

        Returns:
            Dict with keys ``claim``, ``accident_claim``, ``rental_agreement``,
            ``storage_form``, and ``invoices``, or ``None`` if the claim is not found.
        """
        summary: dict = {
            "claim": None,
            "accident_claim": None,
            "rental_agreement": None,
            "storage_form": None,
            "invoices": [],
        }

        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT claim_id, claimant_name, claim_type, claim_start_date,
                       status, closed_date, closed_by, recently_deleted,
                       is_disputed, dispute_reason
                FROM claims
                WHERE claim_id = %s;
                """,
                (claim_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            columns = [desc[0] for desc in cur.description]
            summary["claim"] = dict(zip(columns, row))

            cur.execute(
                """
                SELECT
                    checklist_vd,
                    driver_full_name, driver_email, driver_telephone,
                    driver_address, driver_postcode, driver_dob,
                    driver_ni_number, driver_occupation,
                    client_vehicle_make, client_vehicle_model,
                    client_registration, client_policy_no,
                    client_cover_type, client_policy_holder
                FROM accident_claims
                WHERE claim_id = %s;
                """,
                (claim_id,),
            )
            row = cur.fetchone()
            if row:
                columns = [desc[0] for desc in cur.description]
                summary["accident_claim"] = dict(zip(columns, row))

            cur.execute(
                """
                SELECT
                    hire_vehicle_reg, hire_vehicle_make, hire_vehicle_model,
                    hire_vehicle_date_out, hire_vehicle_date_in,
                    hire_vehicle_miles_out, hire_vehicle_miles_in,
                    change_vehicle_history
                FROM rental_agreements
                WHERE claim_id = %s;
                """,
                (claim_id,),
            )
            row = cur.fetchone()
            if row:
                columns = [desc[0] for desc in cur.description]
                summary["rental_agreement"] = dict(zip(columns, row))

            cur.execute(
                "SELECT storage_location_key FROM storage_forms WHERE claim_id = %s;",
                (claim_id,),
            )
            row = cur.fetchone()
            if row:
                summary["storage_form"] = {"storage_location_key": row[0]}

            cur.execute(
                """
                SELECT id, invoice_datetime, info, storage_bill, rent_bill
                FROM invoice
                WHERE claim_id = %s
                ORDER BY invoice_datetime DESC;
                """,
                (claim_id,),
            )
            rows = cur.fetchall()
            if rows:
                columns = [desc[0] for desc in cur.description]
                summary["invoices"] = [dict(zip(columns, row)) for row in rows]

        return summary
