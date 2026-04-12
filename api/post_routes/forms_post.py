"""
Upsert routes for the five main claim forms (``/post`` prefix).

These endpoints are intentionally unauthenticated — they are called by the
front-end form submissions that are separate from the main authenticated API.

Routes:
    POST /post/accident-claims/{claim_id}
    PUT  /post/accident-claims/{claim_id}
    POST /post/pre-inspection-forms
    POST /post/cancellation-forms
    POST /post/storage-forms
    POST /post/rental-agreements
"""

from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request

from db.connection import DBConnection
from sql.combinedQueries import Queries

router = APIRouter(tags=["post-forms"])


@router.post("/accident-claims/{claim_id}")
@router.put("/accident-claims/{claim_id}")
async def upsert_accident_claim(
    claim_id: str,
    request: Request,
) -> Dict[str, Any]:
    """
    Create or update an accident claim (upsert).

    ``claim_id`` is also read from the request body; the path-parameter
    value is used as a fallback.  Only the fields present in the body are
    written.

    Returns:
        Flat dict of all accident-claim columns.

    Raises:
        HTTPException(400): For invalid JSON.
        HTTPException(500): When the upsert fails.
    """
    try:
        incoming_data: dict = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    claim_id = incoming_data.get("claim_id") or claim_id
    update_data = {k: v for k, v in incoming_data.items() if k != "claim_id"}

    conn = DBConnection.get_connection()
    queries = Queries(conn)

    result = queries.upsert_accident_claim(claim_id, update_data)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to save claim")

    return {
        "claim_id": result["claim_id"],
        "checklist_v.d": result.get("checklist_vd"),
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
    }


@router.post("/pre-inspection-forms")
async def upsert_pre_inspection_form(request: Request) -> Dict[str, Any]:
    """
    Create or update a pre-inspection form.

    ``claim_id`` is required in the body.  If ``inspection_id`` is also
    provided the existing row is updated; otherwise a new row is inserted.

    Returns:
        Flat dict of all pre-inspection form fields.

    Raises:
        HTTPException(400): For invalid JSON or missing ``claim_id``.
        HTTPException(500): When the upsert fails.
    """
    try:
        incoming_data: dict = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or missing JSON body")

    claim_id = incoming_data.get("claim_id")
    if not claim_id or not isinstance(claim_id, str) or not claim_id.strip():
        raise HTTPException(
            status_code=400,
            detail="claim_id is required and must be a non-empty string in the request body",
        )

    inspection_id = incoming_data.get("inspection_id")
    update_data = {k: v for k, v in incoming_data.items() if k not in ("claim_id", "inspection_id")}

    conn = DBConnection.get_connection()
    queries = Queries(conn)

    if inspection_id:
        result = queries.upsert_pre_inspection_form(claim_id, update_data, inspection_id=inspection_id)
    else:
        result = queries.upsert_pre_inspection_form(claim_id, update_data)

    if not result:
        raise HTTPException(status_code=500, detail="Failed to save pre-inspection form")

    response = {f"condition_{i}": result.get(f"condition_{i}", "") for i in range(1, 31)}
    response.update({
        "date": result.get("date", ""),
        "customer": result.get("customer", ""),
        "detailer": result.get("detailer", ""),
        "order_number": result.get("order_number", ""),
        "year": result.get("year", ""),
        "make": result.get("make", ""),
        "model": result.get("model", ""),
        "notes": result.get("notes", ""),
        "recommendations": result.get("recommendations", ""),
        "customer_signature": result.get("customer_signature"),
        "detailer_signature": result.get("detailer_signature"),
        "base_vehicle_image": result.get("base_vehicle_image"),
        "annotated_vehicle_image": result.get("annotated_vehicle_image"),
        "claim_id": result["claim_id"],
        "inspection_id": result["inspection_id"],
    })
    return response


@router.post("/cancellation-forms")
async def upsert_cancellation_form(request: Request) -> Dict[str, Any]:
    """
    Create or update a cancellation form.

    ``claim_id`` is required in the body.  Only fields present in the body are
    written.

    Returns:
        Flat dict of cancellation form fields.

    Raises:
        HTTPException(400): For invalid JSON or missing ``claim_id``.
        HTTPException(500): When the upsert fails.
    """
    try:
        incoming_data: dict = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or missing JSON body")

    claim_id = incoming_data.get("claim_id")
    if not claim_id or not isinstance(claim_id, str) or not claim_id.strip():
        raise HTTPException(
            status_code=400,
            detail="claim_id is required and must be a non-empty string in the request body",
        )

    update_data = {k: v for k, v in incoming_data.items() if k != "claim_id"}

    conn = DBConnection.get_connection()
    queries = Queries(conn)

    result = queries.upsert_cancellation_form(claim_id, update_data)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to save cancellation form")

    return {
        "name": result.get("name", ""),
        "address": result.get("address", ""),
        "postcode": result.get("postcode", ""),
        "email": result.get("email", ""),
        "cancellation_date": result.get("cancellation_date", ""),
        "cancellation_signature": result.get("cancellation_signature"),
        "claim_id": result["claim_id"],
    }


@router.post("/storage-forms")
async def upsert_storage_form(request: Request) -> Dict[str, Any]:
    """
    Create or update a storage form / storage invoice.

    ``claim_id`` is required in the body.  Only fields present in the body
    are written.

    Returns:
        Flat dict of storage form fields.

    Raises:
        HTTPException(400): For invalid JSON or missing ``claim_id``.
        HTTPException(500): When the upsert fails.
    """
    try:
        incoming_data: dict = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or missing JSON body")

    claim_id = incoming_data.get("claim_id")
    if not claim_id or not isinstance(claim_id, str) or not claim_id.strip():
        raise HTTPException(
            status_code=400,
            detail="claim_id is required and must be a non-empty string in the request body",
        )

    update_data = {k: v for k, v in incoming_data.items() if k != "claim_id"}

    conn = DBConnection.get_connection()
    queries = Queries(conn)

    result = queries.upsert_storage_form(claim_id, update_data)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to save storage form")

    return {
        "name": result.get("name", ""),
        "postcode": result.get("postcode", ""),
        "address1": result.get("address1", ""),
        "address2": result.get("address2", ""),
        "vehicle_make": result.get("vehicle_make", ""),
        "vehicle_model": result.get("vehicle_model", ""),
        "registration_number": result.get("registration_number", ""),
        "date_of_recovery": result.get("date_of_recovery", ""),
        "storage_start_date": result.get("storage_start_date", ""),
        "storage_end_date": result.get("storage_end_date", ""),
        "number_of_days": result.get("number_of_days"),
        "charges_per_day": result.get("charges_per_day"),
        "total_storage_charge": result.get("total_storage_charge"),
        "recovery_charge": result.get("recovery_charge"),
        "subtotal": result.get("subtotal"),
        "vat_amount": result.get("vat_amount"),
        "invoice_total": result.get("invoice_total"),
        "client_date": result.get("client_date", ""),
        "owner_date": result.get("owner_date", ""),
        "client_signature": result.get("client_signature"),
        "owner_signature": result.get("owner_signature"),
        "claim_id": result["claim_id"],
        "storage_location_key": result.get("storage_location_key", ""),
    }


@router.post("/rental-agreements")
async def upsert_rental_agreement(request: Request) -> Dict[str, Any]:
    """
    Create or update a rental agreement.

    ``claim_id`` is required in the body.  Saves hire dates, triggers
    fleet-history updates, updates car availability, and updates claim status.

    Returns:
        Flat dict of all rental agreement fields.

    Raises:
        HTTPException(400): For invalid JSON or missing ``claim_id``.
        HTTPException(500): When the upsert fails.
    """
    try:
        incoming_data: dict = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or missing JSON body")

    claim_id = incoming_data.get("claim_id")
    if not claim_id or not isinstance(claim_id, str) or not claim_id.strip():
        raise HTTPException(
            status_code=400,
            detail="claim_id is required and must be a non-empty string in the request body",
        )

    update_data = {k: v for k, v in incoming_data.items() if k != "claim_id"}

    conn = DBConnection.get_connection()
    queries = Queries(conn)

    result = queries.upsert_rental_agreement(claim_id, update_data)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to save rental agreement")

    return {
        "rental_agreement_id": result["rental_agreement_id"],
        "claim_id": result["claim_id"],
        "hirer_name": result.get("hirer_name", ""),
        "title": result.get("title", ""),
        "permanent_address": result.get("permanent_address", ""),
        "additional_driver_name": result.get("additional_driver_name", ""),
        "licence_no": result.get("licence_no", ""),
        "date_issued": result.get("date_issued", ""),
        "expiry_date": result.get("expiry_date", ""),
        "dob": result.get("dob", ""),
        "date_test_passed": result.get("date_test_passed", ""),
        "occupation": result.get("occupation", ""),
        "daily_rate": result.get("daily_rate"),
        "policy_excess": result.get("policy_excess"),
        "deposit": result.get("deposit"),
        "refuelling_charge": result.get("refuelling_charge"),
        "insurance_company": result.get("insurance_company", ""),
        "policy_no": result.get("policy_no", ""),
        "insurance_dates": result.get("insurance_dates", ""),
        "own_insurance_confirm": result.get("own_insurance_confirm", "No"),
        "insurance_date": result.get("insurance_date", ""),
        "insurance_time": result.get("insurance_time", ""),
        "motoring_offence_3yrs": result.get("motoring_offence_3yrs", ""),
        "disqualified_5yrs": result.get("disqualified_5yrs", ""),
        "accident_3yrs": result.get("accident_3yrs", ""),
        "insurance_declined_5yrs": result.get("insurance_declined_5yrs", ""),
        "dishonesty_conviction": result.get("dishonesty_conviction", ""),
        "medical_condition1": result.get("medical_condition1", ""),
        "medical_condition2": result.get("medical_condition2", ""),
        "medical_details": result.get("medical_details", ""),
        "additional_driver_auth": result.get("additional_driver_auth", ""),
        "hire_vehicle_reg": result.get("hire_vehicle_reg", ""),
        "hire_vehicle_make": result.get("hire_vehicle_make", ""),
        "hire_vehicle_model": result.get("hire_vehicle_model", ""),
        "hire_vehicle_group": result.get("hire_vehicle_group", ""),
        "hire_vehicle_date_out": result.get("hire_vehicle_date_out", ""),
        "hire_vehicle_date_in": result.get("hire_vehicle_date_in", ""),
        "hire_vehicle_fuel_out": result.get("hire_vehicle_fuel_out", ""),
        "hire_vehicle_fuel_in": result.get("hire_vehicle_fuel_in", ""),
        "change_vehicle_reg": result.get("change_vehicle_reg", ""),
        "change_vehicle_make": result.get("change_vehicle_make", ""),
        "change_vehicle_model": result.get("change_vehicle_model", ""),
        "change_vehicle_group": result.get("change_vehicle_group", ""),
        "change_vehicle_date_out": result.get("change_vehicle_date_out", ""),
        "change_vehicle_date_in": result.get("change_vehicle_date_in", ""),
        "change_vehicle_fuel_out": result.get("change_vehicle_fuel_out", ""),
        "change_vehicle_fuel_in": result.get("change_vehicle_fuel_in", ""),
        "admin_fee": result.get("admin_fee"),
        "delivery_charge": result.get("delivery_charge"),
        "cdw_per_day": result.get("cdw_per_day"),
        "days_out": result.get("days_out"),
        "days_in": result.get("days_in"),
        "total_days": result.get("total_days"),
        "rate_per_day": result.get("rate_per_day"),
        "refuelling_total": result.get("refuelling_total"),
        "subtotal": result.get("subtotal"),
        "vat": result.get("vat"),
        "total_cost": result.get("total_cost"),
        "declaration_date": result.get("declaration_date", ""),
        "liability_date": result.get("liability_date", ""),
        "hirer_signature_terms": result.get("hirer_signature_terms"),
        "company_signature": result.get("company_signature"),
        "hirer_signature_insurance": result.get("hirer_signature_insurance"),
        "declaration_signature": result.get("declaration_signature"),
        "liability_signature": result.get("liability_signature"),
    }
