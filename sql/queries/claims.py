"""Claims query mixin.

Covers: claim CRUD, soft-delete / restore / close / reopen, status, billing.
"""


class ClaimsQueries:
    """Mixin providing DB methods for the ``claims`` table and related operations."""

    def insert_claim(
        self,
        claimant_name: str | None,
        claim_type: str | None,
        council: str | None,
        claim_id: str | None = None,
    ) -> bool:
        """Insert a new claim row."""
        query = """
            INSERT INTO claims (claim_id, claimant_name, claim_type, council)
            VALUES (%s, %s, %s, %s);
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (claim_id, claimant_name, claim_type, council))
            self.conn.commit()
        return True

    def delete_claim(self, claim_id: str) -> bool:
        """Permanently delete a claim row."""
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

    def update_claimant_name(self, claim_id: str, new_name: str) -> bool:
        """Update the claimant name for a claim."""
        query = """
            UPDATE claims
            SET claimant_name = %s
            WHERE claim_id = %s;
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (new_name, claim_id))
            self.conn.commit()
            return cur.rowcount > 0

    def get_all_claims(self) -> list[dict]:
        """Return all active (non-soft-deleted) claims with their latest invoice."""
        query = """
            SELECT
                c.*,
                i.id AS invoice_id,
                i.invoice_datetime,
                i.info
            FROM claims c
            LEFT JOIN (
                SELECT DISTINCT ON (claim_id)
                    id, claim_id, invoice_datetime, info
                FROM invoice
                ORDER BY claim_id, invoice_datetime DESC
            ) i ON c.claim_id = i.claim_id
            WHERE c.recently_deleted = FALSE;
        """
        with self.conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            return [dict(zip(cols, row)) for row in rows]

    def get_claim_by_id(self, claim_id: str) -> dict | None:
        """Return a single claim by its ID."""
        query = "SELECT * FROM claims WHERE claim_id = %s;"
        with self.conn.cursor() as cur:
            cur.execute(query, (claim_id,))
            row = cur.fetchone()
            if row:
                cols = [desc[0] for desc in cur.description]
                return dict(zip(cols, row))
        return None

    def soft_delete_claim(self, claim_id: str, deleted_by: str) -> bool:
        """Mark a claim as recently deleted without removing it."""
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
        """Undo a soft-delete on a short claim."""
        query = """
            UPDATE claims
            SET recently_deleted = FALSE,
                recently_deleted_date = NULL,
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

    def get_recently_deleted_claims(self) -> list[dict]:
        """Return all claims that have been soft-deleted."""
        query = "SELECT * FROM claims WHERE recently_deleted = TRUE;"
        try:
            with self.conn.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()
                cols = [desc[0] for desc in cur.description]
                return [dict(zip(cols, row)) for row in rows]
        except Exception as e:
            print(f"Error fetching recently deleted claims: {e}")
            return []

    def permanently_delete_recently_deleted_claims(self) -> int:
        """Delete claims that have been soft-deleted for more than 3 days."""
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

    def close_claim(self, claim_id: str, closed_by: str) -> bool:
        """Close a claim and record the user who closed it."""
        query = """
            UPDATE claims
            SET closed_by = %s,
                closed_date = NOW()
            WHERE claim_id = %s;
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (closed_by, claim_id))
                if cur.rowcount == 0:
                    return False
                self.conn.commit()
                self.update_claim_status(claim_id, "close claim")
            return True
        except Exception as e:
            print(f"Error in close_claim: {e}")
            self.conn.rollback()
            return False

    def reopen_claim(self, claim_id: str) -> bool:
        """Clear close metadata to reopen a claim."""
        query = """
            UPDATE claims
            SET closed_by = NULL,
                closed_date = NULL
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
        """Update the ``status`` column of a claim."""
        query = """
            UPDATE claims
            SET status = %s
            WHERE claim_id = %s;
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (status, claim_id))
            if cur.rowcount == 0:
                return False
            self.conn.commit()
        return True

    def get_rental_by_claim(self, claim_id: str):
        """Return the ``total_cost`` from the rental agreement for ``claim_id``."""
        query = "SELECT total_cost FROM rental_agreements WHERE claim_id = %s"
        with self.conn.cursor() as cur:
            cur.execute(query, (claim_id,))
            row = cur.fetchone()
            if not row:
                return None
            (total_cost,) = row
            return total_cost

    def get_storage_by_claim(self, claim_id: str):
        """Return the ``invoice_total`` from the storage form for ``claim_id``."""
        query = "SELECT invoice_total FROM storage_forms WHERE claim_id = %s"
        with self.conn.cursor() as cur:
            cur.execute(query, (claim_id,))
            row = cur.fetchone()
            if not row:
                return None
            (invoice_total,) = row
            return invoice_total
