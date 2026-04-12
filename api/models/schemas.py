"""
Pydantic request / response schemas.

All Pydantic models used by the API layer are defined here so that
they can be imported from a single location in every route module.
"""

from typing import List, Optional
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Auth / User schemas
# ---------------------------------------------------------------------------

class RegisterUserRequest(BaseModel):
    """Payload for POST /api/register."""

    username: str
    password: str
    role: str


class ChangePasswordRequest(BaseModel):
    """Payload for PUT /api/change-password."""

    username: str
    new_password: str


# ---------------------------------------------------------------------------
# Claim schemas
# ---------------------------------------------------------------------------

class SoftDeleteClaimRequest(BaseModel):
    """Payload for PUT /api/claims/{claim_id}/soft-delete."""

    deleted_by: str


class CloseClaimRequest(BaseModel):
    """Payload for PUT /api/claims/{claim_id}/close."""

    closed_by: str
    reason: Optional[str] = None


class ClaimLockUpdate(BaseModel):
    """Payload for PUT /api/claims/{claim_id}/lock."""

    locked: bool
    locked_by: Optional[str] = None


class HireVehicleDatesUpdate(BaseModel):
    """Payload for PUT /api/claims/{claim_id}/hire-vehicle-dates."""

    date_in: Optional[str] = None
    date_out: Optional[str] = None


class PaymentUpdate(BaseModel):
    """Payload for PUT /api/claims/{claim_id}/payment."""

    payment: Optional[str] = None
    pay_date: Optional[str] = None


# ---------------------------------------------------------------------------
# Invoice schemas
# ---------------------------------------------------------------------------

class InvoiceCreate(BaseModel):
    """Payload for POST /api/invoice."""

    claim_id: str
    info: str
    docs: Optional[List[str]] = []
    storage_bill: Optional[float] = 0
    rent_bill: Optional[float] = 0
    user_name: str


class InvoiceUpdate(BaseModel):
    """Payload for PUT /api/invoice/{invoice_id}."""

    info: Optional[str] = None
    storage_bill: Optional[float] = None
    rent_bill: Optional[float] = None
    user_name: Optional[str] = None
    payment_date: Optional[str] = None
    payment_amount: Optional[str] = None


class LongHireInvoiceCreate(BaseModel):
    """Payload for POST /api/long_hire_invoice."""

    claim_id: str
    amount: float
    user_name: str


# ---------------------------------------------------------------------------
# Car schemas
# ---------------------------------------------------------------------------

class CarCreate(BaseModel):
    """Payload for POST /api/car."""

    model: Optional[str] = None
    name: Optional[str] = None
    reg_no: Optional[str] = None
    attributes: Optional[List[str]] = []


class CarUpdate(BaseModel):
    """Payload for PUT /api/car/{car_id}."""

    model: Optional[str] = None
    name: Optional[str] = None
    service_time: Optional[str] = None
    attributes: Optional[List[str]] = []


# ---------------------------------------------------------------------------
# Long-claim schemas
# ---------------------------------------------------------------------------

class LongClaimCreate(BaseModel):
    """Payload for POST /api/long-claim."""

    starting_date: Optional[str] = None
    ending_date: Optional[str] = None
    hirer_name: Optional[str] = None


class LongClaimUpdate(BaseModel):
    """Payload for PUT /api/long-claim."""

    long_claim_id: str
    starting_date: Optional[str] = None
    ending_date: Optional[str] = None
    hirer_name: Optional[str] = None


class LongClaimCarAction(BaseModel):
    """Payload for POST /api/long-claim/{long_claim_id}/add-car."""

    car_id: int


class DailyRateUpdate(BaseModel):
    """Payload for PUT /api/long-claim/{long_claim_id}/daily-rate."""

    car_id: int
    daily_rate: float


# ---------------------------------------------------------------------------
# Claimant schemas
# ---------------------------------------------------------------------------

class ClaimantCreate(BaseModel):
    """Payload for POST /api/claimant."""

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
    """Payload for PUT /api/claimant/{claimant_id}."""

    claimant_id: Optional[str] = None
    ref_no: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    miles: Optional[float] = None
    name: Optional[str] = None
    location: Optional[str] = None
    delivery_charges: Optional[float] = None


# ---------------------------------------------------------------------------
# Notification schemas
# ---------------------------------------------------------------------------

class BroadcastCreate(BaseModel):
    """Payload for POST /api/notifications/broadcast."""

    sender_id: int
    title: str
    message: str


# ---------------------------------------------------------------------------
# Internal / Dependency schemas
# ---------------------------------------------------------------------------

class CurrentUser(BaseModel):
    """
    Represents the currently authenticated user as injected by
    :func:`~api.dependencies.get_current_user`.
    """

    id: str
    username: str
    role: str
    permissions: dict = {}
