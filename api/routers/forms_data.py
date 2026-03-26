"""Form-data read routes (accident claims, pre-inspection, cancellation, storage, rental).

All routes are protected by the global JWT dependency set on the parent router.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List

from api.deps import get_db, get_current_user

router = APIRouter(tags=["forms"])


# ─────────────────────────────────────────────────────────────────────────────
# Accident Claims – GET
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/accident-claims/{claim_id}")
async def get_accident_claim(
    claim_id: str,
    queries=Depends(get_db),
) -> Dict[str, Any]:
    """Return the full accident claim form for the given ``claim_id``."""
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


# ─────────────────────────────────────────────────────────────────────────────
# Accident Claims – direction / JSON update (PUT)
# ─────────────────────────────────────────────────────────────────────────────

from fastapi import Request  # noqa: E402 – local import to keep grouping clear


@router.put("/accident-claims/{claim_id}/direction")
async def update_drawing_direction(
    claim_id: str,
    request: Request,
    queries=Depends(get_db),
) -> Dict[str, Any]:
    """Update the *before* or *after* direction drawing and its JSON data.

    Request body::

        {
            "type":      "before" | "after",
            "value":     "<drawing URL or string>",
            "json_data": { ... }   // optional
        }
    """
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    direction_type = data.get("type")
    value = data.get("value")
    json_data = data.get("json_data")

    if direction_type not in ["before", "after"]:
        raise HTTPException(status_code=400, detail="type must be 'before' or 'after'")
    if value is None:
        raise HTTPException(status_code=400, detail="value is required")

    value_column = (
        "direction_before_drawing" if direction_type == "before" else "direction_after_drawing"
    )
    json_column = "json_before" if direction_type == "before" else "json_after"

    queries.upsert_accident_claim_with_json(
        claim_id, value_column, value, json_column, json_data
    )

    return {
        "claim_id": claim_id,
        "updated_value_column": value_column,
        "value": value,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Pre-Inspection Forms
# ─────────────────────────────────────────────────────────────────────────────

def _format_pre_inspection(result: dict) -> dict:
    """Flatten a pre-inspection DB row into the API response shape."""
    response = {f"condition_{i}": result.get(f"condition_{i}", "") for i in range(1, 31)}
    response.update(
        {
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
        }
    )
    return response


@router.get("/pre-inspection-forms/{claim_id}")
async def get_pre_inspection_forms(
    claim_id: str,
    queries=Depends(get_db),
) -> List[Dict[str, Any]]:
    """Return all pre-inspection forms for ``claim_id`` (may be multiple rows)."""
    results = queries.get_pre_inspection_form(claim_id)
    return [_format_pre_inspection(r) for r in results]


@router.get("/pre-inspection-forms/inspection/{inspection_id}")
async def get_pre_inspection_form_by_inspection_id(
    inspection_id: str,
    queries=Depends(get_db),
) -> Dict[str, Any]:
    """Return a single pre-inspection form by its unique ``inspection_id``."""
    result = queries.get_pre_inspection_form_by_inspection(inspection_id)
    if not result:
        raise HTTPException(
            status_code=404,
            detail="Pre-inspection form not found for this inspection_id",
        )
    return _format_pre_inspection(result)


# ─────────────────────────────────────────────────────────────────────────────
# Cancellation Form – GET
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/cancellation-forms/{claim_id}")
async def get_cancellation_form(
    claim_id: str,
    queries=Depends(get_db),
) -> Dict[str, Any]:
    """Return the cancellation form for ``claim_id``."""
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


# ─────────────────────────────────────────────────────────────────────────────
# Storage Form – GET
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/storage-forms/{claim_id}")
async def get_storage_form(
    claim_id: str,
    queries=Depends(get_db),
) -> Dict[str, Any]:
    """Return the storage form / storage invoice for ``claim_id``."""
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
    }


# ─────────────────────────────────────────────────────────────────────────────
# Rental Agreement – GET
# ─────────────────────────────────────────────────────────────────────────────

def _format_rental_agreement(result: dict) -> dict:
    """Flatten a rental_agreements DB row into the API response shape."""
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
    }


@router.get("/rental-agreements/{claim_id}")
async def get_rental_agreement(
    claim_id: str,
    queries=Depends(get_db),
) -> Dict[str, Any]:
    """Return the rental agreement for ``claim_id``."""
    result = queries.get_rental_agreement(claim_id)
    if not result:
        raise HTTPException(status_code=404, detail="Rental agreement not found")
    return _format_rental_agreement(result)
