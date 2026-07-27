"""Deterministic source admission for KAI Phase 4."""

from __future__ import annotations

from app.modules.eui.schemas.knowledge_acquisition import (
    KnowledgeAcquisitionInputReference,
    SourceAdmissionDecision,
)

ADMITTED_SOURCE_TYPES: frozenset[str] = frozenset({
    "pdf",
    "worksheet",
    "ocr_text",
    "answer_key",
    "teacher_note",
    "lesson_plan",
})

NEEDS_REVIEW_SOURCE_TYPES: frozenset[str] = frozenset({
    "student_work",
})


def admit_source(reference: KnowledgeAcquisitionInputReference) -> SourceAdmissionDecision:
    """Return conservative source-admission posture for a KAI input."""

    source_type = reference.source_type
    if source_type in ADMITTED_SOURCE_TYPES:
        return SourceAdmissionDecision(
            status="admitted",
            reason="source_type_admitted_for_phase_4_candidate_generation",
            review_required=True,
        )
    if source_type in NEEDS_REVIEW_SOURCE_TYPES:
        return SourceAdmissionDecision(
            status="needs_review",
            reason="student_work_not_admitted_without_explicit_authorization",
            review_required=True,
        )
    return SourceAdmissionDecision(
        status="unsupported",
        reason="source_type_not_admitted_for_phase_4",
        review_required=True,
    )
