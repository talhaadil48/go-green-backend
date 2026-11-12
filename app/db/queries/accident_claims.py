import asyncpg
from app.db.base import record_to_dict


UPDATABLE_COLUMNS = [
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
    "circumstance_drawing", "direction_before_drawing", "direction_after_drawing",
]


async def upsert_accident_claim(
    conn: asyncpg.Connection, claim_id: str, data: dict
) -> dict | None:
    fields_to_update = [col for col in UPDATABLE_COLUMNS if col in data]

    if not fields_to_update and claim_id not in data:
        return None

    # Build positional placeholders: $1 = claim_id, $2...$n = field values
    columns = ["claim_id"] + fields_to_update
    ph = ", ".join(f"${i+1}" for i in range(len(columns)))
    set_clause = ", ".join(f"{col} = EXCLUDED.{col}" for col in fields_to_update)

    query = f"""
        INSERT INTO accident_claims ({', '.join(columns)})
        VALUES ({ph})
        ON CONFLICT (claim_id) DO UPDATE SET {set_clause}
        RETURNING *;
    """

    values = [claim_id] + [data[k] for k in fields_to_update]

    try:
        row = await conn.fetchrow(query, *values)
        return record_to_dict(row)
    except Exception as e:
        print(f"Error in upsert_accident_claim: {e}")
        return None


async def get_accident_claim(conn: asyncpg.Connection, claim_id: str) -> dict | None:
    row = await conn.fetchrow("SELECT * FROM accident_claims WHERE claim_id = $1;", claim_id)
    return record_to_dict(row)


async def upsert_accident_claim_with_json(
    conn: asyncpg.Connection,
    claim_id: str,
    value_column: str,
    value: str,
    json_column: str,
    json_data: dict | None,
) -> dict | None:
    if value_column not in ("direction_before_drawing", "direction_after_drawing"):
        return None
    if json_column not in ("json_before", "json_after"):
        return None

    import json as _json
    json_str = _json.dumps(json_data) if json_data is not None else None

    query = f"""
        INSERT INTO accident_claims (claim_id, {value_column}, {json_column})
        VALUES ($1, $2, $3)
        ON CONFLICT (claim_id) DO UPDATE SET
            {value_column} = EXCLUDED.{value_column},
            {json_column} = EXCLUDED.{json_column}
        RETURNING *;
    """
    row = await conn.fetchrow(query, claim_id, value, json_str)
    return record_to_dict(row)
