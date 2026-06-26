"""School operations schemas — library, events."""

import re
import uuid
from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class LibraryBookOut(BaseModel):
    id: uuid.UUID
    title: str
    author: Optional[str] = None
    isbn: Optional[str] = None
    category: Optional[str] = None
    total_copies: int
    available_copies: int
    issued_to: list[str] = Field(default_factory=list)

class LibraryBookCreate(BaseModel):
    title: str = Field(..., max_length=300)
    author: Optional[str] = None
    isbn: Optional[str] = None
    category: Optional[str] = None
    total_copies: int = 1

class EventOut(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str] = None
    event_date: date
    event_time: Optional[str] = None
    venue: Optional[str] = None
    target_roles: Optional[list[str]] = None
    model_config = ConfigDict(from_attributes=True)

class EventCreate(BaseModel):
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    event_date: date
    venue: Optional[str] = None
    target_roles: Optional[list[str]] = None


class TransportRouteCreate(BaseModel):
    route_name: str = Field(..., max_length=100)
    vehicle_number: Optional[str] = None
    driver_name: Optional[str] = None
    driver_contact: Optional[str] = None
    stops: Optional[list] = None
    capacity: int = 30


class AdmissionCandidateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    grade_applied: str = Field(..., min_length=1, max_length=40)
    enquiry_date: date
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, pattern="^(male|female|other)$")
    parent_name: str = Field(..., min_length=1, max_length=120)
    parent_relation: str = Field(default="father", pattern="^(father|mother|guardian)$")
    parent_occupation: Optional[str] = Field(None, max_length=120)
    parent_mobile: str = Field(..., min_length=10, max_length=20)
    parent_email: Optional[str] = Field(None, max_length=120)
    address_line: Optional[str] = Field(None, max_length=300)
    city: Optional[str] = Field(None, max_length=80)
    previous_school_name: Optional[str] = Field(None, max_length=200)
    previous_grade: Optional[str] = Field(None, max_length=40)
    enquiry_source: Optional[str] = Field(
        None, pattern="^(walk_in|referral|website|phone|social|other)$"
    )
    notes: Optional[str] = Field(None, max_length=2000)


class AdmissionStageUpdate(BaseModel):
    stage: str = Field(..., pattern="^(enquiry|applied|interview|offer|enrolled)$")
    details: Optional[dict] = None


class AdmissionDocumentExtractRequest(BaseModel):
    file_id: uuid.UUID
    document_type: str = Field(..., pattern="^(aadhaar|birth_certificate|apaar)$")


class AppliedStageDetails(BaseModel):
    application_date: date
    birth_certificate_file_id: uuid.UUID
    birth_certificate_file_name: Optional[str] = Field(None, max_length=300)
    birth_certificate_number: str = Field(..., min_length=1, max_length=40)
    aadhaar_file_id: uuid.UUID
    aadhaar_file_name: Optional[str] = Field(None, max_length=300)
    aadhaar_number: str = Field(..., pattern=r"^\d{12}$")
    apaar_file_id: Optional[uuid.UUID] = None
    apaar_file_name: Optional[str] = Field(None, max_length=300)
    apaar_number: Optional[str] = Field(None, max_length=30)
    report_card_file_id: Optional[uuid.UUID] = None
    report_card_file_name: Optional[str] = Field(None, max_length=300)
    preferred_joining_date: Optional[date] = None
    sibling_in_school: bool = False
    sibling_details: Optional[str] = Field(None, max_length=200)
    application_notes: Optional[str] = Field(None, max_length=2000)

    @field_validator("aadhaar_number", mode="before")
    @classmethod
    def normalize_aadhaar(cls, value: object) -> object:
        if value is None:
            return value
        digits = re.sub(r"\D", "", str(value))
        return digits

    @field_validator("apaar_number", mode="before")
    @classmethod
    def normalize_apaar(cls, value: object) -> object | None:
        if value is None or str(value).strip() == "":
            return None
        digits = re.sub(r"\D", "", str(value))
        return digits if digits else None

    @field_validator("birth_certificate_number", mode="before")
    @classmethod
    def normalize_birth_certificate(cls, value: object) -> object:
        if value is None:
            return value
        return re.sub(r"\s+", " ", str(value).strip().upper())


class InterviewStageDetails(BaseModel):
    exam_date: date
    exam_time: Optional[str] = Field(None, max_length=10)
    exam_venue: Optional[str] = Field(None, max_length=200)
    exam_type: str = Field(..., pattern="^(written|interview|both)$")
    schedule_notes: Optional[str] = Field(None, max_length=2000)


class OfferStageDetails(BaseModel):
    exam_marks: float = Field(..., ge=0)
    max_marks: float = Field(100, gt=0)
    merit_result: str = Field(..., pattern="^(pass|merit|waitlist|fail)$")
    recommended_for_offer: bool = False
    merit_notes: Optional[str] = Field(None, max_length=2000)
    admission_fee: float = Field(..., ge=0)
    annual_school_fee: float = Field(..., ge=0)
    transport_fee: float = Field(0, ge=0)
    hostel_fee: float = Field(0, ge=0)
    books_uniform_fee: float = Field(0, ge=0)
    other_fees: float = Field(0, ge=0)
    fee_agreement_date: date
    parent_agreed: bool = False
    fee_notes: Optional[str] = Field(None, max_length=2000)

    @model_validator(mode="after")
    def validate_merit_and_fees(self):
        if self.exam_marks > self.max_marks:
            raise ValueError("Exam marks cannot exceed maximum marks")
        if self.merit_result == "fail":
            raise ValueError("Cannot move to offer with a fail result — move candidate back to interview")
        if not self.recommended_for_offer:
            raise ValueError("Candidate must be recommended for offer based on exam merit")
        if not self.parent_agreed:
            raise ValueError("Parent must agree to the proposed fee structure")
        return self


class EnrolledStageDetails(BaseModel):
    tc_received: bool = False
    tc_number: str = Field(..., min_length=1, max_length=60)
    tc_issue_date: Optional[date] = None
    admission_fee_paid: bool = False
    payment_reference: Optional[str] = Field(None, max_length=120)
    enrollment_date: date
    provisional_admission_no: Optional[str] = Field(None, max_length=60)
    enrollment_notes: Optional[str] = Field(None, max_length=2000)

    @model_validator(mode="after")
    def require_enrollment_checklist(self):
        if not self.tc_received:
            raise ValueError("Transfer certificate (TC) must be marked as received")
        if not self.admission_fee_paid:
            raise ValueError("Admission fee must be marked as paid")
        return self


class SchoolExpenseCreate(BaseModel):
    vendor: str = Field(..., max_length=200)
    category: str = Field(..., max_length=60)
    amount: float = Field(..., gt=0)
    expense_date: date
    receipt_file_id: Optional[uuid.UUID] = None


class TransportAssignRequest(BaseModel):
    student_id: uuid.UUID
    route_id: uuid.UUID
    boarding_stop: Optional[str] = None


class ResidentialBlockCreate(BaseModel):
    block_name: str = Field(..., max_length=100)
    block_gender: str = "mixed"
    warden_name: Optional[str] = None
    warden_contact: Optional[str] = None
    total_rooms: int = 0


class ResidentialAllocateRequest(BaseModel):
    student_id: uuid.UUID
    block_id: uuid.UUID
    room_number: Optional[str] = None


class StaffOnboardCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, pattern="^(male|female|other)$")
    mobile: str = Field(..., min_length=10, max_length=15)
    email: Optional[str] = Field(None, max_length=255)
    address_line: Optional[str] = Field(None, max_length=300)
    city: Optional[str] = Field(None, max_length=80)
    role: str = Field(
        ...,
        pattern="^(teacher|class_incharge|admin|operations)$",
    )
    employee_id: Optional[str] = Field(None, max_length=50)
    department: Optional[str] = Field(None, max_length=100)
    qualification: Optional[str] = Field(None, max_length=500)
    joining_date: Optional[date] = None
    previous_experience: Optional[str] = Field(None, max_length=5000)
    aadhaar_number: Optional[str] = Field(None, max_length=12)
    aadhaar_document_file_id: Optional[uuid.UUID] = None
    experience_document_file_id: Optional[uuid.UUID] = None

    @field_validator("aadhaar_number", mode="before")
    @classmethod
    def normalize_aadhaar(cls, value: object) -> object | None:
        if value is None or str(value).strip() == "":
            return None
        digits = re.sub(r"\D", "", str(value))
        if len(digits) != 12:
            raise ValueError("Aadhaar must be 12 digits")
        return digits
