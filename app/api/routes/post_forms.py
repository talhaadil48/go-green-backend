"""
Routes under /post prefix — no authentication required.
These routes allow clients to submit forms directly (accident claims, pre-inspection,
cancellation, storage, rental agreements, hire checklists, claim documents).
"""
from fastapi import APIRouter, HTTPException, Request
from typing import Any, Dict
from app.db.pool import get_pool
from app.db.queries import accident_claims as ac_q
from app.db.queries import inspection_forms as insp_q
from app.db.queries import cancellation_forms as cf_q
from app.db.queries import storage_forms as sf_q
from app.db.queries import hire_checklist as hc_q
from app.db.queries import claims as claims_q
from app.services.rental_agreements import upsert_rental_agreement as svc_upsert_rental

router = APIRouter()


@router.post("/accident-claims/{claim_id}")
@router.put("/accident-claims/{claim_id}")
async def upsert_accident_claim(claim_id: str, request: Request) -> Dict[str, Any]:
    try:
        incoming_data: dict = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # original code extracted claim_id from body, ignoring the path param
    claim_id = incoming_data.get("claim_id")
    update_data = {k: v for k, v in incoming_data.items() if k != "claim_id"}

    pool = get_pool()
    async with pool.acquire() as conn:
        result = await ac_q.upsert_accident_claim(conn, claim_id, update_data)

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
    try:
        incoming_data: dict = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or missing JSON body")

    claim_id = incoming_data.get("claim_id")
    if not claim_id or not isinstance(claim_id, str) or not claim_id.strip():
        raise HTTPException(status_code=400, detail="claim_id is required and must be a non-empty string in the request body")

    inspection_id = incoming_data.get("inspection_id")
    update_data = {k: v for k, v in incoming_data.items() if k not in ("claim_id", "inspection_id")}

    pool = get_pool()
    async with pool.acquire() as conn:
        result = await insp_q.upsert_pre_inspection_form(conn, claim_id, update_data, inspection_id)

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
    try:
        incoming_data: dict = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or missing JSON body")

    claim_id = incoming_data.get("claim_id")
    if not claim_id or not isinstance(claim_id, str) or not claim_id.strip():
        raise HTTPException(status_code=400, detail="claim_id is required and must be a non-empty string in the request body")

    update_data = {k: v for k, v in incoming_data.items() if k != "claim_id"}

    pool = get_pool()
    async with pool.acquire() as conn:
        result = await cf_q.upsert_cancellation_form(conn, claim_id, update_data)

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
    try:
        incoming_data: dict = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or missing JSON body")

    claim_id = incoming_data.get("claim_id")
    if not claim_id or not isinstance(claim_id, str) or not claim_id.strip():
        raise HTTPException(status_code=400, detail="claim_id is required and must be a non-empty string in the request body")

    update_data = {k: v for k, v in incoming_data.items() if k != "claim_id"}

    pool = get_pool()
    async with pool.acquire() as conn:
        result = await sf_q.upsert_storage_form(conn, claim_id, update_data)

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
    try:
        incoming_data: dict = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or missing JSON body")

    claim_id = incoming_data.get("claim_id")
    if not claim_id or not isinstance(claim_id, str) or not claim_id.strip():
        raise HTTPException(status_code=400, detail="claim_id is required and must be a non-empty string in the request body")

    update_data = {k: v for k, v in incoming_data.items() if k != "claim_id"}

    pool = get_pool()
    async with pool.acquire() as conn:
        result = await svc_upsert_rental(conn, claim_id, update_data)

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


@router.put("/claim-documents/{claim_id}")
async def upsert_claim_documents(claim_id: str, payload: Dict[str, Any]):
    documents = payload.get("documents")
    if not isinstance(documents, dict):
        raise HTTPException(status_code=400, detail="documents must be a JSON object")

    pool = get_pool()
    async with pool.acquire() as conn:
        await claims_q.upsert_claim_documents(conn, claim_id, documents)

    return {
        "message": "Documents saved successfully",
        "claim_id": claim_id,
        "documents": documents,
    }


@router.get("/claim-documents/{claim_id}")
async def get_claim_documents(claim_id: str) -> Dict[str, Any]:
    pool = get_pool()
    async with pool.acquire() as conn:
        result = await claims_q.get_claim_documents(conn, claim_id)

    if not result:
        raise HTTPException(status_code=404, detail="Documents not found")

    return {
        "claim_id": result["claim_id"],
        "documents": result.get("documents", {}),
    }


@router.get("/recently")
async def delete_recently_deleted_claims():
    pool = get_pool()
    async with pool.acquire() as conn:
        deleted_count = await claims_q.permanently_delete_recently_deleted_claims(conn)
    return {"success": True, "deleted_count": deleted_count}


@router.post("/hire-checklists")
async def upsert_hire_checklist(request: Request) -> Dict[str, Any]:
    try:
        incoming_data: dict = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or missing JSON body")

    long_claim_id = incoming_data.get("long_claim_id")
    car_id = incoming_data.get("car_id")
    claimant_id = incoming_data.get("claimant_id")

    if not long_claim_id or not isinstance(long_claim_id, str) or not long_claim_id.strip():
        raise HTTPException(status_code=400, detail="long_claim_id is required and must be a non-empty string")
    if car_id is None:
        raise HTTPException(status_code=400, detail="car_id is required")
    if claimant_id is None:
        raise HTTPException(status_code=400, detail="claimant_id is required")

    data = {k: v for k, v in incoming_data.items() if k not in ("long_claim_id", "car_id", "claimant_id")}

    pool = get_pool()
    async with pool.acquire() as conn:
        result = await hc_q.upsert_hire_checklist(conn, long_claim_id, int(car_id), int(claimant_id), data)

    if not result:
        raise HTTPException(status_code=500, detail="Failed to save hire checklist")
    return result
