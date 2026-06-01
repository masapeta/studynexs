"""Fee models — fee structures, student fee records, and payment receipts."""
from __future__ import annotations

import enum
import uuid
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import BaseModel


class FeeType(str, enum.Enum):
    TUITION = "tuition"
    TRANSPORT = "transport"
    LIBRARY = "library"
    LAB = "lab"
    SPORTS = "sports"
    MISCELLANEOUS = "miscellaneous"


class FeeFrequency(str, enum.Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    ONE_TIME = "one_time"


class FeeStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"
    WAIVED = "waived"
    PARTIAL = "partial"


class PaymentMode(str, enum.Enum):
    ONLINE = "online"        # Razorpay
    CASH = "cash"
    CHEQUE = "cheque"
    BANK_TRANSFER = "bank_transfer"
    UPI = "upi"


class FeeStructure(BaseModel):
    __tablename__ = "fee_structures"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    class_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("classes.id"), nullable=True
    )  # NULL = all classes
    fee_type: Mapped[FeeType] = mapped_column(Enum(FeeType), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    frequency: Mapped[FeeFrequency] = mapped_column(Enum(FeeFrequency), nullable=False)
    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("academic_years.id"), nullable=False
    )
    due_day: Mapped[int | None] = mapped_column()  # day of month


class StudentFeeRecord(BaseModel):
    __tablename__ = "student_fee_records"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id"), nullable=False
    )
    fee_structure_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("fee_structures.id"), nullable=False
    )
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[FeeStatus] = mapped_column(Enum(FeeStatus), default=FeeStatus.PENDING)
    paid_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    payment_mode: Mapped[PaymentMode | None] = mapped_column(Enum(PaymentMode))
    razorpay_order_id: Mapped[str | None] = mapped_column(String(100))
    razorpay_payment_id: Mapped[str | None] = mapped_column(String(100))

    # Receipt linkage — populated after payment
    receipt_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("fee_receipts.id"), nullable=True
    )

    receipt = relationship("FeeReceipt", lazy="selectin")

    __table_args__ = (
        Index("ix_fees_school_student_status", "school_id", "student_id", "status"),
        Index("ix_fees_school_due_status", "school_id", "due_date", "status"),
    )


class FeeReceipt(BaseModel):
    """
    Immutable payment receipt — generated on successful payment.
    receipt_number is unique per school and auto-incremented.
    Stores a snapshot of school logo URL so receipts remain valid
    even if the school changes their logo later.
    """
    __tablename__ = "fee_receipts"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    # Unique receipt number per school: SIA-2026-00001, SIA-2026-00002, ...
    receipt_number: Mapped[str] = mapped_column(String(50), nullable=False)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id"), nullable=False
    )
    student_name: Mapped[str] = mapped_column(String(200), nullable=False)  # snapshot
    class_name: Mapped[str] = mapped_column(String(50), nullable=False)     # snapshot: "Grade 5-A"
    amount_paid: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    payment_mode: Mapped[PaymentMode] = mapped_column(Enum(PaymentMode), nullable=False)
    fee_type: Mapped[str] = mapped_column(String(50), nullable=False)       # snapshot: "Tuition"
    fee_period: Mapped[str | None] = mapped_column(String(50))              # "July 2026", "Q1 2026"
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Razorpay details (if online payment)
    razorpay_payment_id: Mapped[str | None] = mapped_column(String(100))
    transaction_id: Mapped[str | None] = mapped_column(String(100))

    # School branding snapshot (immutable — captured at receipt time)
    school_name: Mapped[str] = mapped_column(String(200), nullable=False)
    school_logo_url: Mapped[str | None] = mapped_column(String(500))
    school_address: Mapped[str | None] = mapped_column(Text)
    school_contact: Mapped[str | None] = mapped_column(String(100))

    # Generated PDF stored in Blob Storage
    pdf_url: Mapped[str | None] = mapped_column(String(500))

    # Sequence tracking: school-level auto-increment for receipt numbers
    receipt_sequence: Mapped[int] = mapped_column(BigInteger, nullable=False)

    __table_args__ = (
        UniqueConstraint("school_id", "receipt_number", name="uq_receipt_number_per_school"),
        UniqueConstraint("school_id", "receipt_sequence", name="uq_receipt_sequence_per_school"),
        Index("ix_receipts_student", "school_id", "student_id"),
        # Idempotency: at most one receipt per (school, transaction_id) for gateway payments.
        Index(
            "uq_receipt_txn_per_school", "school_id", "transaction_id",
            unique=True, postgresql_where=text("transaction_id IS NOT NULL"),
        ),
    )


class ReceiptCounter(BaseModel):
    """
    Atomic per-school receipt counter — prevents race conditions.

    HOW IT WORKS (race-condition safe):
    1. BEGIN TRANSACTION
    2. SELECT last_sequence FROM receipt_counters
       WHERE school_id = ? FOR UPDATE;          ← row-level lock
    3. next_seq = last_sequence + 1
    4. UPDATE receipt_counters SET last_sequence = next_seq WHERE school_id = ?
    5. INSERT INTO fee_receipts (..., receipt_sequence=next_seq, receipt_number='SIA-2026-00042')
    6. COMMIT                                    ← lock released

    If two parents pay simultaneously:
    - Parent A acquires the row lock, gets seq=42, updates to 43
    - Parent B WAITS until Parent A commits
    - Parent B then gets seq=43, updates to 44
    - Zero conflicts, zero retries, guaranteed sequential
    """
    __tablename__ = "receipt_counters"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), unique=True, nullable=False
    )
    last_sequence: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    prefix: Mapped[str] = mapped_column(String(10), nullable=False)  # "SIA", "GVPS", "LSS"

