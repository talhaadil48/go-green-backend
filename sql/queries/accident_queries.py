"""
Accident-claim query methods.

All database operations related to the ``accident_claims`` table live here.
"""

from psycopg2.extras import RealDictCursor
from .base import ClaimFormBase


class AccidentClaimQueries(ClaimFormBase):
    """Mixin class that provides accident-claim read/write queries."""

    # ------------------------------------------------------------------
    # Write helpers
    # ------------------------------------------------------------------

    def upsert_accident_claim(self, claim_id: str, data: dict) -> dict | None:
        """
        Insert or update an accident claim (upsert).

        Only columns present in *data* are written; any other updatable
        column keeps its existing value.

        Args:
            claim_id: The unique claim identifier.
            data: A flat dict whose keys are accident_claims column names.

        Returns:
            The saved row as a dict, or ``None`` on failure.
        """
        updatable_columns = [
            "checklist_vd", "checklist_pi", "checklist_dvla", "checklist_badge",
            "checklist_recovery", "checklist_hire", "checklist_ni_no",
            "checklist_storage", "checklist_plate", "checklist_licence",
            "checklist_logbook",
            "date_of_claim", "accident_date", "accident_time",
            "accident_location", "accident_description",
            "owner_full_name", "owner_email", "owner_telephone",
            "owner_address", "owner_postcode", "owner_dob",
            "owner_ni_number", "owner_occupation",
            "driver_full_name", "driver_email", "driver_telephone",
            "driver_address", "driver_postcode", "driver_dob",
            "driver_ni_number", "driver_occupation",
            "client_vehicle_make", "client_vehicle_model",
            "client_registration", "client_policy_no",
            "client_cover_type", "client_policy_holder",
            "third_party_name", "third_party_email", "third_party_telephone",
            "third_party_address", "third_party_postcode", "third_party_dob",
            "third_party_ni_number", "third_party_occupation",
            "third_party_vehicle_make", "third_party_vehicle_model",
            "third_party_registration", "third_party_policy_no",
            "third_party_policy_holder",
            "fault_opinion", "fault_reason",
            "road_conditions", "weather_conditions",
            "witness1_name", "witness1_address", "witness1_postcode",
            "witness1_telephone",
            "witness2_name", "witness2_address", "witness2_postcode",
            "witness2_telephone",
            "loss_of_earnings", "employer_details",
            "print_name", "declaration_date", "client_signature",
            "circumstance_drawing",
            "direction_before_drawing", "direction_after_drawing",
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

    def upsert_accident_claim_with_json(
        self,
        claim_id: str,
        value_column: str,
        value: str,
        json_column: str,
        json_data: dict | None,
    ) -> dict | None:
        """
        Upsert a drawing column and its paired JSON column on an accident claim.

        Only ``direction_before_drawing`` / ``direction_after_drawing`` and
        ``json_before`` / ``json_after`` are accepted.

        Args:
            claim_id: The unique claim identifier.
            value_column: One of ``direction_before_drawing`` or
                ``direction_after_drawing``.
            value: The string/URL value to store in *value_column*.
            json_column: One of ``json_before`` or ``json_after``.
            json_data: Optional JSON-serialisable dict to store.

        Returns:
            The updated row as a dict, or ``None`` if the column names are invalid.
        """
        if value_column not in ("direction_before_drawing", "direction_after_drawing"):
            return None
        if json_column not in ("json_before", "json_after"):
            return None

        query = f"""
            INSERT INTO accident_claims (claim_id, {value_column}, {json_column})
            VALUES (%s, %s, %s)
            ON CONFLICT (claim_id)
            DO UPDATE SET
                {value_column} = EXCLUDED.{value_column},
                {json_column}  = EXCLUDED.{json_column}
            RETURNING *;
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (claim_id, value, json_data))
            self.conn.commit()
            return cur.fetchone()

    # ------------------------------------------------------------------
    # Read helpers
    # ------------------------------------------------------------------

    def get_accident_claim(self, claim_id: str) -> dict | None:
        """
        Retrieve a single accident claim by its ID.

        Args:
            claim_id: The unique claim identifier.

        Returns:
            The row as a dict, or ``None`` if not found.
        """
        query = "SELECT * FROM accident_claims WHERE claim_id = %s;"
        with self.conn.cursor() as cur:
            cur.execute(query, (claim_id,))
            row = cur.fetchone()
            if row:
                columns = [desc[0] for desc in cur.description]
                return dict(zip(columns, row))
        return None
