"""
Read-only form routes.

GET endpoints for the four main claim forms and the pre-inspection-form
single-record lookup.

Routes:
    GET /api/pre-inspection-forms/{claim_id}
    GET /api/pre-inspection-forms/inspection/{inspection_id}
    GET /api/cancellation-forms/{claim_id}
    GET /api/storage-forms/{claim_id}
    GET /api/rental-agreements/{claim_id}
"""

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from db.connection import DBConnection
from sql.combinedQueries import Queries

router = APIRouter(tags=["forms"])


@router.get("/pre-inspection-forms/{claim_id}")
async def get_pre_inspection_form(claim_id: str) -> List[Dict[str, Any]]:
    """
    Retrieve all pre-inspection forms for a given claim.

    Multiple inspections may exist for a single claim; they are returned
    in order of creation (``inspection_id`` ascending).

    Args:
        claim_id: The unique claim identifier.

    Returns:
        List of pre-inspection form dicts (may be empty if none exist).
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    results = queries.get_pre_inspection_form(claim_id)

    response_list = []
    for result in results:
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
        response_list.append(response)

    return response_list


@router.get("/pre-inspection-forms/inspection/{inspection_id}")
async def get_pre_inspection_form_by_inspection_id(
    inspection_id: str,
) -> Dict[str, Any]:
    """
    Retrieve a single pre-inspection form by its inspection ID.

    Args:
        inspection_id: The unique inspection row identifier.

    Returns:
        A flat dict of all pre-inspection form fields.

    Raises:
        HTTPException(404): When no form exists for *inspection_id*.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    result = queries.get_pre_inspection_form_by_inspection(inspection_id)
    if not result:
        raise HTTPException(
            status_code=404,
            detail="Pre-inspection form not found for this inspection_id",
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


@router.get("/cancellation-forms/{claim_id}")
async def get_cancellation_form(claim_id: str) -> Dict[str, Any]:
    """
    Retrieve the cancellation form for a given claim.

    Args:
        claim_id: The unique claim identifier.

    Returns:
        A flat dict of cancellation form fields.

    Raises:
        HTTPException(404): When no form exists for *claim_id*.
    """
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
        "claim_id": result["claim_id"],
    }


@router.get("/storage-forms/{claim_id}")
async def get_storage_form(claim_id: str) -> Dict[str, Any]:
    """
    Retrieve the storage form for a given claim.

    Args:
        claim_id: The unique claim identifier.

    Returns:
        A flat dict of storage form fields.

    Raises:
        HTTPException(404): When no form exists for *claim_id*.
    """
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
        "claim_id": result["claim_id"],
        "storage_location_key": result.get("storage_location_key", ""),
    }


@router.get("/rental-agreements/{claim_id}")
async def get_rental_agreement(claim_id: str) -> Dict[str, Any]:
    """
    Retrieve the rental agreement for a given claim.

    Args:
        claim_id: The unique claim identifier.

    Returns:
        A flat dict of all rental agreement fields.

    Raises:
        HTTPException(404): When no agreement exists for *claim_id*.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    result = queries.get_rental_agreement(claim_id)
    if not result:
        raise HTTPException(status_code=404, detail="Rental agreement not found")

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
        "change_vehicle_history": result.get("change_vehicle_history", ""),
        "hire_vehicle_miles_out": result.get("hire_vehicle_miles_out", ""),
        "hire_vehicle_miles_in": result.get("hire_vehicle_miles_in", ""),
    }
