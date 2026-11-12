from pydantic import BaseModel
from typing import Optional, List


class BroadcastCreate(BaseModel):
    sender_id: int
    title: str
    message: str


class HireVehicleDatesUpdate(BaseModel):
    date_in: Optional[str] = None
    date_out: Optional[str] = None


class DailyRateUpdate(BaseModel):
    car_id: int
    daily_rate: float


class PaymentUpdate(BaseModel):
    payment: Optional[str] = None
    pay_date: Optional[str] = None


class ClaimLockUpdate(BaseModel):
    locked: bool
    locked_by: Optional[str] = None


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
    hirer_name: Optional[str] = None


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
    attributes: Optional[List[str]] = []


class CarUpdate(BaseModel):
    model: Optional[str] = None
    name: Optional[str] = None
    service_time: Optional[str] = None
    attributes: Optional[List[str]] = []


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
    reason: Optional[str] = None


class LongHireInvoiceCreate(BaseModel):
    claim_id: str
    amount: float
    user_name: str


class InvoiceUpdate(BaseModel):
    info: str | None = None
    storage_bill: float | None = None
    rent_bill: float | None = None
    user_name: str | None = None
    payment_date: str | None = None
    payment_amount: str | None = None
