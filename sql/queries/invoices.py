"""Invoices query mixin.

Covers: short-claim invoices and long-hire invoices.
"""

from typing import Any, Dict, List
from psycopg2.extras import RealDictCursor


class InvoicesQueries:
    """Mixin providing DB methods for ``invoice`` and ``long_hire_invoices`` tables."""

    # ── Short-claim invoices ──────────────────────────────────────────────────

    def insert_invoice(
        self,
        claim_id: str,
        info: str,
        docs: list,
        storage_bill: float,
        rent_bill: float,
        user_name: str,
    ) -> int:
        """Insert a short-claim invoice and return the new ``id``."""
        query = """
            INSERT INTO invoice (claim_id, info, docs, storage_bill, rent_bill, user_name)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id;
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (claim_id, info, docs, storage_bill, rent_bill, user_name))
                invoice_id = cur.fetchone()[0]
                self.conn.commit()
                return invoice_id
        except Exception as e:
            print(f"Error inserting invoice: {e}")
            self.conn.rollback()
            return 0

    def update_invoice(
        self,
        invoice_id: int,
        info=None,
        storage_bill=None,
        rent_bill=None,
        user_name=None,
    ):
        """Update non-None fields on a short-claim invoice."""
        fields = []
        values = []

        if info is not None:
            fields.append("info = %s")
            values.append(info)
        if storage_bill is not None:
            fields.append("storage_bill = %s")
            values.append(storage_bill)
        if rent_bill is not None:
            fields.append("rent_bill = %s")
            values.append(rent_bill)
        if user_name is not None:
            fields.append("user_name = %s")
            values.append(user_name)

        if not fields:
            return 0

        query = f"UPDATE invoice SET {', '.join(fields)} WHERE id = %s RETURNING id;"
        values.append(invoice_id)

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, values)
                result = cur.fetchone()
                if result is None:
                    return 0
                self.conn.commit()
                return result[0]
        except Exception as e:
            print(f"Error updating invoice: {e}")
            self.conn.rollback()
            return 0

    def get_all_invoices(self):
        """Return all short-claim invoices joined with claimant name."""
        query = """
            SELECT
                i.id, i.claim_id, c.claimant_name,
                i.invoice_datetime, i.info, i.docs,
                i.storage_bill, i.rent_bill, i.user_name
            FROM invoice i
            LEFT JOIN claims c ON i.claim_id = c.claim_id
            ORDER BY i.invoice_datetime DESC;
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query)
                return cur.fetchall()
        except Exception as e:
            print(f"Error fetching all invoices: {e}")
            return []

    def get_invoices_by_claim_id(self, claim_id: str):
        """Return all invoices for a specific claim."""
        query = """
            SELECT id, claim_id, invoice_datetime, info,
                   docs, storage_bill, rent_bill, user_name
            FROM invoice
            WHERE claim_id = %s
            ORDER BY invoice_datetime DESC;
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (claim_id,))
                return cur.fetchall()
        except Exception as e:
            print(f"Error fetching invoices: {e}")
            return []

    # ── Long-hire invoices ────────────────────────────────────────────────────

    def insert_long_hire_invoice(
        self, claim_id: str, amount: float, user_name: str
    ) -> int:
        """Create a long-hire invoice and mark the long claim as invoiced."""
        insert_query = """
            INSERT INTO long_hire_invoices (claim_id, amount, date_sent, user_name)
            VALUES (%s, %s, CURRENT_DATE, %s)
            RETURNING id;
        """
        update_claim_query = """
            UPDATE long_claims
            SET invoice_sent = TRUE,
                date_sent = CURRENT_DATE
            WHERE id = %s;
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(insert_query, (claim_id, amount, user_name))
                invoice_id = cur.fetchone()[0]
                cur.execute(update_claim_query, (claim_id,))
                self.conn.commit()
                return invoice_id
        except Exception as e:
            print(f"Error inserting long hire invoice and updating claim: {e}")
            self.conn.rollback()
            return 0

    def get_all_long_hire_invoices(self) -> List[Dict[str, Any]]:
        """Return all long-hire invoices joined with hirer name."""
        query = """
            SELECT
                lhi.id, lhi.claim_id, lc.hirer_name,
                lhi.amount, lhi.date_sent, lhi.user_name
            FROM long_hire_invoices lhi
            LEFT JOIN long_claims lc ON lhi.claim_id = lc.id
            ORDER BY lhi.date_sent DESC;
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query)
                return cur.fetchall()
        except Exception as e:
            print(f"Error fetching long hire invoices: {e}")
            return []
