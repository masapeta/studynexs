"""EUI Phase 4 — KAI source admission policy."""

from __future__ import annotations

import uuid

from app.modules.eui.schemas.knowledge_acquisition import KnowledgeAcquisitionInputReference
from app.modules.eui.services.knowledge_acquisition_source_admission import admit_source


def _reference(source_type: str) -> KnowledgeAcquisitionInputReference:
    return KnowledgeAcquisitionInputReference(
        tenant_id=uuid.uuid4(),
        source_type=source_type,  # type: ignore[arg-type]
    )


def test_kai_source_admission_allows_bounded_phase_4_sources():
    for source_type in (
        "pdf",
        "worksheet",
        "ocr_text",
        "answer_key",
        "teacher_note",
        "lesson_plan",
    ):
        decision = admit_source(_reference(source_type))

        assert decision.status == "admitted"
        assert decision.review_required is True


def test_kai_source_admission_rejects_student_work_without_authorization():
    decision = admit_source(_reference("student_work"))

    assert decision.status == "needs_review"
    assert "student_work_not_admitted" in decision.reason
    assert decision.review_required is True


def test_kai_source_admission_fails_closed_for_unsupported_sources():
    decision = admit_source(_reference("image"))

    assert decision.status == "unsupported"
    assert decision.review_required is True
