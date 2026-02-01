from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any
from sql.combinedQueries import Queries
from db.connection import DBConnection
router = APIRouter(prefix="/api", tags=["claims"])

@router.post("/accident-claims/{claim_id}")
@router.put("/accident-claims/{claim_id}")
async def upsert_accident_claim(
    claim_id: str,
    request: Request,
    # db = Depends(get_db_dependency)   ← replace with your actual db dependency
) -> Dict[str, Any]:
    """
    Create new accident claim or update existing one (partial update).
    Accepts any subset of fields.
    """
    try:
        incoming_data: dict = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

   
    claim_id = incoming_data.get("claim_id")
    # Remove claim_id from update data if present (it's already in path)
    update_data = {k: v for k, v in incoming_data.items() if k != "claim_id"}

    conn = DBConnection.get_connection()          # ← your connection logic
    queries = Queries(conn)
 
    result = queries.upsert_accident_claim(claim_id, update_data)

    if not result:
        raise HTTPException(status_code=500, detail="Failed to save claim")

    # Format response exactly like your example
    response = {
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

    return response



@router.post("/pre-inspection-forms")
async def upsert_pre_inspection_form(request: Request) -> Dict[str, Any]:
    """
    Create new pre-inspection form or update existing one.
    claim_id MUST be provided in the request body.
    Accepts partial updates (only sent fields are updated).
    """
    try:
        incoming_data: dict = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or missing JSON body")

    claim_id = incoming_data.get("claim_id")
    if not claim_id or not isinstance(claim_id, str) or not claim_id.strip():
        raise HTTPException(
            status_code=400,
            detail="claim_id is required and must be a non-empty string in the request body"
        )

    # Remove claim_id from the fields to update
    update_data = {k: v for k, v in incoming_data.items() if k != "claim_id"}

    conn = DBConnection.get_connection()
    queries = Queries(conn)

    result = queries.upsert_pre_inspection_form(claim_id, update_data)

    if not result:
        raise HTTPException(status_code=500, detail="Failed to save pre-inspection form")

    # Format response exactly matching your example structure
    response = {
        "condition_1": result.get("condition_1", ""),
        "condition_2": result.get("condition_2", ""),
        "condition_3": result.get("condition_3", ""),
        "condition_4": result.get("condition_4", ""),
        "condition_5": result.get("condition_5", ""),
        "condition_6": result.get("condition_6", ""),
        "condition_7": result.get("condition_7", ""),
        "condition_8": result.get("condition_8", ""),
        "condition_9": result.get("condition_9", ""),
        "condition_10": result.get("condition_10", ""),
        "condition_11": result.get("condition_11", ""),
        "condition_12": result.get("condition_12", ""),
        "condition_13": result.get("condition_13", ""),
        "condition_14": result.get("condition_14", ""),
        "condition_15": result.get("condition_15", ""),
        "condition_16": result.get("condition_16", ""),
        "condition_17": result.get("condition_17", ""),
        "condition_18": result.get("condition_18", ""),
        "condition_19": result.get("condition_19", ""),
        "condition_20": result.get("condition_20", ""),
        "condition_21": result.get("condition_21", ""),
        "condition_22": result.get("condition_22", ""),
        "condition_23": result.get("condition_23", ""),
        "condition_24": result.get("condition_24", ""),
        "condition_25": result.get("condition_25", ""),
        "condition_26": result.get("condition_26", ""),
        "condition_27": result.get("condition_27", ""),
        "condition_28": result.get("condition_28", ""),
        "condition_29": result.get("condition_29", ""),
        "condition_30": result.get("condition_30", ""),
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
    }

    return response



@router.post("/cancellation-forms")
async def upsert_cancellation_form(request: Request) -> Dict[str, Any]:
    """
    Create new cancellation form or update existing one.
    claim_id MUST be provided in the request body.
    Accepts partial updates (only sent fields are updated).
    """
    try:
        incoming_data: dict = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or missing JSON body")

    claim_id = incoming_data.get("claim_id")
    if not claim_id or not isinstance(claim_id, str) or not claim_id.strip():
        raise HTTPException(
            status_code=400,
            detail="claim_id is required and must be a non-empty string in the request body"
        )

    # Remove claim_id from update fields
    update_data = {k: v for k, v in incoming_data.items() if k != "claim_id"}

    conn = DBConnection.get_connection()
    queries = Queries(conn)

    result = queries.upsert_cancellation_form(claim_id, update_data)

    if not result:
        raise HTTPException(status_code=500, detail="Failed to save cancellation form")

    # Format response to match your typical pattern
    response = {
        "name": result.get("name", ""),
        "address": result.get("address", ""),
        "postcode": result.get("postcode", ""),
        "email": result.get("email", ""),
        "cancellation_date": result.get("cancellation_date", ""),
        "cancellation_signature": result.get("cancellation_signature"),
        "claim_id": result["claim_id"]
    }

    return response



@router.post("/storage-forms")
async def upsert_storage_form(request: Request) -> Dict[str, Any]:
    """
    Create new storage form / storage invoice or update existing one.
    claim_id MUST be provided in the request body.
    Accepts partial updates (only sent fields are updated).
    """
    try:
        incoming_data: dict = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or missing JSON body")
    

    claim_id = incoming_data.get("claim_id")
    if not claim_id or not isinstance(claim_id, str) or not claim_id.strip():
        raise HTTPException(
            status_code=400,
            detail="claim_id is required and must be a non-empty string in the request body"
        )

    # Remove claim_id from the update payload
    update_data = {k: v for k, v in incoming_data.items() if k != "claim_id"}

    conn = DBConnection.get_connection()
    queries = Queries(conn)

    result = queries.upsert_storage_form(claim_id, update_data)

    if not result:
        raise HTTPException(status_code=500, detail="Failed to save storage form")

    # Response format matching your example structure
    response = {
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
        "claim_id": result["claim_id"]
    }

    return response

@router.post("/rental-agreements")
async def upsert_rental_agreement(request: Request) -> Dict[str, Any]:
    """
    Create or update rental agreement.
    - claim_id is REQUIRED in the request body
    - Uses upsert logic based on claim_id (UNIQUE constraint)
    - Supports partial updates
    """
    try:
        incoming_data: dict = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or missing JSON body")

    claim_id = incoming_data.get("claim_id")
    if not claim_id or not isinstance(claim_id, str) or not claim_id.strip():
        raise HTTPException(
            status_code=400,
            detail="claim_id is required and must be a non-empty string in the request body"
        )

    # Remove claim_id from the fields we're updating
    update_data = {k: v for k, v in incoming_data.items() if k != "claim_id"}

    conn = DBConnection.get_connection()
    queries = Queries(conn)

    result = queries.upsert_rental_agreement(claim_id, update_data)

    if not result:
        raise HTTPException(status_code=500, detail="Failed to save rental agreement")

    # Format response – same style as your example
    response = {
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

    return response


@router.get("/accident-claims/{claim_id}")
async def get_accident_claim(claim_id: str) -> Dict[str, Any]:
    conn = DBConnection.get_connection()
    queries = Queries(conn)
    
    result = queries.get_accident_claim(claim_id)
    if not result:
        raise HTTPException(status_code=404, detail="Accident claim not found")
    
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
    }


# ────────────────────────────────────────────────
# 2. Pre-Inspection Form - GET
# ────────────────────────────────────────────────
@router.get("/pre-inspection-forms/{claim_id}")
async def get_pre_inspection_form(claim_id: str) -> Dict[str, Any]:
    conn = DBConnection.get_connection()
    queries = Queries(conn)
    
    result = queries.get_pre_inspection_form(claim_id)
    if not result:
        raise HTTPException(status_code=404, detail="Pre-inspection form not found")
    
    response = {}
    for i in range(1, 31):
        key = f"condition_{i}"
        response[key] = result.get(key, "")
    
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
    })
    return response


# ────────────────────────────────────────────────
# 3. Cancellation Form - GET
# ────────────────────────────────────────────────
@router.get("/cancellation-forms/{claim_id}")
async def get_cancellation_form(claim_id: str) -> Dict[str, Any]:
    conn = DBConnection.get_connection()
    queries = Queries(conn)
    
    result = queries.get_cancellation_form(claim_id)
    if not result:
        raise HTTPException(status_code=404, detail="Cancellation form not found")
    
    return {
        "name": result.get("name", ""),
        "address": result.get("address", ""),
        "postcode": result.get("postcode", ""),
        "email": result.get("email", ""),
        "cancellation_date": result.get("cancellation_date", ""),
        "cancellation_signature": result.get("cancellation_signature"),
        "claim_id": result["claim_id"]
    }


# ────────────────────────────────────────────────
# 4. Storage Form - GET
# ────────────────────────────────────────────────
@router.get("/storage-forms/{claim_id}")
async def get_storage_form(claim_id: str) -> Dict[str, Any]:
    conn = DBConnection.get_connection()
    queries = Queries(conn)
    
    result = queries.get_storage_form(claim_id)
    if not result:
        raise HTTPException(status_code=404, detail="Storage form not found")
    
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
        "claim_id": result["claim_id"]
    }


# ────────────────────────────────────────────────
# 5. Rental Agreement - GET
# ────────────────────────────────────────────────
@router.get("/rental-agreements/{claim_id}")
async def get_rental_agreement(claim_id: str) -> Dict[str, Any]:
    conn = DBConnection.get_connection()
    queries = Queries(conn)
    
    result = queries.get_rental_agreement(claim_id)
    if not result:
        raise HTTPException(status_code=404, detail="Rental agreement not found")
    
    response = {
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
    return response



@router.post("/claims")
async def create_claim(payload: Dict[str, Any]):
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    claimant_name = payload.get("claimant_name")
    claim_type = payload.get("claim_type")

    

    queries.insert_claim(
        claimant_name=claimant_name,
        claim_type=claim_type
    )

    return {
        "message": "Claim created successfully",
    }



@router.get("/claims")
async def get_all_claims() -> list[Dict[str, Any]]:
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    return queries.get_all_claims()


@router.get("/claims/{claim_id}")
async def get_claim(claim_id: str) -> Dict[str, Any]:
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    result = queries.get_claim_by_id(claim_id)
    if not result:
        raise HTTPException(status_code=404, detail="Claim not found")

    return result





@router.get("/claim-documents/{claim_id}", response_model=Dict[str, Any])
async def get_claim_documents(claim_id: str):
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    result = queries.get_claim_documents(claim_id)

    if not result:
        raise HTTPException(status_code=404, detail="Documents not found")

    return {
        "claim_id": result["claim_id"],
        "documents": result.get("documents", {})
    }


@router.put("/claim-documents/{claim_id}")
async def upsert_claim_documents(
    claim_id: str,
    payload: Dict[str, Any]
):
    documents = payload.get("documents")

    if not isinstance(documents, dict):
        raise HTTPException(status_code=400, detail="documents must be a JSON object")

    conn = DBConnection.get_connection()
    queries = Queries(conn)

    queries.upsert_claim_documents(claim_id, documents)

    return {
        "message": "Documents saved successfully",
        "claim_id": claim_id,
        "documents": documents
    }


@router.delete("/claim-documents/{claim_id}/{doc_name}")
async def delete_claim_document(claim_id: str, doc_name: str):
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    success = queries.delete_claim_document(claim_id, doc_name)

    if not success:
        raise HTTPException(status_code=404, detail="Document not found for this claim")

    return {
        "message": f"Document '{doc_name}' deleted successfully",
        "claim_id": claim_id
    }


