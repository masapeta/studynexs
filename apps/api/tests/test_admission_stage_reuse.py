"""Admission stage reuse — saved details when moving back and forward."""
from __future__ import annotations

import uuid
from datetime import date

from app.db.models.school_ops import AdmissionCandidate, AdmissionStage
from app.modules.school_ops.services.ops_service import SchoolOpsService


def _candidate(**kwargs) -> AdmissionCandidate:
    row = AdmissionCandidate(
        school_id=uuid.uuid4(),
        name="Test Student",
        grade_applied="5",
        stage=AdmissionStage.ENQUIRY,
        enquiry_date=date.today(),
        stage_details={},
    )
    for key, value in kwargs.items():
        setattr(row, key, value)
    return row


def test_has_saved_stage_details_when_later_stage_exists():
    service = SchoolOpsService(db=None)  # type: ignore[arg-type]
    row = _candidate(
        stage=AdmissionStage.ENQUIRY,
        stage_details={
            "interview": {"exam_date": "2026-06-01", "exam_type": "both"},
        },
    )
    assert service._has_saved_stage_details(row, AdmissionStage.APPLIED) is True


def test_has_saved_stage_details_when_same_stage_exists():
    service = SchoolOpsService(db=None)  # type: ignore[arg-type]
    row = _candidate(
        stage_details={
            "applied": {
                "application_date": "2026-06-01",
                "birth_certificate_file_id": str(uuid.uuid4()),
                "aadhaar_file_id": str(uuid.uuid4()),
            }
        }
    )
    assert service._has_saved_stage_details(row, AdmissionStage.APPLIED) is True


def test_has_saved_stage_details_false_for_first_time():
    service = SchoolOpsService(db=None)  # type: ignore[arg-type]
    row = _candidate(stage_details={})
    assert service._has_saved_stage_details(row, AdmissionStage.APPLIED) is False
