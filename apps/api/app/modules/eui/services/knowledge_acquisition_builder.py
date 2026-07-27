"""Passive KAI candidate builder for Phase 4."""

from __future__ import annotations

from typing import Any

from app.modules.eui.schemas.knowledge_acquisition import (
    EducationalArtifactCandidate,
    KnowledgeAcquisitionInputReference,
    KnowledgeAcquisitionModality,
    KnowledgeAcquisitionProvenance,
    KnowledgeAcquisitionTrustSignals,
)
from app.modules.eui.schemas.platform_capability import (
    PlatformCapabilityLookupRequest,
    PlatformCapabilityLookupResult,
)
from app.modules.eui.services.knowledge_acquisition_candidate_id import (
    content_hash,
    stable_kai_candidate_id,
)
from app.modules.eui.services.knowledge_acquisition_source_admission import admit_source
from app.modules.eui.services.platform_capability_lookup import PlatformCapabilityLookupService


class KnowledgeAcquisitionCandidateBuilder:
    """Build non-authoritative KAI candidates from structured inputs."""

    def __init__(
        self,
        capability_lookup: PlatformCapabilityLookupService | None = None,
    ) -> None:
        self.capability_lookup = capability_lookup or PlatformCapabilityLookupService()

    def build(
        self,
        reference: KnowledgeAcquisitionInputReference,
    ) -> EducationalArtifactCandidate:
        admission = admit_source(reference)
        capability_result = self._lookup_capability(reference)
        extraction_status = _extraction_status(reference, admission.status)
        ambiguity_count = _ambiguity_count(reference)
        review_status = _review_status(
            admission_status=admission.status,
            capability_result=capability_result,
            ambiguity_count=ambiguity_count,
        )
        capability_mode = capability_result.mode if capability_result else None
        normalized_content = _normalized_content(reference)

        return EducationalArtifactCandidate(
            id=stable_kai_candidate_id(reference),
            tenant_id=reference.tenant_id,
            source_type=reference.source_type,
            artifact_type=reference.artifact_type,
            modality=reference.modality or _infer_modality(reference.source_type),
            source_admission_status=admission.status,
            extraction_status=extraction_status,
            review_status=review_status,
            extracted_text=reference.supplied_extracted_text,
            normalized_content=normalized_content,
            detected_language=reference.detected_language,
            detected_script=reference.detected_script,
            educational_identity_id=reference.educational_identity_id,
            educational_context_summary=dict(reference.educational_context_summary),
            capability_mode=capability_mode,
            capability_matched=capability_result.matched if capability_result else False,
            provenance=KnowledgeAcquisitionProvenance(
                source="kai_phase_4_passive_candidate_builder",
                source_reference=reference.source_reference,
                source_version=reference.source_version,
                checksum=reference.checksum,
                page_number=reference.page_number,
                metadata={
                    "authorization": "EUI-PH4-KAI-AUTH-001",
                    "source_type": reference.source_type,
                },
            ),
            trust_signals=KnowledgeAcquisitionTrustSignals(
                input_quality=reference.input_quality,
                extraction_confidence=reference.extraction_confidence,
                language_confidence=reference.language_confidence,
                capability_mode=capability_mode,
                review_required=admission.review_required or review_status != "candidate",
                ambiguity_count=ambiguity_count,
                metadata={
                    "source_admission_reason": admission.reason,
                    "capability_fallback": (
                        capability_result.fallback_reason if capability_result else None
                    ),
                },
            ),
            metadata={
                "authorization": "EUI-PH4-KAI-AUTH-001",
                "passive": True,
                "candidate_only": True,
                "source_admission_reason": admission.reason,
                "capability_authoritative": (
                    capability_result.authoritative if capability_result else None
                ),
            },
        )

    def _lookup_capability(
        self,
        reference: KnowledgeAcquisitionInputReference,
    ) -> PlatformCapabilityLookupResult | None:
        if not reference.capability_domain or not reference.capability_key:
            return None
        context = reference.educational_context_summary
        return self.capability_lookup.lookup(
            PlatformCapabilityLookupRequest(
                domain=reference.capability_domain,
                capability_key=reference.capability_key,
                board=_string_or_none(context.get("board")),
                curriculum=_string_or_none(context.get("curriculum")),
                curriculum_version=_string_or_none(context.get("curriculum_version")),
                grade=_string_or_none(context.get("grade")),
                subject=_string_or_none(context.get("subject")),
                language=reference.detected_language or _string_or_none(context.get("language")),
                script=reference.detected_script,
                input_type=_capability_input_type(reference),
                artifact_type=reference.artifact_type,
                assessment_mode=_string_or_none(context.get("assessment_mode")),
                metadata={"source": "kai_candidate_builder"},
            )
        )


def _extraction_status(
    reference: KnowledgeAcquisitionInputReference,
    admission_status: str,
) -> str:
    if admission_status == "unsupported":
        return "unsupported"
    if admission_status == "needs_review":
        return "partial"
    if reference.supplied_extracted_text:
        return "supplied"
    return "not_attempted"


def _review_status(
    *,
    admission_status: str,
    capability_result: PlatformCapabilityLookupResult | None,
    ambiguity_count: int,
) -> str:
    if admission_status == "unsupported":
        return "unsupported"
    if ambiguity_count > 0:
        return "ambiguous"
    if admission_status == "needs_review":
        return "needs_review"
    if capability_result and capability_result.review_required:
        return "needs_review"
    return "candidate"


def _ambiguity_count(reference: KnowledgeAcquisitionInputReference) -> int:
    count = 0
    if not reference.educational_identity_id:
        count += 1
    if not reference.educational_context_summary:
        count += 1
    return count


def _normalized_content(reference: KnowledgeAcquisitionInputReference) -> dict[str, Any]:
    text = reference.supplied_extracted_text
    return {
        "has_extracted_text": bool(text),
        "extracted_text_sha256": content_hash(text),
        "extracted_text_length": len(text) if text else 0,
        "source_type": reference.source_type,
        "artifact_type": reference.artifact_type,
    }


def _infer_modality(source_type: str) -> KnowledgeAcquisitionModality:
    if source_type in {"pdf", "worksheet", "answer_key", "lesson_plan"}:
        return "document"
    if source_type in {"ocr_text", "teacher_note"}:
        return "text"
    if source_type == "image":
        return "image"
    if source_type == "voice":
        return "audio"
    if source_type == "student_work":
        return "mixed"
    return "unknown"


def _capability_input_type(reference: KnowledgeAcquisitionInputReference) -> str | None:
    configured = reference.metadata.get("capability_input_type")
    if configured:
        return str(configured)
    if reference.source_type == "ocr_text":
        return "printed_text"
    return reference.source_type


def _string_or_none(value: object) -> str | None:
    if value is None:
        return None
    return str(value)
