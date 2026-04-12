"""
Pre-inspection-form query methods.

All database operations for the ``pre_inspection_forms`` table live here.
"""

from .base import ClaimFormBase


class PreInspectionQueries(ClaimFormBase):
    """Mixin class that provides pre-inspection-form read/write queries."""

    # ------------------------------------------------------------------
    # Write helpers
    # ------------------------------------------------------------------

    def upsert_pre_inspection_form(
        self,
        claim_id: str,
        data: dict,
        inspection_id: str = None,
    ) -> dict | None:
        """
        Insert a new pre-inspection form row, or update an existing one.

        - When *inspection_id* is supplied the existing row with that ID is
          updated (upsert on ``inspection_id``).
        - When *inspection_id* is omitted a new row is inserted.

        Only columns present in *data* are written.

        Args:
            claim_id: The claim this inspection belongs to.
            data: Flat dict of column-name → value pairs.
            inspection_id: Optional existing inspection row ID to update.

        Returns:
            The saved row as a dict, or ``None`` on failure.
        """
        updatable_columns = [
            "condition_1", "condition_2", "condition_3", "condition_4", "condition_5",
            "condition_6", "condition_7", "condition_8", "condition_9", "condition_10",
            "condition_11", "condition_12", "condition_13", "condition_14", "condition_15",
            "condition_16", "condition_17", "condition_18", "condition_19", "condition_20",
            "condition_21", "condition_22", "condition_23", "condition_24", "condition_25",
            "condition_26", "condition_27", "condition_28", "condition_29", "condition_30",
            "date", "customer", "detailer", "order_number",
            "year", "make", "model",
            "notes", "recommendations",
            "customer_signature", "detailer_signature",
            "base_vehicle_image", "annotated_vehicle_image",
        ]

        fields_to_update = [col for col in updatable_columns if col in data]

        try:
            with self.conn.cursor() as cur:
                if inspection_id:
                    # UPDATE existing row keyed on inspection_id
                    columns = ["claim_id", "inspection_id"] + fields_to_update
                    values_placeholders = ", ".join(f"%({col})s" for col in columns)
                    set_clause = ", ".join(
                        f"{col} = EXCLUDED.{col}" for col in fields_to_update
                    )
                    query = f"""
                        INSERT INTO pre_inspection_forms ({', '.join(columns)})
                        VALUES ({values_placeholders})
                        ON CONFLICT (inspection_id)
                        DO UPDATE SET
                            {set_clause}
                        RETURNING *;
                    """
                    params = {
                        "claim_id": claim_id,
                        "inspection_id": inspection_id,
                        **{col: data[col] for col in fields_to_update},
                    }
                else:
                    # INSERT new row
                    columns = ["claim_id"] + fields_to_update
                    values_placeholders = ", ".join(f"%({col})s" for col in columns)
                    query = f"""
                        INSERT INTO pre_inspection_forms ({', '.join(columns)})
                        VALUES ({values_placeholders})
                        RETURNING *;
                    """
                    params = {
                        "claim_id": claim_id,
                        **{col: data[col] for col in fields_to_update},
                    }

                cur.execute(query, params)
                row = cur.fetchone()

                if not row:
                    self.conn.commit()
                    return None

                col_names = [desc[0] for desc in cur.description]
                self.conn.commit()
                return dict(zip(col_names, row))

        except Exception as e:
            print(f"Error in upsert_pre_inspection_form: {e}")
            self.conn.rollback()
            return None

    # ------------------------------------------------------------------
    # Read helpers
    # ------------------------------------------------------------------

    def get_pre_inspection_form(self, claim_id: str) -> list[dict]:
        """
        Retrieve all pre-inspection forms for a given claim.

        Forms are ordered by ``inspection_id`` ascending so the earliest
        inspection is first.

        Args:
            claim_id: The claim whose forms to retrieve.

        Returns:
            List of row dicts (empty list if none found).
        """
        query = """
            SELECT * FROM pre_inspection_forms
            WHERE claim_id = %s
            ORDER BY inspection_id ASC;
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (claim_id,))
            rows = cur.fetchall()
            if rows:
                columns = [desc[0] for desc in cur.description]
                return [dict(zip(columns, row)) for row in rows]
        return []

    def get_pre_inspection_form_by_inspection(self, inspection_id: str) -> dict | None:
        """
        Retrieve a single pre-inspection form by its inspection ID.

        Args:
            inspection_id: The unique inspection row identifier.

        Returns:
            The row as a dict, or ``None`` if not found.
        """
        query = "SELECT * FROM pre_inspection_forms WHERE inspection_id = %s;"
        with self.conn.cursor() as cur:
            cur.execute(query, (inspection_id,))
            row = cur.fetchone()
            if row:
                columns = [desc[0] for desc in cur.description]
                return dict(zip(columns, row))
        return None
