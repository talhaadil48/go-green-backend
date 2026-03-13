"""Centralized Pydantic request/response schemas for the Go-Green API.

All request body models used by the ``/api``, ``/post``, and ``/auth`` routers
are defined here so that schema changes are made in a single place.

Import pattern inside a router module::

    from api.schemas import CarCreate, CarUpdate, InvoiceCreate
"""

from typing import Any, List, Optional
from pydantic import BaseModel


# ─────────────────────────────────────────────────────────────────────────────
# Claims
# ─────────────────────────────────────────────────────────────────────────────

class SoftDeleteClaimRequest(BaseModel):
    """Body for PUT /api/claims/{claim_id}/soft-delete."""
    deleted_by: str


class CloseClaimRequest(BaseModel):
    """Body for PUT /api/claims/{claim_id}/close."""
    closed_by: str


# ─────────────────────────────────────────────────────────────────────────────
# Cars
# ─────────────────────────────────────────────────────────────────────────────

class CarCreate(BaseModel):
    """Body for POST /api/car."""
    model: str
    name: str
    reg_no: str


class CarUpdate(BaseModel):
    """Body for PUT /api/car/{car_id}."""
    model: str
    name: str
    reg_no: str


# ─────────────────────────────────────────────────────────────────────────────
# Invoices
# ─────────────────────────────────────────────────────────────────────────────

class InvoiceCreate(BaseModel):
    """Body for POST /api/invoice."""
    claim_id: str
    info: Optional[str] = None
    docs: Optional[List[Any]] = None
    storage_bill: Optional[float] = None
    rent_bill: Optional[float] = None
    user_name: Optional[str] = None


class InvoiceUpdate(BaseModel):
    """Body for PUT /api/invoice/{invoice_id}."""
    info: Optional[str] = None
    storage_bill: Optional[float] = None
    rent_bill: Optional[float] = None
    user_name: Optional[str] = None


class LongHireInvoiceCreate(BaseModel):
    """Body for POST /api/long_hire_invoice."""
    claim_id: str
    amount: float
    user_name: str


# ─────────────────────────────────────────────────────────────────────────────
# Long-hire claims
# ─────────────────────────────────────────────────────────────────────────────

class LongClaimCreate(BaseModel):
    """Body for POST /api/long-claim."""
    starting_date: Optional[str] = None
    ending_date: Optional[str] = None
    hirer_name: Optional[str] = None


class LongClaimUpdate(BaseModel):
    """Body for PUT /api/long-claim."""
    long_claim_id: str
    starting_date: Optional[str] = None
    ending_date: Optional[str] = None
    hirer_name: Optional[str] = None


class LongClaimCarAction(BaseModel):
    """Body for POST /api/long-claim/{long_claim_id}/add-car."""
    car_id: int


# ─────────────────────────────────────────────────────────────────────────────
# Claimants
# ─────────────────────────────────────────────────────────────────────────────

class ClaimantCreate(BaseModel):
    """Body for POST /api/claimant."""
    long_claim_id: str
    car_id: int
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    miles: Optional[float] = None
    name: Optional[str] = None
    location: Optional[str] = None
    delivery_charges: Optional[float] = None


class ClaimantUpdate(BaseModel):
    """Body for PUT /api/claimant/{claimant_id}."""
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    miles: Optional[float] = None
    name: Optional[str] = None
    location: Optional[str] = None
    delivery_charges: Optional[float] = None


# ─────────────────────────────────────────────────────────────────────────────
# Daily rates
# ─────────────────────────────────────────────────────────────────────────────

class DailyRateUpdate(BaseModel):
    """Body for PUT /api/long-claim/{long_claim_id}/daily-rate."""
    car_id: int
    daily_rate: float


# ─────────────────────────────────────────────────────────────────────────────
# Users / auth
# ─────────────────────────────────────────────────────────────────────────────

class RegisterUserRequest(BaseModel):
    """Body for POST /api/register."""
    username: str
    password: str
    role: str


class ChangePasswordRequest(BaseModel):
    """Body for PUT /api/change-password."""
    username: str
    new_password: str
