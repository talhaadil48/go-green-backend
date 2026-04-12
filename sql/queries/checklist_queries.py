"""
Hire-checklist query methods.

Covers all database operations for the ``hire_checklist`` table.
"""

from .base import ClaimFormBase


class HireChecklistQueries(ClaimFormBase):
    """Mixin class that provides hire-checklist read/write queries."""

    # ------------------------------------------------------------------
    # Write helpers
    # ------------------------------------------------------------------

    def upsert_hire_checklist(
        self,
        long_claim_id: str,
        car_id: int,
        claimant_id: int,
        data: dict,
    ) -> dict | None:
        """
        Insert or update a hire checklist (upsert on the composite key
        ``(long_claim_id, car_id, claimant_id)``).

        Only columns present in *data* are written.

        Args:
            long_claim_id: The owning long-claim ID.
            car_id: The numeric car ID.
            claimant_id: The numeric claimant row ID.
            data: Flat dict of column-name → value pairs.

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
                columns = ["long_claim_id", "car_id", "claimant_id"] + fields_to_update
                values_placeholders = ", ".join(f"%({col})s" for col in columns)
                set_clause = ", ".join(
                    f"{col} = EXCLUDED.{col}" for col in fields_to_update
                )

                query = f"""
                    INSERT INTO hire_checklist ({', '.join(columns)})
                    VALUES ({values_placeholders})
                    ON CONFLICT (long_claim_id, car_id, claimant_id)
                    DO UPDATE SET
                    {set_clause}
                    RETURNING *;
                """

                params = {
                    "long_claim_id": long_claim_id,
                    "car_id": car_id,
                    "claimant_id": claimant_id,
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
            self.conn.rollback()
            print("Error in upsert_hire_checklist:", e)
            return None

    # ------------------------------------------------------------------
    # Read helpers
    # ------------------------------------------------------------------

    def get_hire_checklists(
        self,
        long_claim_id: str,
        car_id: int,
        claimant_id: int,
    ) -> list[dict]:
        """
        Retrieve all hire checklists for a given long_claim + car + claimant combination.

        Results are ordered by ``inspection_id`` ascending.

        Args:
            long_claim_id: The owning long-claim ID.
            car_id: The numeric car ID.
            claimant_id: The numeric claimant row ID.

        Returns:
            List of checklist dicts (empty list if none found).
        """
        query = """
            SELECT * FROM hire_checklist
            WHERE long_claim_id = %s
            AND car_id = %s
            AND claimant_id = %s
            ORDER BY inspection_id ASC;
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (long_claim_id, car_id, claimant_id))
            rows = cur.fetchall()
            if rows:
                columns = [desc[0] for desc in cur.description]
                return [dict(zip(columns, row)) for row in rows]
        return []
