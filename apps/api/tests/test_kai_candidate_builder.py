"""EUI Phase 4 — KAI candidate builder."""

from __future__ import annotations

import uuid

from app.modules.eui.schemas.knowledge_acquisition import KnowledgeAcquisitionInputReference
from app.modules.eui.services.knowledge_acquisition_builder import (
    KnowledgeAcquisitionCandidateBuilder,
)
from app.modules.eui.services.knowledge_acquisition_candidate_id import (
    content_hash,
    stable_kai_candidate_id,
)


def test_kai_candidate_builder_creates_candidate_without_authority():
    reference = _reference(
        source_type="pdf",
        artifact_type="worksheet",
        supplied_extracted_text="Question 1: Measure the length.",
        educational_identity_id="ei://cbse/ncf2023/2024/g6/science/ch05",
        educational_context_summary={
            "board": "CBSE",
            "curriculum": "NCF2023",
            "grade": "6",
            "subject": "Science",
        },
    )
    builder = KnowledgeAcquisitionCandidateBuilder()

    candidate = builder.build(reference)

    assert candidate.id == stable_kai_candidate_id(reference)
    assert candidate.source_admission_status == "admitted"
    assert candidate.extraction_status == "supplied"
    assert candidate.review_status == "candidate"
    assert candidate.authoritative is False
    assert candidate.trust_signals.review_required is True
    assert candidate.normalized_content["extracted_text_sha256"] == content_hash(
        "Question 1: Measure the length."
    )
    assert "Question 1" not in str(candidate.normalized_content)


def test_kai_candidate_builder_marks_missing_identity_context_ambiguous():
    candidate = KnowledgeAcquisitionCandidateBuilder().build(
        _reference(
            source_type="teacher_note",
            supplied_extracted_text="Use local examples for motion.",
        )
    )

    assert candidate.review_status == "ambiguous"
    assert candidate.trust_signals.ambiguity_count == 2
    assert candidate.authoritative is False


def test_kai_candidate_builder_rejects_unsupported_source_type_safely():
    candidate = KnowledgeAcquisitionCandidateBuilder().build(
        _reference(
            source_type="image",
            supplied_extracted_text="diagram pixels",
        )
    )

    assert candidate.source_admission_status == "unsupported"
    assert candidate.extraction_status == "unsupported"
    assert candidate.review_status == "unsupported"
    assert candidate.authoritative is False


def test_kai_candidate_builder_keeps_student_work_out_of_admitted_sources():
    candidate = KnowledgeAcquisitionCandidateBuilder().build(
        _reference(
            source_type="student_work",
            supplied_extracted_text="student answer",
            educational_identity_id="ei://cbse/ncf2023/g6/science/ch05",
            educational_context_summary={"board": "CBSE", "grade": "6", "subject": "Science"},
        )
    )

    assert candidate.source_admission_status == "needs_review"
    assert candidate.review_status == "needs_review"
    assert "student_work_not_admitted" in candidate.metadata["source_admission_reason"]


def test_kai_candidate_builder_attaches_supported_capability_posture():
    candidate = KnowledgeAcquisitionCandidateBuilder().build(
        _reference(
            source_type="ocr_text",
            artifact_type="worksheet",
            supplied_extracted_text="स्पष्ट मुद्रित पाठ",
            detected_language="Hindi",
            detected_script="Devanagari",
            educational_identity_id="ei://cbse/ncf2023/g6/hindi/ch01",
            educational_context_summary={"language": "Hindi"},
            capability_domain="language",
            capability_key="printed_ocr",
            metadata={"capability_input_type": "printed_text"},
        )
    )

    assert candidate.capability_mode == "supported"
    assert candidate.capability_matched is True
    assert candidate.review_status == "candidate"


def test_kai_candidate_builder_does_not_upgrade_assist_capability_posture():
    candidate = KnowledgeAcquisitionCandidateBuilder().build(
        _reference(
            source_type="ocr_text",
            artifact_type="worksheet",
            supplied_extracted_text="हस्तलिखित पाठ",
            detected_language="Hindi",
            detected_script="Devanagari",
            educational_identity_id="ei://cbse/ncf2023/g6/hindi/ch01",
            educational_context_summary={"language": "Hindi"},
            capability_domain="language",
            capability_key="handwriting_ocr",
            metadata={"capability_input_type": "handwriting"},
        )
    )

    assert candidate.capability_mode == "assist"
    assert candidate.review_status == "needs_review"
    assert candidate.trust_signals.review_required is True


def test_kai_candidate_id_uses_hash_not_raw_text():
    reference = _reference(
        source_type="answer_key",
        supplied_extracted_text="secret answer key text",
    )

    candidate_id = stable_kai_candidate_id(reference)

    assert candidate_id.startswith("kai://answer-key/")
    assert "secret" not in candidate_id
    assert candidate_id == stable_kai_candidate_id(reference)


def _reference(**kwargs) -> KnowledgeAcquisitionInputReference:
    payload = {"tenant_id": uuid.uuid4(), **kwargs}
    return KnowledgeAcquisitionInputReference(**payload)
