"""Invoice routes (short-claim invoices and long-hire invoices)."""

from fastapi import APIRouter, Depends
from typing import Any, List, Optional

from api.deps import get_db
from api.schemas import InvoiceCreate, InvoiceUpdate, LongHireInvoiceCreate

router = APIRouter(tags=["invoices"])


# ─────────────────────────────────────────────────────────────────────────────
# Short-claim invoices
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/invoice")
async def create_invoice(data: InvoiceCreate, queries=Depends(get_db)):
    """Create a new short-claim invoice."""
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


@router.put("/invoice/{invoice_id}")
async def update_invoice(invoice_id: int, data: InvoiceUpdate, queries=Depends(get_db)):
    """Update fields on an existing short-claim invoice."""
    updated_id = queries.update_invoice(
        invoice_id,
        data.info,
        data.storage_bill,
        data.rent_bill,
        data.user_name,
    )
    if updated_id == 0:
        return {"success": False, "message": "Nothing updated or invoice not found"}
    return {"success": True, "invoice_id": updated_id}


@router.get("/invoice")
async def get_all_invoices(queries=Depends(get_db)):
    """Return all short-claim invoices across all claims."""
    invoices = queries.get_all_invoices()
    return {"success": True, "count": len(invoices), "data": invoices}


@router.get("/invoice/{claim_id}")
async def get_invoices_by_claim(claim_id: str, queries=Depends(get_db)):
    """Return all invoices for a specific claim."""
    invoices = queries.get_invoices_by_claim_id(claim_id)
    return {"success": True, "count": len(invoices), "data": invoices}


# ─────────────────────────────────────────────────────────────────────────────
# Long-hire invoices
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/long_hire_invoice")
async def create_long_hire_invoice(data: LongHireInvoiceCreate, queries=Depends(get_db)):
    """Create a long-hire invoice and mark the long claim as invoiced."""
    invoice_id = queries.insert_long_hire_invoice(
        data.claim_id, data.amount, data.user_name
    )
    if invoice_id == 0:
        return {"success": False, "message": "Failed to create invoice"}
    return {"success": True, "invoice_id": invoice_id}


@router.get("/long_hire_invoice")
async def get_all_long_hire_invoices(queries=Depends(get_db)):
    """Return all long-hire invoices."""
    invoices = queries.get_all_long_hire_invoices()
    return {"success": True, "count": len(invoices), "data": invoices}
