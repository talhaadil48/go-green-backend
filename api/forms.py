from fastapi import APIRouter, HTTPException, Request , Depends
from typing import Dict, Any
from sql.combinedQueries import Queries
from db.connection import DBConnection
from utils.hashing import hash_password
from psycopg2.errors import UniqueViolation
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional,List
from utils.jwt_handler import decode_token
from fastapi import status



security = HTTPBearer(
    scheme_name="Bearer",
    description="JWT Authorization header using the Bearer scheme"
)
class DailyRateUpdate(BaseModel):
    car_id: int
    daily_rate: float


class InvoiceCreate(BaseModel):
    claim_id: str
    info: str
    docs: Optional[List[str]] = []
    storage_bill: Optional[float] = 0
    rent_bill: Optional[float] = 0
    user_name: str

class ChangePasswordRequest(BaseModel):
    username: str
    new_password: str

class RegisterUserRequest(BaseModel):
    username: str
    password: str
    role: str
class CurrentUser(BaseModel):
    id: str
    username: str
    role: str
    permissions: dict = {}
class LongClaimCreate(BaseModel):
    starting_date: Optional[str] = None
    ending_date: Optional[str] = None
    hirer_name : Optional[str] = None

class LongClaimUpdate(BaseModel):
    long_claim_id: str
    starting_date: Optional[str] = None
    ending_date: Optional[str] = None
    hirer_name: Optional[str] = None

class LongClaimCarAction(BaseModel):
    car_id: int

class CarCreate(BaseModel):
    model: Optional[str] = None
    name: Optional[str] = None
    reg_no: Optional[str] = None

class CarUpdate(BaseModel):
    model: Optional[str] = None
    name: Optional[str] = None
    reg_no: Optional[str] = None

class ClaimantCreate(BaseModel):
    claimant_id: Optional[str] = None
    ref_no: Optional[str] = None
    long_claim_id: str
    car_id: int
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    miles: Optional[float] = None
    name: Optional[str] = None
    location: Optional[str] = None
    delivery_charges: Optional[float] = 0

class ClaimantUpdate(BaseModel):
    claimant_id: Optional[str] = None
    ref_no: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    miles: Optional[float] = None
    name: Optional[str] = None
    location: Optional[str] = None
    delivery_charges: Optional[float] = None

class SoftDeleteClaimRequest(BaseModel):
    deleted_by: str

class CloseClaimRequest(BaseModel):
    closed_by: str

class LongHireInvoiceCreate(BaseModel):
    claim_id: str
    amount: float
    user_name: str


class InvoiceUpdate(BaseModel):
    info: str | None = None
    storage_bill: float | None = None
    rent_bill: float | None = None
    user_name: str | None = None



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
        "json_after": result.get("json_after")
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
    claim_type    = payload.get("claim_type")
    council       = payload.get("council")          # ← new required field
    claim_id      = payload.get("claim_id")         # optional

    if not all([claimant_name, claim_type]):
        raise HTTPException(
            status_code=400,
            detail="claimant_name, claim_type and council are required"
        )

    try:
        a = queries.insert_claim(
            claimant_name=claimant_name,
            claim_type=claim_type,
            council=council,                        # ← added
            claim_id=claim_id
        )
        
    except UniqueViolation:
        conn.rollback()
        raise HTTPException(
            status_code=409,
            detail="claim_id already exists"
        )
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

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
async def register_user(
    data: RegisterUserRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )

    conn = DBConnection.get_connection()
    queries = Queries(conn)

    hashed_password = hash_password(data.password)

    user = queries.create_user(
        data.username,
        hashed_password,
        data.role
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists",
        )

    return {"message": "User created successfully"}

@router.put("/change-password")
async def change_password(
    data: ChangePasswordRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )

    conn = DBConnection.get_connection()
    queries = Queries(conn)

    hashed_password = hash_password(data.new_password)

    success = queries.change_user_password(
        data.username,
        hashed_password
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return {"message": "Password updated successfully"}

    
@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: CurrentUser = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )

    conn = DBConnection.get_connection()
    queries = Queries(conn)

    deleted = queries.delete_user(user_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return {
        "message": "User deleted successfully"
    }
    
@router.put("/claims/{claim_id}/soft-delete")
async def soft_delete_claim(claim_id: str, request: SoftDeleteClaimRequest):
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    deleted = queries.soft_delete_claim(claim_id, request.deleted_by)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Claim not found"
        )

    return {
        "message": "Claim soft deleted successfully",
        "claim_id": claim_id,
        "deleted_by": request.deleted_by
    }



@router.put("/claims/{claim_id}/close")
async def close_claim(claim_id: str, request: CloseClaimRequest):
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    closed = queries.close_claim(claim_id, request.closed_by)

    if not closed:
        raise HTTPException(
            status_code=404,
            detail="Claim not found"
        )

    return {
        "message": "Claim closed successfully",
        "claim_id": claim_id,
        "closed_by": request.closed_by
    }



@router.put("/claims/{claim_id}/reopen")
async def reopen_claim(claim_id: str):
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    reopened = queries.reopen_claim(claim_id)

    if not reopened:
        raise HTTPException(
            status_code=404,
            detail="Claim not found"
        )

    return {
        "message": "Claim reopened successfully",
        "claim_id": claim_id
    }

@router.get("/users")
async def get_all_users(
    current_user: CurrentUser = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )

    conn = DBConnection.get_connection()
    queries = Queries(conn)

    users = queries.get_all_non_admin_users()

    return {
        "users": users
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



@router.post("/invoice")
async def create_invoice(data: InvoiceCreate):
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    invoice_id = queries.insert_invoice(
        data.claim_id,
        data.info,
        data.docs,
        data.storage_bill,
        data.rent_bill,
        data.user_name
    )

    if invoice_id == 0:
        return {"success": False, "message": "Failed to create invoice"}

    return {
        "success": True,
        "invoice_id": invoice_id
    }

@router.put("/invoice/{invoice_id}")
async def update_invoice(invoice_id: int, data: InvoiceUpdate):
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    updated_id = queries.update_invoice(
        invoice_id,
        data.info,
        data.storage_bill,
        data.rent_bill,
        data.user_name
    )

    if updated_id == 0:
        return {
            "success": False,
            "message": "Nothing updated or invoice not found"
        }

    return {
        "success": True,
        "invoice_id": updated_id
    }


@router.get("/invoice")
async def get_all_invoices():
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    invoices = queries.get_all_invoices()

    return {
        "success": True,
        "count": len(invoices),
        "data": invoices
    }


@router.get("/invoice/{claim_id}")
async def get_invoices(claim_id: str):
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    invoices = queries.get_invoices_by_claim_id(claim_id)

    return {
        "success": True,
        "count": len(invoices),
        "data": invoices
    }
    

@router.put("/claims/{claim_id}")
async def update_claimant_name(claim_id: str, payload: Dict[str, Any]):
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    new_name = payload.get("claimant_name")
    if not new_name:
        raise HTTPException(
            status_code=400,
            detail="claimant_name is required"
        )

    try:
        updated = queries.update_claimant_name(claim_id=claim_id, new_name=new_name)
        if not updated:
            raise HTTPException(
                status_code=404,
                detail=f"Claim with id {claim_id} not found"
            )
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    return {"message": "Claimant name updated successfully", "claim_id": claim_id}



@router.post("/car")
async def create_car(payload: CarCreate):
    conn = DBConnection.get_connection()
    queries = Queries(conn)
    try:
        queries.insert_car(
            payload.model,
            payload.name,
            payload.reg_no
        )
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "success": True,
        "message": "Car created successfully"
    }

@router.delete("/car/{car_id}")
async def delete_car(car_id: str):
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    deleted = queries.delete_car(car_id)
    if deleted:
        return {
            "success": True,
            "message": "Car deleted successfully"
        }
    else:
        return {
            "success": False,
            "message": f"No car found with id {car_id}"
        }

@router.put("/car/{car_id}")
async def update_car(car_id: int, payload: CarUpdate):
    conn = DBConnection.get_connection()
    queries = Queries(conn)
    try:
        updated = queries.update_car(
            car_id,
            payload.model,
            payload.name,
            payload.reg_no
        )
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    if not updated:
        raise HTTPException(status_code=404, detail="Car not found")

    return {
        "success": True,
        "message": "Car updated successfully"
    }


@router.get("/car/{car_id}")
async def get_car_by_id(car_id: int):
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    car = queries.get_car_by_id(car_id)
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")

    return {
        "success": True,
        "data": car
    }


@router.get("/cars")
async def get_all_cars():
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    cars = queries.get_all_cars()

    return {
        "success": True,
        "count": len(cars),
        "data": cars
    }



@router.get("/cars/free")
async def get_free_cars():
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    cars = queries.get_free_cars()

    return {
        "success": True,
        "count": len(cars),
        "data": cars
    }



@router.get("/cars/available")
async def get_available_cars():
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    cars = queries.get_available_cars()

    return {
        "success": True,
        "count": len(cars),
        "data": cars
    }


# ---------------------- LONG CLAIMS ----------------------
@router.post("/long-claim")
async def create_long_claim(payload: LongClaimCreate):
    conn = DBConnection.get_connection()
    queries = Queries(conn)
    if not payload.starting_date:
        payload.starting_date = None
    if not payload.ending_date:
        payload.ending_date = None

    long_claim_id = queries.insert_long_claim(
        payload.starting_date,
        payload.ending_date,
        payload.hirer_name
    )

    return {
        "success": True,
        "long_claim_id": long_claim_id
    }

@router.put("/long-claim")
async def update_long_claim(payload: LongClaimUpdate):
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    if not payload.starting_date:
        payload.starting_date = None
    if not payload.ending_date:
        payload.ending_date = None

    queries.update_long_claim(
        payload.long_claim_id,
        payload.starting_date,
        payload.ending_date,
        payload.hirer_name
    )

    return {
        "success": True,        
        "message": "Long claim updated successfully"
    }


@router.post("/long-claim/{long_claim_id}/add-car")
async def add_car_to_long_claim(long_claim_id: str, payload: LongClaimCarAction):
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    queries.add_car_to_long_claim(long_claim_id, payload.car_id)

    return {
        "success": True,
        "message": "Car added to long claim"
    }


@router.delete("/long-claim/{long_claim_id}/remove-car/{car_id}")
async def remove_car_from_long_claim(long_claim_id: str, car_id: int):
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    queries.remove_car_from_long_claim(long_claim_id, car_id)

    return {
        "success": True,
        "message": "Car removed from long claim"
    }

@router.get("/long-claims")
async def get_all_long_claims():
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    claims = queries.get_all_long_claims()

    return {
        "success": True,
        "count": len(claims),
        "data": claims
    }



# ---------------------- CLAIMANT ----------------------
@router.post("/claimant")
async def create_claimant(payload: ClaimantCreate):
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    try:
        claimant_id = queries.insert_claimant(
            payload.long_claim_id,
            payload.car_id,
            payload.start_date,
            payload.end_date,
            payload.miles,
            payload.name,
            payload.location,
            payload.delivery_charges or 0,
            payload.claimant_id,
            payload.ref_no
        )

        return {
            "success": True,
            "claimant_id": claimant_id
        }

    except ValueError as e:
        return HTTPException(
            status_code=400,
            detail=str(e)
        )





@router.put("/claimant/{claimant_id}")
async def update_claimant(claimant_id: int, payload: ClaimantUpdate):
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    try:
        queries.update_claimant(
            claimant_id,
            new_claimant_id=payload.claimant_id,
            ref_no=payload.ref_no,
            start_date=payload.start_date,
            end_date=payload.end_date,
            miles=payload.miles,
            name=payload.name,
            location=payload.location,
            delivery_charges=payload.delivery_charges
        )

        return {
            "success": True,
            "message": "Claimant updated successfully"
        }

    except ValueError as e:
        return HTTPException(
            status_code=400,
            detail=str(e)
        )

@router.delete("/claimant/{claimant_id}")
async def delete_claimant(claimant_id: int):
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    deleted = queries.delete_claimant(claimant_id)
    if deleted:
        return {"success": True, "message": "Claimant deleted successfully"}
    else:
        return {"success": False, "message": "Claimant not found"}


@router.get("/claimant/{claimant_id}")
async def get_claimant_by_id(claimant_id: int):
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    data = queries.get_claimant(claimant_id=claimant_id)

    return {
        "success": True,
        "count": len(data),
        "data": data
    }


@router.get("/claimants")
async def get_all_claimants():
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    data = queries.get_all_claimants()

    return {
        "success": True,
        "count": len(data),
        "data": data
    }

# ---------------------- HIRE CHECKLIST ----------------------



@router.get("/long-claim/{long_claim_id}/cars")
async def get_cars_for_long_claim(long_claim_id: str):
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    data = queries.get_cars_by_long_claim(long_claim_id)

    return {
        "success": True,
        "count": len(data),
        "data": data
    }

@router.get("/car/{car_id}/claimants/{claim_id}")
async def get_claimants_for_car(car_id: int, claim_id: str):
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    data = queries.get_claimants_by_car(car_id, claim_id)

    return {
        "success": True,
        "count": len(data),
        "data": data
    }

@router.get("/long-hire/{long_claim_id}/claimants")
async def get_claimants_for_claim(long_claim_id: str):
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    data = queries.get_claimants_for_claim(long_claim_id)

    # Optionally, group claimants by car_id for easier frontend use
    claimants_by_car = {}
    for claimant in data:
        car_id = claimant['car_id']
        if car_id not in claimants_by_car:
            claimants_by_car[car_id] = []
        claimants_by_car[car_id].append(claimant)

    return {
        "success": True,
        "count": len(data),
        "data": claimants_by_car
    }

@router.get("/long-claims/{claim_id}")
async def get_long_claim_by_id(claim_id: str):
    conn = DBConnection.get_connection()
    queries = Queries(conn)
    claim = queries.get_long_claim_by_id(claim_id)
    if not claim:
        return {
            "success": False,
            "message": f"Long claim with id {claim_id} not found"
        }

    return {
        "success": True,
        "data": claim
    }


@router.put("/long-claim/{long_claim_id}/mark-invoice")
async def mark_invoice(long_claim_id: str):
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    updated = queries.mark_invoice(long_claim_id)
    if updated:
        return {"success": True, "message": "Invoice marked as true"}
    else:
        return {"success": False, "message": "Long claim not found"}
    


@router.put("/long-claims/{claim_id}/restore")
async def restore_claim(claim_id: str):
    conn = DBConnection.get_connection()
    queries = Queries(conn)
    restored = queries.restore_claim(claim_id)
    if restored == 0:
        return {"success": False, "message": "Claim not found"}
    return {"success": True, "message": f"Claim {claim_id} restored successfully."}


@router.delete("/long-claims/{claim_id}/delete")
async def delete_long_claim(claim_id: str):
    conn = DBConnection.get_connection()
    queries = Queries(conn)
    deleted = queries.delete_long_claim(claim_id)
    if deleted == 0:
        return {"success": False, "message": "Claim not found"}
    return {"success": True, "message": f"Claim {claim_id} deleted permanently."}

@router.patch("/long-claims/{claim_id}/mark-deleted")
async def mark_recently_deleted(claim_id: str, payload: Dict[str, str]):
    deleted_by = payload.get("deleted_by")
    if not deleted_by:
        raise HTTPException(status_code=400, detail="deleted_by is required")

    conn = DBConnection.get_connection()
    queries = Queries(conn)
    
    try:
        updated = queries.mark_as_recently_deleted(claim_id, deleted_by)
        if updated == 0:
            raise HTTPException(status_code=404, detail="Claim not found")
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    
    return {"success": True, "message": f"Claim {claim_id} marked as recently deleted by {deleted_by}."}


@router.get("/long/soft-deleted")
async def get_soft_deleted_long_claims():
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    claims = queries.get_soft_deleted_long_claims()

    return {
        "success": True,
        "count": len(claims),
        "data": claims
    }


@router.get("/hire-checklists/{long_claim_id}/{car_id}/{claimant_id}")
async def get_hire_checklists(
    long_claim_id: str,
    car_id: int,
    claimant_id: int
) -> List[Dict[str, Any]]:
    """
    Get ALL hire checklists for the given claim + car + claimant combination.
    
    Path parameters:
      - long_claim_id : str
      - car_id        : int
      - claimant_id   : int
    
    Returns:
      - list of checklists (each as dict)
      - empty list [] if no checklists exist
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    results = queries.get_hire_checklists(
        long_claim_id=long_claim_id,
        car_id=car_id,
        claimant_id=claimant_id
    )

    response_list = []

    for result in results:
        item = {
            # All 30 condition fields
            **{f"condition_{i}": result.get(f"condition_{i}", "") for i in range(1, 31)},
            # Main metadata fields
            "date": result.get("date", ""),
            "customer": result.get("customer", ""),
            "detailer": result.get("detailer", ""),
            "order_number": result.get("order_number", ""),
            "year": result.get("year", ""),
            "make": result.get("make", ""),
            "model": result.get("model", ""),
            "notes": result.get("notes", ""),
            "recommendations": result.get("recommendations", ""),
            # Signatures & images (allow None / null)
            "customer_signature": result.get("customer_signature"),
            "detailer_signature": result.get("detailer_signature"),
            "base_vehicle_image": result.get("base_vehicle_image"),
            "annotated_vehicle_image": result.get("annotated_vehicle_image"),
            # Identifying keys
            "long_claim_id": result["long_claim_id"],
            "car_id": result["car_id"],
            "claimant_id": result["claimant_id"],
            "inspection_id": result["inspection_id"],
        }
        response_list.append(item)

    return response_list


@router.put("/claims/{claim_id}/restore")
async def restore_claim(claim_id: str):
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    restored = queries.restore_short_claim(claim_id)

    if not restored:
        raise HTTPException(
            status_code=409,
            detail="Claim not found"
        )

    return {
        "message": "Claim restored successfully",
        "claim_id": claim_id
    }



@router.put("/claims/{claim_id}/status")
async def update_claim_status_api(claim_id: str, payload: Dict[str, str]):
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    status = payload.get("status")
    if not status:
        raise HTTPException(status_code=400, detail="status is required")

    try:
        updated = queries.update_claim_status(claim_id, status)
        if not updated:
            raise HTTPException(status_code=404, detail="claim_id not found")
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    return {"message": "Status updated successfully", "claim_id": claim_id, "status": status}



@router.get("/claim-bill/{claim_id}")
async def get_claim_bill(claim_id: str) -> Dict[str, Any]:
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    rental = queries.get_rental_by_claim(claim_id)
    storage = queries.get_storage_by_claim(claim_id)

    return {
        "rental": rental,
        "storage": storage
    }

@router.post("/long_hire_invoice")
async def create_long_hire_invoice(data: LongHireInvoiceCreate):
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    invoice_id = queries.insert_long_hire_invoice(
        data.claim_id,
        data.amount,
        data.user_name
    )

    if invoice_id == 0:
        return {"success": False, "message": "Failed to create invoice"}

    return {"success": True, "invoice_id": invoice_id}
@router.get("/long_hire_invoice")
async def get_all_long_hire_invoices():
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    invoices = queries.get_all_long_hire_invoices()

    return {
        "success": True,
        "count": len(invoices),
        "data": invoices
    }



@router.get("/long-claim/{long_claim_id}/daily-rates")
async def get_daily_rates(long_claim_id: str):
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    data = queries.get_daily_rates_for_claim(long_claim_id)

    # convert list to dict {car_id: daily_rate} for easier use in frontend
    rates = {item['car_id']: item['daily_rate'] or 0 for item in data}

    return {
        "success": True,
        "data": rates
    }


@router.put("/long-claim/{long_claim_id}/daily-rate")
async def update_daily_rate(long_claim_id: str, body: DailyRateUpdate):
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    updated = queries.update_daily_rate(
        long_claim_id,
        body.car_id,
        body.daily_rate
    )

    return {
        "success": updated
    }



@router.put("/accident-claims/{claim_id}/direction")
async def update_drawing_direction(
    claim_id: str,
    request: Request
) -> Dict[str, Any]:
    """
    Update value and JSON column for an accident claim.
    Body:
    {
        "type": "before" | "after",
        "value": "link or string value",
        "json_data": { ... }  # optional JSON object
    }
    """
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    direction_type = data.get("type")
    value = data.get("value")
    json_data = data.get("json_data")  # optional JSON

    if direction_type not in ["before", "after"]:
        raise HTTPException(status_code=400, detail="type must be 'before' or 'after'")
    if value is None:
        raise HTTPException(status_code=400, detail="value is required")

    value_column = "direction_before_drawing" if direction_type == "before" else "direction_after_drawing"
    json_column = "json_before" if direction_type == "before" else "json_after"

    conn = DBConnection.get_connection()
    queries = Queries(conn)
    result = queries.upsert_accident_claim_with_json(
        claim_id, value_column, value, json_column, json_data
    )

    return {
        "claim_id": claim_id,
        "updated_value_column": value_column,
        "value": value,
            }


@router.put("/cars/{car_id}/long")
async def update_long_hire(
    car_id: int,
    request: Request
) -> Dict[str, Any]:

    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    value = data.get("value")

    if value not in [True, False]:
        raise HTTPException(status_code=400, detail="value must be true or false")

    conn = DBConnection.get_connection()
    queries = Queries(conn)

    result = queries.update_is_long_hire(car_id, value)

    if not result:
        raise HTTPException(status_code=404, detail="Car not found")

    return {
        "car_id": car_id,
        "is_long_hire": value
    }


@router.put("/cars/availability/{reg_no}")
async def update_availability(
    reg_no: str,
    request: Request
) -> Dict[str, Any]:

    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    value = data.get("value")

    if value not in [True, False]:
        raise HTTPException(status_code=400, detail="value must be true or false")

    conn = DBConnection.get_connection()
    queries = Queries(conn)

    result = queries.update_is_available(reg_no, value)

    if not result:
        raise HTTPException(status_code=404, detail="Car not found")

    return {
        "reg_no": reg_no,
        "is_available": value
    }