"""
Cancellation-form and storage-form query methods.

Covers all database operations for the ``cancellation_forms`` and
``storage_forms`` tables.
"""

from .base import ClaimFormBase


class CancellationFormQueries(ClaimFormBase):
    """Mixin class for cancellation-form read/write queries."""

    def upsert_cancellation_form(self, claim_id: str, data: dict) -> dict | None:
        """
        Insert or update a cancellation form (upsert on ``claim_id``).

        Only columns present in *data* are written.

        Args:
            claim_id: The claim this form belongs to.
            data: Flat dict of column-name → value pairs.

        Returns:
            The saved row as a dict, or ``None`` if no fields were provided
            or on failure.
        """
        updatable_columns = [
            "name", "address", "postcode", "email",
            "cancellation_date", "cancellation_signature",
        ]

        fields_to_update = [col for col in updatable_columns if col in data]

        if not fields_to_update:
            return None

        set_clause = ", ".join(f"{col} = EXCLUDED.{col}" for col in fields_to_update)
        columns = ["claim_id"] + fields_to_update
        values_placeholders = ", ".join(f"%({col})s" for col in columns)

        query = f"""
            INSERT INTO cancellation_forms ({', '.join(columns)})
            VALUES ({values_placeholders})
            ON CONFLICT (claim_id)
            DO UPDATE SET
                {set_clause}
            RETURNING *;
        """

        params = {"claim_id": claim_id, **{k: data[k] for k in fields_to_update}}

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, params)
                row = cur.fetchone()
                if row:
                    self.conn.commit()
                    col_names = [desc[0] for desc in cur.description]
                    return dict(zip(col_names, row))
            return None
        except Exception as e:
            print(f"Error in upsert_cancellation_form: {e}")
            self.conn.rollback()
            return None

    def get_cancellation_form(self, claim_id: str) -> dict | None:
        """
        Retrieve the cancellation form for a given claim.

        Args:
            claim_id: The unique claim identifier.

        Returns:
            The row as a dict, or ``None`` if not found.
        """
        query = "SELECT * FROM cancellation_forms WHERE claim_id = %s;"
        with self.conn.cursor() as cur:
            cur.execute(query, (claim_id,))
            row = cur.fetchone()
            if row:
                columns = [desc[0] for desc in cur.description]
                return dict(zip(columns, row))
        return None


class StorageFormQueries(ClaimFormBase):
    """Mixin class for storage-form read/write queries."""

    def upsert_storage_form(self, claim_id: str, data: dict) -> dict | None:
        """
        Insert or update a storage form / storage invoice (upsert on ``claim_id``).

        Empty-string values are coerced to ``None`` so numeric columns do not
        receive invalid data.  Only columns present in *data* are written.

        Args:
            claim_id: The claim this form belongs to.
            data: Flat dict of column-name → value pairs.

        Returns:
            The saved row as a dict, or ``None`` if no valid fields were
            provided or on failure.
        """
        updatable_columns = [
            "name", "postcode", "address1", "address2",
            "vehicle_make", "vehicle_model", "registration_number",
            "date_of_recovery", "storage_start_date", "storage_end_date",
            "number_of_days", "charges_per_day", "total_storage_charge",
            "recovery_charge", "subtotal", "vat_amount", "invoice_total",
            "client_date", "owner_date",
            "client_signature", "owner_signature",
            "storage_location_key",
        ]

        fields_to_update = [col for col in updatable_columns if col in data]

        if not fields_to_update:
            print("No fields to update in storage form")
            return None

        # Coerce empty strings to None so numeric columns stay valid
        cleaned_data = {k: None if v == "" else v for k, v in data.items()}

        set_clause = ", ".join(f"{col} = EXCLUDED.{col}" for col in fields_to_update)
        columns = ["claim_id"] + fields_to_update
        values_placeholders = ", ".join(f"%({col})s" for col in columns)

        query = f"""
            INSERT INTO storage_forms ({', '.join(columns)})
            VALUES ({values_placeholders})
            ON CONFLICT (claim_id)
            DO UPDATE SET
                {set_clause}
            RETURNING *;
        """

        params = {"claim_id": claim_id, **{k: cleaned_data[k] for k in fields_to_update}}

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, params)
                row = cur.fetchone()
                if row:
                    self.conn.commit()
                    col_names = [desc[0] for desc in cur.description]
                    return dict(zip(col_names, row))
            return None
        except Exception as e:
            print(f"Error in upsert_storage_form: {e}")
            self.conn.rollback()
            return None

    def get_storage_form(self, claim_id: str) -> dict | None:
        """
        Retrieve the storage form for a given claim.

        Args:
            claim_id: The unique claim identifier.

        Returns:
            The row as a dict, or ``None`` if not found.
        """
        query = "SELECT * FROM storage_forms WHERE claim_id = %s;"
        with self.conn.cursor() as cur:
            cur.execute(query, (claim_id,))
            row = cur.fetchone()
            if row:
                columns = [desc[0] for desc in cur.description]
                return dict(zip(columns, row))
        return None

    def get_storage_by_claim(self, claim_id: str) -> float | None:
        """
        Return the ``invoice_total`` for the storage form associated with a claim.

        Args:
            claim_id: The unique claim identifier.

        Returns:
            The invoice total as a float, or ``None`` if not found.
        """
        query = "SELECT invoice_total FROM storage_forms WHERE claim_id = %s"
        with self.conn.cursor() as cur:
            cur.execute(query, (claim_id,))
            row = cur.fetchone()
            if not row:
                return None
            (invoice_total,) = row
            return invoice_total
