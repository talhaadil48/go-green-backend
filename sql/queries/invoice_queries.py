"""
Invoice query methods.

Covers all database operations for the ``invoice`` and
``long_hire_invoices`` tables.
"""

from datetime import datetime
from typing import Any, Dict, List

from psycopg2.extras import RealDictCursor

from .base import ClaimFormBase


class InvoiceQueries(ClaimFormBase):
    """Mixin class that provides invoice read/write queries."""

    # ------------------------------------------------------------------
    # Short-hire invoices
    # ------------------------------------------------------------------

    def insert_invoice(
        self,
        claim_id: str,
        info: str,
        docs: list,
        storage_bill: float,
        rent_bill: float,
        user_name: str,
    ) -> int:
        """
        Insert a new invoice record for a short-hire claim.

        If ``'Rental Agreement'`` is present in *docs*, the claim status is
        updated to ``"invoice sent"`` and the claim's ``invoice_date`` is
        set to now.

        Args:
            claim_id: The claim this invoice belongs to.
            info: Free-text invoice information.
            docs: List of document names included in this invoice.
            storage_bill: Storage charge amount.
            rent_bill: Rental charge amount.
            user_name: Username of the person raising the invoice.

        Returns:
            The new invoice ID, or ``0`` on failure.
        """
        if "Rental Agreement" in docs:
            self.update_claim_status(claim_id, "invoice sent")
            self.update_invoice_date(claim_id, datetime.now())

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
        payment_date=None,
        payment_amount=None,
        user=None,
    ) -> int:
        """
        Update fields on an existing invoice.

        If ``payment_date`` transitions from ``NULL`` to a real value the
        parent claim is automatically closed via
        :meth:`close_claim`.

        Args:
            invoice_id: The invoice to update.
            info: New info text or ``None`` to leave unchanged.
            storage_bill: New storage bill or ``None``.
            rent_bill: New rent bill or ``None``.
            user_name: New username or ``None``.
            payment_date: New payment date or ``None``.
            payment_amount: New payment amount or ``None``.
            user: Username performing the update (used for auto-close).

        Returns:
            The updated invoice ID, or ``0`` if not found / nothing changed.
        """
        fields = []
        values = []

        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    "SELECT payment_date, claim_id FROM invoice WHERE id = %s",
                    (invoice_id,),
                )
                prev = cur.fetchone()
                old_payment_date = prev[0] if prev else None
                claim_id = prev[1] if prev else None

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
                if payment_date is not None:
                    fields.append("payment_date = %s")
                    values.append(payment_date)
                if payment_amount is not None:
                    fields.append("payment_amount = %s")
                    values.append(payment_amount)

                if not fields:
                    return 0

                query = f"""
                    UPDATE invoice
                    SET {", ".join(fields)}
                    WHERE id = %s
                    RETURNING id, payment_date;
                """
                values.append(invoice_id)
                cur.execute(query, values)
                result = cur.fetchone()

                if result is None:
                    return 0

                new_payment_date = result[1]
                if old_payment_date is None and new_payment_date is not None:
                    self.close_claim(claim_id, user, "Invoice payment recorded")

                self.conn.commit()
                return result[0]

        except Exception as e:
            print(f"Error updating invoice: {e}")
            self.conn.rollback()
            return 0

    def get_all_invoices(self) -> list[Dict[str, Any]]:
        """
        Retrieve all invoices joined with their parent claim's name.

        Results are ordered by invoice datetime descending.

        Returns:
            List of invoice dicts.
        """
        query = """
            SELECT
                i.id, i.claim_id, c.claimant_name,
                i.invoice_datetime, i.info, i.docs,
                i.storage_bill, i.rent_bill, i.user_name,
                i.payment_date, i.payment_amount
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

    def get_invoices_by_claim_id(self, claim_id: str) -> list:
        """
        Retrieve all invoices for a given claim, newest first.

        Args:
            claim_id: The unique claim identifier.

        Returns:
            List of invoice rows.
        """
        query = """
            SELECT id, claim_id, invoice_datetime, info,
                   docs, storage_bill, rent_bill, user_name,
                   payment_date, payment_amount
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

    # ------------------------------------------------------------------
    # Long-hire invoices
    # ------------------------------------------------------------------

    def insert_long_hire_invoice(
        self, claim_id: str, amount: float, user_name: str
    ) -> int:
        """
        Insert a new long-hire invoice and mark the long claim as invoiced.

        Args:
            claim_id: The long-claim ID.
            amount: Invoice amount.
            user_name: Username of the person raising the invoice.

        Returns:
            The new long-hire invoice ID, or ``0`` on failure.
        """
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
            print(f"Error inserting long hire invoice: {e}")
            self.conn.rollback()
            return 0

    def get_all_long_hire_invoices(self) -> List[Dict[str, Any]]:
        """
        Retrieve all long-hire invoices joined with the hirer name.

        Results are ordered by date sent descending.

        Returns:
            List of long-hire invoice dicts.
        """
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
