"""
Claim-document query methods.

Covers all database operations for the ``claim_documents`` table.
"""

import json
from .base import ClaimFormBase


class DocumentQueries(ClaimFormBase):
    """Mixin class that provides claim-document read/write queries."""

    def upsert_claim_documents(self, claim_id: str, documents: dict) -> None:
        """
        Insert or merge documents into a claim's document store.

        On conflict the new ``documents`` JSON object is merged with the
        existing one using the Postgres ``||`` operator so previously stored
        documents are preserved.

        Args:
            claim_id: The unique claim identifier.
            documents: Dict mapping document name → value (e.g. URL or status).
        """
        query = """
            INSERT INTO claim_documents (claim_id, documents)
            VALUES (%s, %s)
            ON CONFLICT (claim_id)
            DO UPDATE
            SET documents = claim_documents.documents || EXCLUDED.documents;
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (claim_id, json.dumps(documents)))
                self.conn.commit()
        except Exception as e:
            print(f"Error in upsert_claim_documents: {e}")
            self.conn.rollback()

    def delete_claim_document(self, claim_id: str, doc_name: str) -> bool:
        """
        Remove a single document entry from a claim's document store.

        The document is removed from the JSONB column using the ``-`` operator.

        Args:
            claim_id: The unique claim identifier.
            doc_name: Key of the document to remove.

        Returns:
            ``True`` if the claim was found and updated, ``False`` otherwise.
        """
        query = """
            UPDATE claim_documents
            SET documents = documents - %s
            WHERE claim_id = %s
            RETURNING claim_id;
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (doc_name, claim_id))
                result = cur.fetchone()
                self.conn.commit()
                return bool(result)
        except Exception as e:
            print(f"Error in delete_claim_document: {e}")
            self.conn.rollback()
            return False

    def get_claim_documents(self, claim_id: str) -> dict | None:
        """
        Retrieve the document store for a claim.

        Args:
            claim_id: The unique claim identifier.

        Returns:
            The row as a dict (containing ``claim_id`` and ``documents``),
            or ``None`` if not found.
        """
        query = "SELECT * FROM claim_documents WHERE claim_id = %s;"
        with self.conn.cursor() as cur:
            cur.execute(query, (claim_id,))
            row = cur.fetchone()
            if row:
                columns = [desc[0] for desc in cur.description]
                return dict(zip(columns, row))
        return None
