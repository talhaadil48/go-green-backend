from fastapi import APIRouter, HTTPException, Request , Depends
from typing import Dict, Any
from sql.combinedQueries import Queries
from db.connection import DBConnection
from utils.hashing import hash_password
from psycopg2.errors import UniqueViolation
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from utils.jwt_handler import decode_token
from fastapi import status

security = HTTPBearer(
    scheme_name="Bearer",
    description="JWT Authorization header using the Bearer scheme"
)


class CurrentUser(BaseModel):
    id: str
    username: str
    role: str
    permissions: dict = {}
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> CurrentUser:
    """
    Dependency that:
    1. Extracts Bearer token
    2. Validates & decodes it
    3. Returns structured CurrentUser
    """
    token = credentials.credentials

    # ← REPLACE with your actual token validation logic
    payload = decode_token(token)          # your function

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return CurrentUser(
        id=payload.get("sub"),
        username=payload.get("username", ""),
        role=payload.get("role", "user"),
        permissions=payload.get("permissions", {}),
    )

router = APIRouter(
    prefix="/api",
    tags=["claims"],
    dependencies=[Depends(get_current_user)]          # ← ALL routes protected by default
)

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
# ─────────────────
@router.get("/pre-inspection-forms/{claim_id}")
async def get_pre_inspection_form(claim_id: str) -> list[Dict[str, Any]]:
    """
    Get ALL pre-inspection forms for given claim_id (multiple inspections)
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)
   
    results = queries.get_pre_inspection_form(claim_id)  # Changed to list
   
    response_list = []
    for result in results:
        response = {
            f"condition_{i}": result.get(f"condition_{i}", "") for i in range(1, 31)
        }
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
            "inspection_id": result["inspection_id"],  # NEW
        })
        response_list.append(response)
    
    return response_list  # Returns [] if none

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
         "new_licence_no": result.get("new_licence_no", ""),
        "new_date_issued": result.get("new_date_issued", ""),
        "new_expiry_date": result.get("new_expiry_date", ""),
        "new_dob": result.get("new_dob", ""),
        "new_date_test_passed": result.get("new_date_test_passed", ""),
        "new_occupation": result.get("new_occupation", ""),
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
    claim_id = payload.get("claim_id")  # optional

    try:
        queries.insert_claim(
            claimant_name=claimant_name,
            claim_type=claim_type,
            claim_id=claim_id
        )
    except UniqueViolation:
        conn.rollback()
        raise HTTPException(
            status_code=409,
            detail="claim_id already exists"
        )

    return {
        "message": "Claim created successfully",
        "claim_id": claim_id or "auto-generated"
    }

@router.delete("/claims/{claim_id}")
async def delete_claim(claim_id: str):
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    deleted = queries.delete_claim(claim_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Claim not found"
        )

    return {
        "message": "Claim deleted successfully",
        "claim_id": claim_id
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




@router.post("/register")
async def register_user(username: str, password: str, role: str):
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    hashed_password = hash_password(password)

    user = queries.create_user(username, hashed_password, role)

    if not user:
        raise HTTPException(status_code=400, detail="User already exists")

    return {
        "message": "User created successfully"
    }



@router.put("/claims/{claim_id}/soft-delete")
async def soft_delete_claim(claim_id: str):
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    deleted = queries.soft_delete_claim(claim_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Claim not found"
        )

    return {
        "message": "Claim soft deleted successfully",
        "claim_id": claim_id
    }


@router.put("/claims/{claim_id}/restore")
async def restore_claim(claim_id: str):
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    restored = queries.restore_claim(claim_id)

    if not restored:
        raise HTTPException(
            status_code=404,
            detail="Claim not found"
        )

    return {
        "message": "Claim restored successfully",
        "claim_id": claim_id
    }
    
    
@router.get("/recently")
async def recently_deleted_claims():
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    claims = queries.get_recently_deleted_claims()

    if not claims:  # optional: just for clarity
        return {"count": 0, "claims": []}

    return {
        "count": len(claims),
        "claims": claims
    }



@router.post("/claims/mark-invoice-sent/{claim_id}")
async def mark_invoice_sent(claim_id: str):
    conn = DBConnection.get_connection()
    queries = Queries(conn)
    updated_claim = queries.mark_invoice_sent(claim_id)
    if not updated_claim:
        return {"message": "Claim not found", "claim_id": claim_id}
    return {"message": "Invoice marked as Sent", "claim": updated_claim}


@router.get("/pre-inspection-forms/inspection/{inspection_id}")
async def get_pre_inspection_form_by_inspection_id(
    inspection_id: str
) -> Dict[str, Any]:
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    result = queries.get_pre_inspection_form_by_inspection(inspection_id)

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Pre-inspection form not found for this inspection_id"
        )

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
        "claim_id": result.get("claim_id"),
        "inspection_id": result.get("inspection_id"),
    })

    return response