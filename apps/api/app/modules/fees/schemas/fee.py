"""Fee schemas."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.db.models.fee import FeeStatus, FeeType, PaymentMode


class FeeRecordOut(BaseModel):
    id: uuid.UUID
    student_id: uuid.UUID
    fee_structure_id: uuid.UUID
    amount: float
    due_date: date
    status: FeeStatus
    paid_amount: float
    paid_at: datetime | None = None
    payment_mode: str | None = None
    receipt_id: uuid.UUID | None = None
    model_config = ConfigDict(from_attributes=True)


class PayFeeRequest(BaseModel):
    fee_record_id: uuid.UUID
    # max_digits=10 matches the Numeric(10,2) column (prevents validate-then-overflow→500).
    amount: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)
    payment_mode: PaymentMode
    razorpay_payment_id: str | None = None
    transaction_id: str | None = Field(None, max_length=100)
    idempotency_key: str | None = Field(None, max_length=64)

    @field_validator("transaction_id")
    @classmethod
    def strip_transaction_id(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            return v or None
        return v


class ReceiptOut(BaseModel):
    id: uuid.UUID
    receipt_number: str
    student_name: str
    class_name: str
    amount_paid: float
    payment_mode: str
    fee_type: str
    fee_period: str | None = None
    paid_at: datetime
    school_name: str
    school_logo_url: str | None = None
    pdf_url: str | None = None
    model_config = ConfigDict(from_attributes=True)
