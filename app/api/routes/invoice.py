from fastapi import APIRouter, HTTPException
from app.db.pool import get_pool
from app.db.queries import invoice as inv_q
from app.models.schemas import InvoiceCreate, InvoiceUpdate, LongHireInvoiceCreate
from app.services.invoice import create_invoice, update_invoice as svc_update_invoice, create_long_hire_invoice

router = APIRouter()


@router.get("/long_hire_invoice")
async def get_all_long_hire_invoices():
    pool = get_pool()
    async with pool.acquire() as conn:
        invoices = await inv_q.get_all_long_hire_invoices(conn)
    return {"success": True, "count": len(invoices), "data": invoices}


@router.post("/long_hire_invoice")
async def create_long_hire_invoice_route(data: LongHireInvoiceCreate):
    pool = get_pool()
    async with pool.acquire() as conn:
        invoice_id = await create_long_hire_invoice(conn, data.claim_id, data.amount, data.user_name)
    if invoice_id == 0:
        return {"success": False, "message": "Failed to create invoice"}
    return {"success": True, "invoice_id": invoice_id}


@router.get("/invoice")
async def get_all_invoices():
    pool = get_pool()
    async with pool.acquire() as conn:
        invoices = await inv_q.get_all_invoices(conn)
    return invoices


@router.post("/invoice")
async def create_invoice_route(payload: InvoiceCreate):
    pool = get_pool()
    async with pool.acquire() as conn:
        invoice_id = await create_invoice(conn, payload.claim_id, payload.info, payload.docs or [], payload.storage_bill or 0, payload.rent_bill or 0, payload.user_name)
    if not invoice_id:
        raise HTTPException(status_code=500, detail="Failed to create invoice")
    return {"invoice_id": invoice_id, "message": "Invoice created successfully"}


@router.get("/invoice/{claim_id}")
async def get_invoices_by_claim_id(claim_id: str):
    pool = get_pool()
    async with pool.acquire() as conn:
        invoices = await inv_q.get_invoices_by_claim_id(conn, claim_id)
    return invoices


@router.put("/invoice/{invoice_id}")
async def update_invoice_route(invoice_id: int, payload: InvoiceUpdate):
    pool = get_pool()
    async with pool.acquire() as conn:
        result = await svc_update_invoice(
            conn, invoice_id,
            info=payload.info,
            storage_bill=payload.storage_bill,
            rent_bill=payload.rent_bill,
            user_name=payload.user_name,
            payment_date=payload.payment_date,
            payment_amount=payload.payment_amount,
        )
    if not result:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return {"invoice_id": result, "message": "Invoice updated successfully"}
