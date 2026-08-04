"""School operations — Transport, Library, Events."""
from __future__ import annotations

import enum
import uuid
from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.encryption import EncryptedString
from app.db.models.base import BaseModel


class TransportRoute(BaseModel):
    __tablename__ = "transport_routes"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    route_name: Mapped[str] = mapped_column(String(100), nullable=False)
    vehicle_number: Mapped[str | None] = mapped_column(String(20))
    driver_name: Mapped[str | None] = mapped_column(String(100))
    driver_contact: Mapped[str | None] = mapped_column(String(15))
    stops: Mapped[dict | None] = mapped_column(JSONB, default=list)
    capacity: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class StudentTransport(BaseModel):
    __tablename__ = "student_transport"

    # Defense-in-depth tenancy (§22): scoped through student/route too, but
    # every tenant-owned row carries its own school_id.
    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id"), nullable=False
    )
    route_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transport_routes.id"), nullable=False
    )
    boarding_stop: Mapped[str | None] = mapped_column(String(100))


class LibraryBook(BaseModel):
    __tablename__ = "library_books"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    author: Mapped[str | None] = mapped_column(String(200))
    isbn: Mapped[str | None] = mapped_column(String(20))
    category: Mapped[str | None] = mapped_column(String(100))
    total_copies: Mapped[int] = mapped_column(Integer, default=1)
    available_copies: Mapped[int] = mapped_column(Integer, default=1)


class LibraryIssueStatus(str, enum.Enum):
    ISSUED = "issued"
    RETURNED = "returned"
    OVERDUE = "overdue"


class LibraryIssue(BaseModel):
    __tablename__ = "library_issues"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    book_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("library_books.id"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    due_date: Mapped[date | None] = mapped_column(Date)
    returned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fine_amount: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=Decimal("0.00"))
    status: Mapped[LibraryIssueStatus] = mapped_column(
        Enum(LibraryIssueStatus), default=LibraryIssueStatus.ISSUED
    )


class Event(BaseModel):
    __tablename__ = "events"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    event_time: Mapped[time | None] = mapped_column(Time)
    venue: Mapped[str | None] = mapped_column(String(200))
    target_roles: Mapped[dict | None] = mapped_column(JSONB)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )


class AdmissionStage(str, enum.Enum):
    ENQUIRY = "enquiry"
    APPLIED = "applied"
    INTERVIEW = "interview"
    OFFER = "offer"
    ENROLLED = "enrolled"


ADMISSION_STAGE_ORDER = [
    AdmissionStage.ENQUIRY,
    AdmissionStage.APPLIED,
    AdmissionStage.INTERVIEW,
    AdmissionStage.OFFER,
    AdmissionStage.ENROLLED,
]


class AdmissionCandidate(BaseModel):
    __tablename__ = "admission_candidates"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    grade_applied: Mapped[str] = mapped_column(String(40), nullable=False)
    stage: Mapped[AdmissionStage] = mapped_column(
        Enum(AdmissionStage, values_callable=lambda obj: [e.value for e in obj]),
        default=AdmissionStage.ENQUIRY,
        nullable=False,
    )
    enquiry_date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    gender: Mapped[str | None] = mapped_column(String(20))
    parent_name: Mapped[str | None] = mapped_column(String(120))
    parent_relation: Mapped[str | None] = mapped_column(String(20))
    parent_occupation: Mapped[str | None] = mapped_column(String(120))
    parent_mobile: Mapped[str | None] = mapped_column(String(20))
    parent_email: Mapped[str | None] = mapped_column(String(120))
    address_line: Mapped[str | None] = mapped_column(String(300))
    city: Mapped[str | None] = mapped_column(String(80))
    previous_school_name: Mapped[str | None] = mapped_column(String(200))
    previous_grade: Mapped[str | None] = mapped_column(String(40))
    enquiry_source: Mapped[str | None] = mapped_column(String(40))
    aadhaar_number: Mapped[str | None] = mapped_column(EncryptedString(512))
    birth_certificate_number: Mapped[str | None] = mapped_column(String(40))
    apaar_number: Mapped[str | None] = mapped_column(String(30))
    stage_details: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )


class PayrollStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"


class StaffPayrollEntry(BaseModel):
    __tablename__ = "staff_payroll_entries"
    __table_args__ = (
        UniqueConstraint("school_id", "user_id", "period_month", name="uq_payroll_user_month"),
    )

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    period_month: Mapped[date] = mapped_column(Date, nullable=False)
    gross_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[PayrollStatus] = mapped_column(
        Enum(PayrollStatus, values_callable=lambda obj: [e.value for e in obj]),
        default=PayrollStatus.PENDING,
        nullable=False,
    )
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class StaffProfile(BaseModel):
    """HR onboarding record for school staff (all staff roles)."""

    __tablename__ = "staff_profiles"
    __table_args__ = (UniqueConstraint("user_id", name="uq_staff_profiles_user"),)

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    gender: Mapped[str | None] = mapped_column(String(10))
    aadhaar_number: Mapped[str | None] = mapped_column(EncryptedString(512))
    address_line: Mapped[str | None] = mapped_column(String(300))
    city: Mapped[str | None] = mapped_column(String(80))
    qualification: Mapped[str | None] = mapped_column(Text)
    department: Mapped[str | None] = mapped_column(String(100))
    employee_id: Mapped[str | None] = mapped_column(String(50))
    joining_date: Mapped[date | None] = mapped_column(Date)
    previous_experience: Mapped[str | None] = mapped_column(Text)
    aadhaar_document_file_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("uploaded_files.id"), nullable=True
    )
    experience_document_file_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("uploaded_files.id"), nullable=True
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )


class SchoolExpense(BaseModel):
    __tablename__ = "school_expenses"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    vendor: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(60), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    expense_date: Mapped[date] = mapped_column(Date, nullable=False)
    receipt_file_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("uploaded_files.id"), nullable=True
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
