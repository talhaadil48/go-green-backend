"""Form-data query mixin.

Covers: accident claims, pre-inspection forms, cancellation forms,
storage forms, and rental agreements.
"""

from typing import Optional


class FormQueries:
    """Mixin providing upsert / read methods for all form-type tables."""

    # ── Accident Claims ───────────────────────────────────────────────────────

    def upsert_accident_claim(self, claim_id: str, data: dict) -> dict | None:
        """Insert or update an accident claim row, returning the saved row."""
        updatable_columns = [
            "checklist_vd", "checklist_pi", "checklist_dvla", "checklist_badge",
            "checklist_recovery", "checklist_hire", "checklist_ni_no",
            "checklist_storage", "checklist_plate", "checklist_licence", "checklist_logbook",
            "date_of_claim", "accident_date", "accident_time", "accident_location",
            "accident_description",
            "owner_full_name", "owner_email", "owner_telephone", "owner_address",
            "owner_postcode", "owner_dob", "owner_ni_number", "owner_occupation",
            "driver_full_name", "driver_email", "driver_telephone", "driver_address",
            "driver_postcode", "driver_dob", "driver_ni_number", "driver_occupation",
            "client_vehicle_make", "client_vehicle_model", "client_registration",
            "client_policy_no", "client_cover_type", "client_policy_holder",
            "third_party_name", "third_party_email", "third_party_telephone",
            "third_party_address", "third_party_postcode", "third_party_dob",
            "third_party_ni_number", "third_party_occupation",
            "third_party_vehicle_make", "third_party_vehicle_model",
            "third_party_registration", "third_party_policy_no", "third_party_policy_holder",
            "fault_opinion", "fault_reason", "road_conditions", "weather_conditions",
            "witness1_name", "witness1_address", "witness1_postcode", "witness1_telephone",
            "witness2_name", "witness2_address", "witness2_postcode", "witness2_telephone",
            "loss_of_earnings", "employer_details",
            "print_name", "declaration_date", "client_signature",
            "circumstance_drawing", "direction_before_drawing", "direction_after_drawing",
        ]

        fields_to_update = [col for col in updatable_columns if col in data]

        if not fields_to_update and claim_id not in data:
            return None

        set_clause = ", ".join(f"{col} = EXCLUDED.{col}" for col in fields_to_update)
        columns = ["claim_id"] + fields_to_update
        values_placeholders = ", ".join(f"%({col})s" for col in columns)

        query = f"""
        INSERT INTO accident_claims ({', '.join(columns)})
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
                    cols = [desc[0] for desc in cur.description]
                    return dict(zip(cols, row))
            return None
        except Exception as e:
            print(f"Error in upsert_accident_claim: {e}")
            self.conn.rollback()
            return None

    def upsert_accident_claim_with_json(
        self,
        claim_id: str,
        value_column: str,
        value: str,
        json_column: str,
        json_data: dict | None,
    ) -> dict | None:
        """Update a value column and its JSON companion on an accident claim row."""
        from psycopg2.extras import RealDictCursor

        if value_column not in ["direction_before_drawing", "direction_after_drawing"]:
            return None
        if json_column not in ["json_before", "json_after"]:
            return None

        query = f"""
            INSERT INTO accident_claims (claim_id, {value_column}, {json_column})
            VALUES (%s, %s, %s)
            ON CONFLICT (claim_id)
            DO UPDATE SET
                {value_column} = EXCLUDED.{value_column},
                {json_column} = EXCLUDED.{json_column}
            RETURNING *;
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (claim_id, value, json_data))
            self.conn.commit()
            return cur.fetchone()

    def get_accident_claim(self, claim_id: str) -> dict | None:
        """Return the accident claim row for ``claim_id``."""
        query = "SELECT * FROM accident_claims WHERE claim_id = %s;"
        with self.conn.cursor() as cur:
            cur.execute(query, (claim_id,))
            row = cur.fetchone()
            if row:
                cols = [desc[0] for desc in cur.description]
                return dict(zip(cols, row))
        return None

    # ── Pre-Inspection Forms ──────────────────────────────────────────────────

    def upsert_pre_inspection_form(
        self,
        claim_id: str,
        data: dict,
        inspection_id: Optional[str] = None,
    ) -> dict | None:
        """Insert or update a pre-inspection form row."""
        updatable_columns = [
            *[f"condition_{i}" for i in range(1, 31)],
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
                    columns = ["claim_id", "inspection_id"] + fields_to_update
                    values_placeholders = ", ".join(f"%({col})s" for col in columns)
                    set_clause = ", ".join(
                        f"{col} = EXCLUDED.{col}" for col in fields_to_update
                    )
                    query = f"""
                    INSERT INTO pre_inspection_forms ({', '.join(columns)})
                    VALUES ({values_placeholders})
                    ON CONFLICT (inspection_id)
                    DO UPDATE SET {set_clause}
                    RETURNING *;
                    """
                    params = {
                        "claim_id": claim_id,
                        "inspection_id": inspection_id,
                        **{col: data[col] for col in fields_to_update},
                    }
                else:
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

                cols = [desc[0] for desc in cur.description]
                self.conn.commit()
                return dict(zip(cols, row))

        except Exception as e:
            print(f"Error in upsert_pre_inspection_form: {e}")
            self.conn.rollback()
            return None

    def get_pre_inspection_form(self, claim_id: str) -> list[dict]:
        """Return all pre-inspection forms for ``claim_id`` ordered by inspection_id."""
        query = """
        SELECT * FROM pre_inspection_forms
        WHERE claim_id = %s
        ORDER BY inspection_id ASC;
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (claim_id,))
            rows = cur.fetchall()
            if rows:
                cols = [desc[0] for desc in cur.description]
                return [dict(zip(cols, row)) for row in rows]
        return []

    def get_pre_inspection_form_by_inspection(
        self, inspection_id: str
    ) -> dict | None:
        """Return a single pre-inspection form by ``inspection_id``."""
        query = "SELECT * FROM pre_inspection_forms WHERE inspection_id = %s;"
        with self.conn.cursor() as cur:
            cur.execute(query, (inspection_id,))
            row = cur.fetchone()
            if row:
                cols = [desc[0] for desc in cur.description]
                return dict(zip(cols, row))
        return None

    # ── Cancellation Forms ────────────────────────────────────────────────────

    def upsert_cancellation_form(self, claim_id: str, data: dict) -> dict | None:
        """Insert or update a cancellation form row."""
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
        DO UPDATE SET {set_clause}
        RETURNING *;
        """
        params = {"claim_id": claim_id, **{k: data[k] for k in fields_to_update}}

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, params)
                row = cur.fetchone()
                if row:
                    self.conn.commit()
                    cols = [desc[0] for desc in cur.description]
                    return dict(zip(cols, row))
            return None
        except Exception as e:
            print(f"Error in upsert_cancellation_form: {e}")
            self.conn.rollback()
            return None

    def get_cancellation_form(self, claim_id: str) -> dict | None:
        """Return the cancellation form for ``claim_id``."""
        query = "SELECT * FROM cancellation_forms WHERE claim_id = %s;"
        with self.conn.cursor() as cur:
            cur.execute(query, (claim_id,))
            row = cur.fetchone()
            if row:
                cols = [desc[0] for desc in cur.description]
                return dict(zip(cols, row))
        return None

    # ── Storage Forms ─────────────────────────────────────────────────────────

    def upsert_storage_form(self, claim_id: str, data: dict) -> dict | None:
        """Insert or update a storage form row."""
        updatable_columns = [
            "name", "postcode", "address1", "address2",
            "vehicle_make", "vehicle_model", "registration_number",
            "date_of_recovery", "storage_start_date", "storage_end_date",
            "number_of_days", "charges_per_day", "total_storage_charge",
            "recovery_charge", "subtotal", "vat_amount", "invoice_total",
            "client_date", "owner_date", "client_signature", "owner_signature",
        ]
        fields_to_update = [col for col in updatable_columns if col in data]
        if not fields_to_update:
            print("No fields to update in storage form")
            return None

        cleaned_data = {k: None if v == "" else v for k, v in data.items()}
        set_clause = ", ".join(f"{col} = EXCLUDED.{col}" for col in fields_to_update)
        columns = ["claim_id"] + fields_to_update
        values_placeholders = ", ".join(f"%({col})s" for col in columns)

        query = f"""
        INSERT INTO storage_forms ({', '.join(columns)})
        VALUES ({values_placeholders})
        ON CONFLICT (claim_id)
        DO UPDATE SET {set_clause}
        RETURNING *;
        """
        params = {
            "claim_id": claim_id,
            **{k: cleaned_data[k] for k in fields_to_update},
        }

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, params)
                row = cur.fetchone()
                if row:
                    self.conn.commit()
                    cols = [desc[0] for desc in cur.description]
                    return dict(zip(cols, row))
            return None
        except Exception as e:
            print(f"Error in upsert_storage_form: {e}")
            self.conn.rollback()
            return None

    def get_storage_form(self, claim_id: str) -> dict | None:
        """Return the storage form for ``claim_id``."""
        query = "SELECT * FROM storage_forms WHERE claim_id = %s;"
        with self.conn.cursor() as cur:
            cur.execute(query, (claim_id,))
            row = cur.fetchone()
            if row:
                cols = [desc[0] for desc in cur.description]
                return dict(zip(cols, row))
        return None

    # ── Rental Agreements ─────────────────────────────────────────────────────

    def upsert_rental_agreement(self, claim_id: str, data: dict) -> dict | None:
        """Insert or update a rental agreement row.

        Also auto-updates the parent claim status to ``hire start`` / ``hire end``
        based on whether the hire vehicle dates are present.
        """
        updatable_columns = [
            "hirer_name", "title", "permanent_address",
            "additional_driver_name", "licence_no",
            "new_date_issued", "new_expiry_date", "new_dob",
            "new_date_test_passed", "new_licence_no", "new_occupation",
            "date_issued", "expiry_date", "dob", "date_test_passed", "occupation",
            "daily_rate", "policy_excess", "deposit", "refuelling_charge",
            "insurance_company", "policy_no", "insurance_dates",
            "own_insurance_confirm", "insurance_date", "insurance_time",
            "motoring_offence_3yrs", "disqualified_5yrs", "accident_3yrs",
            "insurance_declined_5yrs", "dishonesty_conviction",
            "medical_condition1", "medical_condition2", "medical_details",
            "additional_driver_auth",
            "hire_vehicle_reg", "hire_vehicle_make", "hire_vehicle_model",
            "hire_vehicle_group", "hire_vehicle_date_out", "hire_vehicle_date_in",
            "hire_vehicle_fuel_out", "hire_vehicle_fuel_in",
            "change_vehicle_reg", "change_vehicle_make", "change_vehicle_model",
            "change_vehicle_group", "change_vehicle_date_out", "change_vehicle_date_in",
            "change_vehicle_fuel_out", "change_vehicle_fuel_in",
            "admin_fee", "delivery_charge", "cdw_per_day",
            "days_out", "days_in", "total_days",
            "rate_per_day", "refuelling_total", "subtotal", "vat", "total_cost",
            "declaration_date", "liability_date",
            "hirer_signature_terms", "company_signature",
            "hirer_signature_insurance", "declaration_signature", "liability_signature",
        ]

        fields_to_update = [col for col in updatable_columns if col in data]
        if not fields_to_update:
            return None

        set_clause = ", ".join(f"{col} = EXCLUDED.{col}" for col in fields_to_update)
        columns = ["claim_id"] + fields_to_update
        values_placeholders = ", ".join(f"%({col})s" for col in columns)

        query = f"""
        INSERT INTO rental_agreements ({', '.join(columns)})
        VALUES ({values_placeholders})
        ON CONFLICT (claim_id)
        DO UPDATE SET {set_clause}
        RETURNING *;
        """
        params = {"claim_id": claim_id, **{k: data[k] for k in fields_to_update}}

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, params)
                row = cur.fetchone()
                if row:
                    col_names = [desc[0] for desc in cur.description]
                    result = dict(zip(col_names, row))

                    hire_out = result.get("hire_vehicle_date_out")
                    hire_in = result.get("hire_vehicle_date_in")
                    if hire_out and hire_in:
                        self.update_claim_status(claim_id, "hire end")
                    elif hire_out:
                        self.update_claim_status(claim_id, "hire start")

                    self.conn.commit()
                    return result
            return None
        except Exception as e:
            print(f"Error in upsert_rental_agreement: {e}")
            self.conn.rollback()
            return None

    def get_rental_agreement(self, claim_id: str) -> dict | None:
        """Return the rental agreement for ``claim_id``."""
        query = "SELECT * FROM rental_agreements WHERE claim_id = %s;"
        with self.conn.cursor() as cur:
            cur.execute(query, (claim_id,))
            row = cur.fetchone()
            if row:
                cols = [desc[0] for desc in cur.description]
                return dict(zip(cols, row))
        return None
