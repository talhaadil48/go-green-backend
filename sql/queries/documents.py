"""Documents query mixin.

Covers: claim_documents table operations.
"""

import json


class DocumentsQueries:
    """Mixin providing DB methods for the ``claim_documents`` table."""

    def upsert_claim_documents(self, claim_id: str, documents: dict) -> None:
        """Merge ``documents`` into the existing JSON map for ``claim_id``."""
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
        """Remove a single document key from the JSON map."""
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
        """Return the documents row for ``claim_id``."""
        query = "SELECT * FROM claim_documents WHERE claim_id = %s;"
        with self.conn.cursor() as cur:
            cur.execute(query, (claim_id,))
            row = cur.fetchone()
            if row:
                cols = [desc[0] for desc in cur.description]
                return dict(zip(cols, row))
        return None
