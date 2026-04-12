"""
Invoice routes.

Routes:
    GET    /api/invoice
    POST   /api/invoice
    GET    /api/invoice/{claim_id}
    PUT    /api/invoice/{invoice_id}
    GET    /api/long_hire_invoice
    POST   /api/long_hire_invoice
    GET    /api/claim-bill/{claim_id}
"""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import status as http_status

from api.models.schemas import CurrentUser, InvoiceCreate, InvoiceUpdate, LongHireInvoiceCreate
from db.connection import DBConnection
from sql.combinedQueries import Queries
from utils.jwt_handler import decode_token

security = HTTPBearer(scheme_name="Bearer")


def _get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> CurrentUser:
    """Internal dependency to get the current user for this router."""
    token = credentials.credentials
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return CurrentUser(
        id=payload.get("sub"),
        username=payload.get("username", ""),
        role=payload.get("role", "user"),
        permissions=payload.get("permissions", {}),
    )


router = APIRouter(tags=["invoices"])


@router.get("/invoice")
async def get_all_invoices():
    """
    Retrieve all invoices joined with their parent claim name.

    Returns:
        Dict with ``success``, ``count``, and ``data``.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)
    invoices = queries.get_all_invoices()
    return {"success": True, "count": len(invoices), "data": invoices}


@router.post("/invoice")
async def create_invoice(data: InvoiceCreate):
    """
    Create a new short-hire invoice.

    If ``'Rental Agreement'`` is in ``docs`` the claim status is updated to
    ``"invoice sent"`` automatically.

    Args:
        data: Invoice creation payload.

    Returns:
        Dict with ``success`` and ``invoice_id``.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    invoice_id = queries.insert_invoice(
        data.claim_id,
        data.info,
        data.docs,
        data.storage_bill,
        data.rent_bill,
        data.user_name,
    )

    if invoice_id == 0:
        return {"success": False, "message": "Failed to create invoice"}

    return {"success": True, "invoice_id": invoice_id}


@router.get("/invoice/{claim_id}")
async def get_invoices(claim_id: str):
    """
    Retrieve all invoices for a given claim, newest first.

    Args:
        claim_id: The unique claim identifier.

    Returns:
        Dict with ``success``, ``count``, and ``data``.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)
    invoices = queries.get_invoices_by_claim_id(claim_id)
    return {"success": True, "count": len(invoices), "data": invoices}


@router.put("/invoice/{invoice_id}")
async def update_invoice(
    invoice_id: int,
    data: InvoiceUpdate,
    current_user: CurrentUser = Depends(_get_current_user),
):
    """
    Update fields on an existing invoice.

    When ``payment_date`` is newly set the parent claim is automatically closed.

    Args:
        invoice_id: The invoice to update.
        data: Fields to update.
        current_user: The authenticated user making the request.

    Returns:
        Dict with ``success`` and ``invoice_id``.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    updated_id = queries.update_invoice(
        invoice_id,
        data.info,
        data.storage_bill,
        data.rent_bill,
        data.user_name,
        data.payment_date,
        data.payment_amount,
        current_user.username,
    )

    if updated_id == 0:
        return {"success": False, "message": "Nothing updated or invoice not found"}

    return {"success": True, "invoice_id": updated_id}


# ---------------------------------------------------------------------------
# Long-hire invoices
# ---------------------------------------------------------------------------

@router.get("/long_hire_invoice")
async def get_all_long_hire_invoices():
    """
    Retrieve all long-hire invoices joined with hirer name.

    Returns:
        Dict with ``success``, ``count``, and ``data``.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)
    invoices = queries.get_all_long_hire_invoices()
    return {"success": True, "count": len(invoices), "data": invoices}


@router.post("/long_hire_invoice")
async def create_long_hire_invoice(data: LongHireInvoiceCreate):
    """
    Create a new long-hire invoice and mark the long claim as invoiced.

    Args:
        data: Long-hire invoice creation payload.

    Returns:
        Dict with ``success`` and ``invoice_id``.
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    invoice_id = queries.insert_long_hire_invoice(data.claim_id, data.amount, data.user_name)
    if invoice_id == 0:
        return {"success": False, "message": "Failed to create invoice"}

    return {"success": True, "invoice_id": invoice_id}


# ---------------------------------------------------------------------------
# Claim bill helper
# ---------------------------------------------------------------------------

@router.get("/claim-bill/{claim_id}")
async def get_claim_bill(claim_id: str) -> Dict[str, Any]:
    """
    Return the rental and storage totals for a claim (used for billing).

    Args:
        claim_id: The unique claim identifier.

    Returns:
        Dict with ``rental`` (float or ``None``) and ``storage`` (float or ``None``).
    """
    conn = DBConnection.get_connection()
    queries = Queries(conn)

    rental = queries.get_rental_by_claim(claim_id)
    storage = queries.get_storage_by_claim(claim_id)

    return {"rental": rental, "storage": storage}
