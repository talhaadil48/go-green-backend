from fastapi import APIRouter, HTTPException, Request , Depends , Body
from typing import Dict, Any
from sql.combinedQueries import Queries
from db.connection import DBConnection
from utils.hashing import hash_password
from psycopg2.errors import UniqueViolation
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from utils.jwt_handler import decode_token
from fastapi import status


router = APIRouter(prefix="/post", tags=["post-claims"])
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
    claim_id ALWAYS required. inspection_id optional.
    If inspection_id given → update that row (404 if not exist)
    If no inspection_id → create new row
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
    
    inspection_id = incoming_data.get("inspection_id")
    # Remove claim_id and inspection_id from the fields to update
    update_data = {k: v for k, v in incoming_data.items() if k not in ("claim_id", "inspection_id")}
    
    conn = DBConnection.get_connection()
    queries = Queries(conn)
    
    if inspection_id:
        # UPDATE existing by inspection_id + claim_id
        result = queries.upsert_pre_inspection_form(claim_id, update_data, inspection_id=inspection_id)
    else:
        # INSERT new (no inspection_id filter)
        result = queries.upsert_pre_inspection_form(claim_id, update_data)
    
    if not result:
        raise HTTPException(status_code=500, detail="Failed to save pre-inspection form")
    
    # Format response exactly matching your example structure + inspection_id
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
        "inspection_id": result["inspection_id"],  # NEW
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
        "claim_id": result["claim_id"],
        "storage_location_key": result.get("storage_location_key", "")
    }

    return response

@router.post("/rental-agreements")
async def upsert_rental_agreement(request: Request) -> Dict[str, Any]:
    """
    Create or update rental agreement.
    
    - claim_id is REQUIRED in the request body
    - rental_agreement_id is OPTIONAL - if provided, updates that specific agreement
    - If no rental_agreement_id provided, creates a new agreement for the claim_id
    - Supports partial updates when rental_agreement_id is provided
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

    # Get rental_agreement_id if provided (optional)
    rental_agreement_id = incoming_data.get("rental_agreement_id")
    
    # Remove claim_id and rental_agreement_id from the fields we're updating
    update_data = {k: v for k, v in incoming_data.items() if k not in ["claim_id", "rental_agreement_id"]}

    conn = DBConnection.get_connection()
    queries = Queries(conn)

    try:
        result = queries.upsert_rental_agreement(claim_id, update_data, rental_agreement_id)
        
    except ValueError as e:
        # Business logic error (vehicle not available, etc.)
        print("Business logic error:", e)
        raise HTTPException(
            status_code=409,  # conflict (better than 400 here)
            detail=str(e)
        )
    except Exception as e:
        # Unexpected server error
        print("Unexpected error:", e)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

    if not result:
        raise HTTPException(status_code=500, detail="Failed to save rental agreement")

    # Return minimal response with just the IDs
    return {
        "rental_agreement_id": result["rental_agreement_id"],
        "claim_id": result["claim_id"],
        "message": "Rental agreement saved successfully"
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



@router.get("/recently")
async def delete_recently_deleted_claims():
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    deleted_count = queries.permanently_delete_recently_deleted_claims()

    return {
        "success": True,
        "deleted_count": deleted_count
    }




@router.post("/hire-checklists")
async def upsert_hire_checklist(request: Request) -> Dict[str, Any]:
    """
    Create new hire checklist or update existing one.

    Required in body:
      - long_claim_id: str
      - car_id:       int
      - claimant_id:  int

    Optional:
      - inspection_id: str/int   → if provided → update that existing row

    Accepts partial updates (only fields sent in the body are updated).
    """
    try:
        incoming_data: dict = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or missing JSON body")

    # ─── Required composite keys ─────────────────────────────────────
    long_claim_id = incoming_data.get("long_claim_id")
    car_id        = incoming_data.get("car_id")
    claimant_id   = incoming_data.get("claimant_id")

    if not long_claim_id or not isinstance(long_claim_id, str) or not long_claim_id.strip():
        raise HTTPException(
            status_code=400,
            detail="long_claim_id is required and must be a non-empty string"
        )
    if not isinstance(car_id, int):
        raise HTTPException(status_code=400, detail="car_id must be an integer")
    if not isinstance(claimant_id, int):
        raise HTTPException(status_code=400, detail="claimant_id must be an integer")


    # Remove identifier fields from update payload
    update_data = {
        k: v for k, v in incoming_data.items()
        if k not in ("long_claim_id", "car_id", "claimant_id", "inspection_id")
    }

    conn = DBConnection.get_connection()   # ← your connection factory
    queries = Queries(conn)

    
    result = queries.upsert_hire_checklist(
        long_claim_id=long_claim_id,
        car_id=car_id,
        claimant_id=claimant_id,
        data=update_data
    )

    if not result:
        raise HTTPException(status_code=500, detail="Failed to save hire checklist")

    # ─── Response  includes all columns that exist in your table ─────
    response = {
        "inspection_id":           result["inspection_id"],
        "long_claim_id":           result["long_claim_id"],
        "car_id":                  result["car_id"],
        "claimant_id":             result["claimant_id"],

        "condition_1":  result.get("condition_1",  ""),
        "condition_2":  result.get("condition_2",  ""),
        "condition_3":  result.get("condition_3",  ""),
        "condition_4":  result.get("condition_4",  ""),
        "condition_5":  result.get("condition_5",  ""),
        "condition_6":  result.get("condition_6",  ""),
        "condition_7":  result.get("condition_7",  ""),
        "condition_8":  result.get("condition_8",  ""),
        "condition_9":  result.get("condition_9",  ""),
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

        "date":                    result.get("date", ""),
        "customer":                result.get("customer", ""),
        "detailer":                result.get("detailer", ""),
        "order_number":            result.get("order_number", ""),
        "year":                    result.get("year", ""),
        "make":                    result.get("make", ""),
        "model":                   result.get("model", ""),
        "notes":                   result.get("notes", ""),
        "recommendations":         result.get("recommendations", ""),
        "customer_signature":      result.get("customer_signature", None),
        "detailer_signature":      result.get("detailer_signature", None),
        "base_vehicle_image":      result.get("base_vehicle_image", None),
        "annotated_vehicle_image": result.get("annotated_vehicle_image", None),
    }

    return response




@router.post("/claims/{claim_id}/unlock")
async def unlock_claim(claim_id: str, request: Request):
    data = await request.json()
    locked = data.get("locked", False)
    print(f"LOCKED CHANGE TO FALSE for {claim_id}")
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    queries.update_claim_lock(
        claim_id=claim_id,
        locked=locked,
        locked_by=None
    )

    return {"status": "ok"}




@router.get("/cars/service-due")
async def get_cars_due_for_service(threshold: int = 8000):
    conn = DBConnection.get_connection()
    
    try:
        queries = Queries(conn)
        due_cars = queries.get_cars_due_for_service(threshold)

        return {
            "success": True,
            "threshold": threshold,
            "count": len(due_cars),
            "data": due_cars
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }



@router.post("/notifications/broadcast-followups")
async def broadcast_due_followups():
    """
    Broadcast all follow-ups due today. Run this once daily via cron job.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)
    try:
        result = queries.broadcast_due_followups(sender_id=23)
        return result
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()