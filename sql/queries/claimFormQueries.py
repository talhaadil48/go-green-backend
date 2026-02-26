from datetime import datetime, timezone
from typing import Optional
import json
from psycopg2.extras import RealDictCursor



class ClaimFormQueries:
    def __init__(self, conn):
        self.conn = conn

    def upsert_accident_claim(self, claim_id: str, data: dict) -> dict | None:
        """
        Upsert (insert or update) accident claim.
        Expects a flat dict with field names matching table columns (or subset).
        Returns the resulting row as dict or None if failed.
        """
        updatable_columns = [
            "checklist_vd", "checklist_pi", "checklist_dvla", "checklist_badge", "checklist_recovery",
            "checklist_hire", "checklist_ni_no", "checklist_storage", "checklist_plate",
            "checklist_licence", "checklist_logbook",
            "date_of_claim", "accident_date", "accident_time", "accident_location", "accident_description",
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
            "circumstance_drawing", "direction_before_drawing", "direction_after_drawing"
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
                    columns = [desc[0] for desc in cur.description]
                    return dict(zip(columns, row))
                return None
        except Exception as e:
            print(f"Error in upsert_accident_claim: {e}")
            self.conn.rollback()
            return None
        
    def upsert_pre_inspection_form(
        self,
        claim_id: str,
        data: dict,
        inspection_id: str = None
    ) -> dict | None:

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
            "base_vehicle_image", "annotated_vehicle_image"
        ]

        fields_to_update = [col for col in updatable_columns if col in data]

        if not fields_to_update:
            if inspection_id:
                return self.get_pre_inspection_form(inspection_id)
            forms = self.get_pre_inspection_forms_by_claim(claim_id)
            return forms[0] if forms else None

        try:
            with self.conn.cursor() as cur:

                if inspection_id:
                    columns = ["claim_id", "inspection_id"] + fields_to_update
                    values_placeholders = ", ".join(f"%({col})s" for col in columns)
                    set_clause = ", ".join(f"{col} = EXCLUDED.{col}" for col in fields_to_update)

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
                        **{col: data[col] for col in fields_to_update}
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
                        **{col: data[col] for col in fields_to_update}
                    }

                cur.execute(query, params)
                row = cur.fetchone()
                if not row:
                    self.conn.commit()
                    return None

                columns = [desc[0] for desc in cur.description]
                self.conn.commit()
                return dict(zip(columns, row))

        except Exception as e:
            print(f"Error in upsert_pre_inspection_form: {e}")
            self.conn.rollback()
            return None
    def upsert_cancellation_form(self, claim_id: str, data: dict) -> dict | None:
        updatable_columns = [
            "name", "address", "postcode", "email",
            "cancellation_date", "cancellation_signature"
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
                    columns = [desc[0] for desc in cur.description]
                    return dict(zip(columns, row))
            return None
        except Exception as e:
            print(f"Error in upsert_cancellation_form: {e}")
            self.conn.rollback()
            return None

    def upsert_storage_form(self, claim_id: str, data: dict) -> dict | None:
        updatable_columns = [
            "name", "postcode", "address1", "address2",
            "vehicle_make", "vehicle_model", "registration_number",
            "date_of_recovery", "storage_start_date", "storage_end_date",
            "number_of_days", "charges_per_day", "total_storage_charge",
            "recovery_charge", "subtotal", "vat_amount", "invoice_total",
            "client_date", "owner_date", "client_signature", "owner_signature"
        ]

        fields_to_update = [col for col in updatable_columns if col in data]

        if not fields_to_update:
            print("No fields to update in storage form")
            return None

        # Convert empty strings to None (good practice you already had)
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
                    columns = [desc[0] for desc in cur.description]
                    return dict(zip(columns, row))
            return None
        except Exception as e:
            print(f"Error in upsert_storage_form: {e}")
            self.conn.rollback()
            return None

    def upsert_rental_agreement(self, claim_id: str, data: dict) -> dict | None:
        updatable_columns = [
            "hirer_name", "title", "permanent_address",
            "additional_driver_name", "licence_no",
             "new_date_issued",
      "new_expiry_date",
      "new_dob",
      "new_date_test_passed","new_licence_no"," new_occupation"    
            "date_issued", "expiry_date", "dob", "date_test_passed", "occupation",
            "daily_rate", "policy_excess", "deposit", "refuelling_charge",
            "insurance_company", "policy_no", "insurance_dates",
            "own_insurance_confirm", "insurance_date", "insurance_time",
            "motoring_offence_3yrs", "disqualified_5yrs", "accident_3yrs",
            "insurance_declined_5yrs", "dishonesty_conviction",
            "medical_condition1", "medical_condition2", "medical_details",
            "additional_driver_auth",
            "hire_vehicle_reg", "hire_vehicle_make", "hire_vehicle_model", "hire_vehicle_group",
            "hire_vehicle_date_out", "hire_vehicle_date_in",
            "hire_vehicle_fuel_out", "hire_vehicle_fuel_in",
            "change_vehicle_reg", "change_vehicle_make", "change_vehicle_model", "change_vehicle_group",
            "change_vehicle_date_out", "change_vehicle_date_in",
            "change_vehicle_fuel_out", "change_vehicle_fuel_in",
            "admin_fee", "delivery_charge", "cdw_per_day",
            "days_out", "days_in", "total_days",
            "rate_per_day", "refuelling_total",
            "subtotal", "vat", "total_cost",
            "declaration_date", "liability_date",
            "hirer_signature_terms", "company_signature",
            "hirer_signature_insurance", "declaration_signature", "liability_signature"
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
            print(f"Error in upsert_rental_agreement: {e}")
            self.conn.rollback()
            return None

    def insert_claim(
        self,
        claimant_name: str | None,
        claim_type: str | None,
        council: str | None,               # ← new parameter
        claim_id: str | None = None
        ) -> bool:
        query = """
            INSERT INTO claims (claim_id, claimant_name, claim_type, council)
            VALUES (%s, %s, %s, %s);
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (claim_id, claimant_name, claim_type, council))
            self.conn.commit()
        return True
    


    def delete_claim(self, claim_id: str) -> bool:
        query = """
            DELETE FROM claims
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
            print(f"Error in delete_claim: {e}")
            self.conn.rollback()
            return False
        
    def update_claimant_name(self, claim_id: str, new_name: str) -> bool:
        query = """
            UPDATE claims
            SET claimant_name = %s
            WHERE claim_id = %s;
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (new_name, claim_id))
            self.conn.commit()
            return cur.rowcount > 0  # True if any row was updated

    def upsert_claim_documents(self, claim_id: str, documents: dict) -> None:
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

    def create_user(self, username: str, password: str, role: str) -> dict | None:
        query = """
            INSERT INTO users (username, password, role)
            VALUES (%s, %s, %s)
            RETURNING id, username, role;
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (username, password, role))
                row = cur.fetchone()
                self.conn.commit()
                if row:
                    columns = [desc[0] for desc in cur.description]
                    return dict(zip(columns, row))
            return None
        except Exception as e:
            print(f"Error in create_user: {e}")
            self.conn.rollback()
            return None
        
    def delete_user(self, user_id: int) -> bool:
        query = """
            DELETE FROM users
            WHERE id = %s
            RETURNING id;
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (user_id,))
                row = cur.fetchone()
                self.conn.commit()
                return row is not None
        except Exception as e:
            print(f"Error in delete_user: {e}")
            self.conn.rollback()
            return False

    def get_all_non_admin_users(self) -> list[dict]:
        query = """
            SELECT id, username, role
            FROM users
            WHERE role != 'admin'
            ORDER BY id ASC;
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()
                columns = [desc[0] for desc in cur.description]
                return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            print(f"Error in get_all_non_admin_users: {e}")
            return []
    # ────────────────────────────────────────────────
    #  Read-only methods — no need for try/except + rollback
    # ────────────────────────────────────────────────

    def get_accident_claim(self, claim_id: str) -> dict | None:
        query = "SELECT * FROM accident_claims WHERE claim_id = %s;"
        with self.conn.cursor() as cur:
            cur.execute(query, (claim_id,))
            row = cur.fetchone()
            if row:
                columns = [desc[0] for desc in cur.description]
                return dict(zip(columns, row))
        return None

    def get_pre_inspection_form(self, claim_id: str) -> list[dict]:  # Changed to list
        """
        Get ALL pre-inspection forms by claim_id (multiple rows)
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
        query = "SELECT * FROM pre_inspection_forms WHERE inspection_id = %s;"
        with self.conn.cursor() as cur:
            cur.execute(query, (inspection_id,))
            row = cur.fetchone()
            if row:
                columns = [desc[0] for desc in cur.description]
                return dict(zip(columns, row))
        return None
    def get_cancellation_form(self, claim_id: str) -> dict | None:
        query = "SELECT * FROM cancellation_forms WHERE claim_id = %s;"
        with self.conn.cursor() as cur:
            cur.execute(query, (claim_id,))
            row = cur.fetchone()
            if row:
                columns = [desc[0] for desc in cur.description]
                return dict(zip(columns, row))
        return None

    def get_storage_form(self, claim_id: str) -> dict | None:
        query = "SELECT * FROM storage_forms WHERE claim_id = %s;"
        with self.conn.cursor() as cur:
            cur.execute(query, (claim_id,))
            row = cur.fetchone()
            if row:
                columns = [desc[0] for desc in cur.description]
                return dict(zip(columns, row))
        return None

    def get_rental_agreement(self, claim_id: str) -> dict | None:
        query = "SELECT * FROM rental_agreements WHERE claim_id = %s;"
        with self.conn.cursor() as cur:
            cur.execute(query, (claim_id,))
            row = cur.fetchone()
            if row:
                columns = [desc[0] for desc in cur.description]
                return dict(zip(columns, row))
        return None

    def get_all_claims(self) -> list[dict]:
        query = """
            SELECT
                c.*,
                i.id AS invoice_id,
                i.invoice_datetime,
                i.info
            FROM claims c
            LEFT JOIN (
                SELECT DISTINCT ON (claim_id)
                    id,
                    claim_id,
                    invoice_datetime,
                    info
                FROM invoice
                ORDER BY claim_id, invoice_datetime DESC
            ) i
            ON c.claim_id = i.claim_id
            WHERE c.recently_deleted = FALSE;
        """
        with self.conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in rows]
    def get_claim_by_id(self, claim_id: str) -> dict | None:
        query = "SELECT * FROM claims WHERE claim_id = %s;"
        with self.conn.cursor() as cur:
            cur.execute(query, (claim_id,))
            row = cur.fetchone()
            if row:
                columns = [desc[0] for desc in cur.description]
                return dict(zip(columns, row))
        return None

    def get_claim_documents(self, claim_id: str) -> dict | None:
        query = "SELECT * FROM claim_documents WHERE claim_id = %s;"
        with self.conn.cursor() as cur:
            cur.execute(query, (claim_id,))
            row = cur.fetchone()
            if row:
                columns = [desc[0] for desc in cur.description]
                return dict(zip(columns, row))
        return None

    def get_user_by_username(self, username: str) -> dict | None:
        query = "SELECT * FROM users WHERE username = %s;"
        with self.conn.cursor() as cur:
            cur.execute(query, (username,))
            row = cur.fetchone()
            if row:
                columns = [desc[0] for desc in cur.description]
                return dict(zip(columns, row))
        return None
    
    
   
   
    def soft_delete_claim(self, claim_id: str) -> bool:
        query = """
            UPDATE claims
            SET recently_deleted = TRUE,
                recently_deleted_date = NOW()
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
            print(f"Error in soft_delete_claim: {e}")
            self.conn.rollback()
            return False

    def restore_claim(self, claim_id: str) -> bool:
        query = """
            UPDATE claims
            SET recently_deleted = FALSE,
                recently_deleted_date = NOW()
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
            print(f"Error in restore_claim: {e}")
            self.conn.rollback()
            return False
        
        
    def get_recently_deleted_claims(self) -> list[dict]:
        query = """
            SELECT *
            FROM claims
            WHERE recently_deleted = TRUE;
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()
                columns = [desc[0] for desc in cur.description]
                return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            print(f"Error fetching recently deleted claims: {e}")
            return []

    def mark_invoice_sent(self, claim_id: int) -> dict:
        query = """
            UPDATE claims
            SET invoice_sent = 'Sent'
            WHERE claim_id = %s
            RETURNING *;
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (claim_id,))
                row = cur.fetchone()
                if not row:
                    return {}  # claim_id not found
                columns = [desc[0] for desc in cur.description]
                return dict(zip(columns, row))
        except Exception as e:
            print(f"Error updating invoice_sent: {e}")
            return {}
        
        
    def permanently_delete_recently_deleted_claims(self) -> int:
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
        
        
    def insert_invoice(self, claim_id: str, info: str) -> int:
        query = """
            INSERT INTO invoice (claim_id, info)
            VALUES (%s, %s)
            RETURNING id;
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (claim_id, info))
                invoice_id = cur.fetchone()[0]
                self.conn.commit()
                return invoice_id
        except Exception as e:
            print(f"Error inserting invoice: {e}")
            self.conn.rollback()
            return 0
        
    def get_invoices_by_claim_id(self, claim_id: str):
        query = """
            SELECT id, claim_id, invoice_datetime, info
            FROM invoice
            WHERE claim_id = %s
            ORDER BY invoice_datetime DESC;
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (claim_id,))
                rows = cur.fetchall()
                return rows
        except Exception as e:
            print(f"Error fetching invoices: {e}")
            return []
        

    def change_user_password(self, username: str, new_password: str) -> bool:
        query = """
            UPDATE users
            SET password = %s
            WHERE username = %s
            RETURNING id;
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (new_password, username))
                row = cur.fetchone()
                self.conn.commit()
                return row is not None
        except Exception as e:
            print(f"Error in change_user_password: {e}")
            self.conn.rollback()
            return False

    def insert_car(self, model, name, reg_no) -> bool:
        try:
            query = """
                INSERT INTO cars (model, name, reg_no)
                VALUES (%s, %s, %s)
            """
            with self.conn.cursor() as cur:
                cur.execute(query, (model, name, reg_no))
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            raise e

    def update_car(self, car_id, model, name, reg_no) -> bool:
        try:
            query = """
                UPDATE cars
                SET model=%s, name=%s, reg_no=%s
                WHERE id=%s
            """
            with self.conn.cursor() as cur:
                cur.execute(query, (model, name, reg_no, car_id))
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            raise e

    def get_car_by_id(self, car_id: int):
        query = "SELECT * FROM cars WHERE id=%s"
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (car_id,))
            return cur.fetchone()

    def get_all_cars(self):
        query = "SELECT * FROM cars"
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            return cur.fetchall()
    # ---------------------- LONG CLAIMS ----------------------
    def insert_long_claim(self, starting_date, ending_date):
        try:
            query = "INSERT INTO long_claims (starting_date, ending_date) VALUES (%s, %s) RETURNING id;"
            with self.conn.cursor() as cur:
                cur.execute(query, (starting_date, ending_date))
                long_claim_id = cur.fetchone()[0]
                self.conn.commit()
            return long_claim_id
        except Exception as e:
            self.conn.rollback()
            raise e
        
    def update_long_claim(self, long_claim_id, starting_date, ending_date):
        try:
            query = """
                UPDATE long_claims
                SET starting_date = %s,
                    ending_date = %s
                WHERE id = %s;
            """
            with self.conn.cursor() as cur:
                cur.execute(query, (starting_date, ending_date, long_claim_id))
                self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e

    def add_car_to_long_claim(self, long_claim_id: str, car_id: int):
        try:
            query = "INSERT INTO long_claim_cars (long_claim_id, car_id) VALUES (%s, %s);"
            with self.conn.cursor() as cur:
                cur.execute(query, (long_claim_id, car_id))
                self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            raise e

    def remove_car_from_long_claim(self, long_claim_id: str, car_id: int):
        try:
            query = "DELETE FROM long_claim_cars WHERE long_claim_id=%s AND car_id=%s;"
            with self.conn.cursor() as cur:
                cur.execute(query, (long_claim_id, car_id))
                self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            raise e

    # ---------------------- CLAIMANT ----------------------
    def insert_claimant(
    self,
    long_claim_id,
    car_id,
    start_date=None,
    end_date=None,
    miles=None,
    name=None,
    location=None,
    delivery_charges=0
):
        try:
            query = """
                INSERT INTO claimant
                (long_claim_id, car_id, start_date, end_date, miles, name, location, delivery_charges)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """
            with self.conn.cursor() as cur:
                cur.execute(
                    query,
                    (long_claim_id, car_id, start_date, end_date, miles, name, location, delivery_charges)
                )
                claimant_id = cur.fetchone()[0]
            self.conn.commit()
            return claimant_id
        except Exception as e:
            self.conn.rollback()
            raise e


    def update_claimant(
        self,
        claimant_id,
        start_date=None,
        end_date=None,
        miles=None,
        name=None,
        location=None,
        delivery_charges=None
    ):
        try:
            # Build dynamic update to skip None fields
            fields = []
            values = []

            if start_date is not None:
                fields.append("start_date=%s")
                values.append(start_date)
            if end_date is not None:
                fields.append("end_date=%s")
                values.append(end_date)
            if miles is not None:
                fields.append("miles=%s")
                values.append(miles)
            if name is not None:
                fields.append("name=%s")
                values.append(name)
            if location is not None:
                fields.append("location=%s")
                values.append(location)
            if delivery_charges is not None:
                fields.append("delivery_charges=%s")
                values.append(delivery_charges)

            if not fields:
                return False  # Nothing to update

            query = f"""
                UPDATE claimant
                SET {', '.join(fields)}
                WHERE id=%s
            """
            values.append(claimant_id)

            with self.conn.cursor() as cur:
                cur.execute(query, tuple(values))

            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            raise e

    def delete_claimant(self, claimant_id: int):
        try:
            query = "DELETE FROM claimant WHERE id=%s"
            with self.conn.cursor() as cur:
                cur.execute(query, (claimant_id,))
            self.conn.commit()
            return cur.rowcount > 0  # True if a row was deleted
        except Exception as e:
            self.conn.rollback()
            raise e
    def get_claimant(self, claimant_id=None, long_claim_id=None, car_id=None):
        query = "SELECT * FROM claimant WHERE 1=1"
        params = []

        if claimant_id:
            query += " AND id=%s"
            params.append(claimant_id)

        if long_claim_id:
            query += " AND long_claim_id=%s"
            params.append(long_claim_id)

        if car_id:
            query += " AND car_id=%s"
            params.append(car_id)

        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            return cur.fetchall()

    def get_all_claimants(self):
        query = "SELECT * FROM claimant ORDER BY id DESC"
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            return cur.fetchall()
    # ---------------------- HIRE CHECKLIST ----------------------
  

    def get_all_long_claims(self):
        query = """
            SELECT
                id,
                starting_date,
                ending_date,
                invoice_sent,
                date_sent
                
            FROM long_claims
            WHERE recently_deleted = FALSE
            ORDER BY id DESC
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            return cur.fetchall()
        


    def get_claimants_by_car(self, car_id):
        query = """
            SELECT *
            FROM claimant
            WHERE car_id = %s
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (car_id,))
            return cur.fetchall()
        
    def get_cars_by_long_claim(self, long_claim_id):
        query = """
            SELECT c.*
            FROM long_claim_cars lcc
            JOIN cars c ON c.id = lcc.car_id
            WHERE lcc.long_claim_id = %s
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (long_claim_id,))
            return cur.fetchall()

    def get_long_claim_by_id(self, claim_id):
        query = """
            SELECT
                id,
                starting_date,
                ending_date,
                invoice_sent
            FROM long_claims
            WHERE id = %s
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (claim_id,))
            return cur.fetchone()
        


    def mark_invoice(self, long_claim_id: str):
        try:
            query = """
                UPDATE long_claims
                SET invoice_sent = TRUE,
                    date_sent = CURRENT_DATE
                WHERE id = %s
            """
            with self.conn.cursor() as cur:
                cur.execute(query, (long_claim_id,))
            self.conn.commit()
            return cur.rowcount > 0  # True if a row was updated
        except Exception as e:
            self.conn.rollback()
            raise e

    def mark_as_recently_deleted(self, claim_id: str):
        query = """
            UPDATE long_claims
            SET recently_deleted = TRUE,
                recently_deleted_date = NOW()
            WHERE id = %s
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (claim_id,))
            self.conn.commit()
            return cur.rowcount
        
    def delete_long_claim(self, claim_id: str):
        query = "DELETE FROM long_claims WHERE id = %s"
        with self.conn.cursor() as cur:
            cur.execute(query, (claim_id,))
            self.conn.commit()
            return cur.rowcount > 0  # True if a row was deleted
        
    def restore_claim(self, claim_id: str):
        query = """
            UPDATE long_claims
            SET recently_deleted = FALSE,
                recently_deleted_date = NULL
            WHERE id = %s
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (claim_id,))
            self.conn.commit()
            return cur.rowcount
        

    def get_soft_deleted_long_claims(self):
        query = """
            SELECT
                id,
                starting_date,
                ending_date,
                invoice_sent,
                date_sent
            FROM long_claims
            WHERE recently_deleted = TRUE
            ORDER BY id DESC
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            return cur.fetchall()



    def upsert_hire_checklist(
    self,
    long_claim_id: str,
    car_id: int,
    claimant_id: int,
    data: dict,
    inspection_id = None
) -> dict | None:
        """
        Upsert logic for hire_checklist table.
        • inspection_id provided → UPDATE that row
        • no inspection_id     → INSERT new row
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
            "base_vehicle_image", "annotated_vehicle_image"
        ]

        fields_to_update = [col for col in updatable_columns if col in data]

        # If caller sent no updatable fields → just return current record (if exists)
        if not fields_to_update:
            if inspection_id:
                # You should implement get_hire_checklist(inspection_id) if you want this behaviour
                return self.get_hire_checklist(inspection_id)  # ← placeholder
            records = self.get_hire_checklists_by_claim(long_claim_id, car_id, claimant_id)
            return records[0] if records else None

        try:
            with self.conn.cursor() as cur:

                if inspection_id:
                    # ─── UPSERT (INSERT or UPDATE on inspection_id) ───────────────
                    columns = ["long_claim_id", "car_id", "claimant_id", "inspection_id"] + fields_to_update
                    values_placeholders = ", ".join(f"%({col})s" for col in columns)
                    set_clause = ", ".join(f"{col} = EXCLUDED.{col}" for col in fields_to_update)

                    query = f"""
                    INSERT INTO hire_checklist ({', '.join(columns)})
                    VALUES ({values_placeholders})
                    ON CONFLICT (inspection_id)
                    DO UPDATE SET
                        {set_clause}
                    RETURNING *;
                    """

                    params = {
                        "long_claim_id": long_claim_id,
                        "car_id": car_id,
                        "claimant_id": claimant_id,
                        "inspection_id": inspection_id,
                        **{col: data[col] for col in fields_to_update}
                    }

                else:
                    # ─── INSERT new record ────────────────────────────────────────
                    columns = ["long_claim_id", "car_id", "claimant_id"] + fields_to_update
                    values_placeholders = ", ".join(f"%({col})s" for col in columns)

                    query = f"""
                    INSERT INTO hire_checklist ({', '.join(columns)})
                    VALUES ({values_placeholders})
                    RETURNING *;
                    """

                    params = {
                        "long_claim_id": long_claim_id,
                        "car_id": car_id,
                        "claimant_id": claimant_id,
                        **{col: data[col] for col in fields_to_update}
                    }

                cur.execute(query, params)
                row = cur.fetchone()
                if not row:
                    self.conn.commit()
                    return None

                columns_list = [desc[0] for desc in cur.description]
                self.conn.commit()
                return dict(zip(columns_list, row))

        except Exception as e:
            print(f"Error in upsert_hire_checklist: {e}")
            self.conn.rollback()
            return None


    def get_hire_checklists(
    self,
    long_claim_id: str,
    car_id: int,
    claimant_id: int
) -> list[dict]:
        """
        Get ALL hire checklists matching the given long_claim_id + car_id + claimant_id.
        Returns list of dictionaries (each = one checklist row), ordered by inspection_id.
        Returns empty list if no records found.
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
                    
    
    # Query method in your Queries class
    def delete_car(self, car_id: str) -> bool:
        try:
            query = "DELETE FROM cars WHERE id = %s"
            with self.conn.cursor() as cur:
                cur.execute(query, (car_id,))
            self.conn.commit()
            return cur.rowcount > 0  # Returns True if a row was deleted
        except Exception as e:
            self.conn.rollback()
            raise e