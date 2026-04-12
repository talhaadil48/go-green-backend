"""
Accident-claim API routes.

GET  /api/accident-claims/{claim_id}           – fetch all fields
PUT  /api/accident-claims/{claim_id}/direction – update drawing direction column
"""

from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request

from db.connection import DBConnection
from sql.combinedQueries import Queries

router = APIRouter(tags=["accident-claims"])


@router.get("/accident-claims/{claim_id}")
async def get_accident_claim(claim_id: str) -> Dict[str, Any]:
    """
    Retrieve all fields for a single accident claim.

    Args:
        claim_id: The unique claim identifier.

    Returns:
        A flat dict of every accident-claim column.

    Raises:
        HTTPException(404): When the claim does not exist.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    result = queries.get_accident_claim(claim_id)
    if not result:
        raise HTTPException(status_code=404, detail="Accident claim not found")

    return {
        "claim_id": result["claim_id"],
        "checklist_v.d": result.get("checklist_vd"),
        "checklist_pi": result.get("checklist_pi"),
        "checklist_dvla": result.get("checklist_dvla"),
        "checklist_badge": result.get("checklist_badge"),
        "checklist_recovery": result.get("checklist_recovery"),
        "checklist_hire": result.get("checklist_hire"),
        "checklist_ni_no": result.get("checklist_ni_no"),
        "checklist_storage": result.get("checklist_storage"),
        "checklist_plate": result.get("checklist_plate"),
        "checklist_licence": result.get("checklist_licence"),
        "checklist_logbook": result.get("checklist_logbook"),
        "date_of_claim": result.get("date_of_claim", ""),
        "accident_date": result.get("accident_date", ""),
        "accident_time": result.get("accident_time", ""),
        "accident_location": result.get("accident_location", ""),
        "accident_description": result.get("accident_description", ""),
        "owner_full_name": result.get("owner_full_name", ""),
        "owner_email": result.get("owner_email", ""),
        "owner_telephone": result.get("owner_telephone", ""),
        "owner_address": result.get("owner_address", ""),
        "owner_postcode": result.get("owner_postcode", ""),
        "owner_dob": result.get("owner_dob", ""),
        "owner_ni_number": result.get("owner_ni_number", ""),
        "owner_occupation": result.get("owner_occupation", ""),
        "driver_full_name": result.get("driver_full_name", ""),
        "driver_email": result.get("driver_email", ""),
        "driver_telephone": result.get("driver_telephone", ""),
        "driver_address": result.get("driver_address", ""),
        "driver_postcode": result.get("driver_postcode", ""),
        "driver_dob": result.get("driver_dob", ""),
        "driver_ni_number": result.get("driver_ni_number", ""),
        "driver_occupation": result.get("driver_occupation", ""),
        "client_vehicle_make": result.get("client_vehicle_make", ""),
        "client_vehicle_model": result.get("client_vehicle_model", ""),
        "client_registration": result.get("client_registration", ""),
        "client_policy_no": result.get("client_policy_no", ""),
        "client_cover_type": result.get("client_cover_type", ""),
        "client_policy_holder": result.get("client_policy_holder", ""),
        "third_party_name": result.get("third_party_name", ""),
        "third_party_email": result.get("third_party_email", ""),
        "third_party_telephone": result.get("third_party_telephone", ""),
        "third_party_address": result.get("third_party_address", ""),
        "third_party_postcode": result.get("third_party_postcode", ""),
        "third_party_dob": result.get("third_party_dob", ""),
        "third_party_ni_number": result.get("third_party_ni_number", ""),
        "third_party_occupation": result.get("third_party_occupation", ""),
        "third_party_vehicle_make": result.get("third_party_vehicle_make", ""),
        "third_party_vehicle_model": result.get("third_party_vehicle_model", ""),
        "third_party_registration": result.get("third_party_registration", ""),
        "third_party_policy_no": result.get("third_party_policy_no", ""),
        "third_party_policy_holder": result.get("third_party_policy_holder", ""),
        "fault_opinion": result.get("fault_opinion", ""),
        "fault_reason": result.get("fault_reason", ""),
        "road_conditions": result.get("road_conditions", ""),
        "weather_conditions": result.get("weather_conditions", ""),
        "witness1_name": result.get("witness1_name", ""),
        "witness1_address": result.get("witness1_address", ""),
        "witness1_postcode": result.get("witness1_postcode", ""),
        "witness1_telephone": result.get("witness1_telephone", ""),
        "witness2_name": result.get("witness2_name", ""),
        "witness2_address": result.get("witness2_address", ""),
        "witness2_postcode": result.get("witness2_postcode", ""),
        "witness2_telephone": result.get("witness2_telephone", ""),
        "loss_of_earnings": result.get("loss_of_earnings"),
        "employer_details": result.get("employer_details", ""),
        "print_name": result.get("print_name", ""),
        "declaration_date": result.get("declaration_date", ""),
        "client_signature": result.get("client_signature"),
        "circumstance_drawing": result.get("circumstance_drawing"),
        "direction_before_drawing": result.get("direction_before_drawing"),
        "direction_after_drawing": result.get("direction_after_drawing"),
        "json_before": result.get("json_before"),
        "json_after": result.get("json_after"),
    }


@router.put("/accident-claims/{claim_id}/direction")
async def update_drawing_direction(
    claim_id: str,
    request: Request,
) -> Dict[str, Any]:
    """
    Update the directional drawing column and its paired JSON column for an
    accident claim.

    Expected body::

        {
            "type":      "before" | "after",
            "value":     "<string or URL>",
            "json_data": { ... }   // optional
        }

    Args:
        claim_id: The unique claim identifier (path parameter).
        request: Raw FastAPI request object used to read the JSON body.

    Returns:
        Dict confirming the updated column and value.

    Raises:
        HTTPException(400): For invalid JSON, unknown ``type``, or missing ``value``.
    """
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    direction_type = data.get("type")
    value = data.get("value")
    json_data = data.get("json_data")

    if direction_type not in ("before", "after"):
        raise HTTPException(status_code=400, detail="type must be 'before' or 'after'")
    if value is None:
        raise HTTPException(status_code=400, detail="value is required")

    value_column = (
        "direction_before_drawing" if direction_type == "before"
        else "direction_after_drawing"
    )
    json_column = "json_before" if direction_type == "before" else "json_after"

    conn = DBConnection.get_connection()
    queries = Queries(conn)
    queries.upsert_accident_claim_with_json(claim_id, value_column, value, json_column, json_data)

    return {
        "claim_id": claim_id,
        "updated_value_column": value_column,
        "value": value,
    }
