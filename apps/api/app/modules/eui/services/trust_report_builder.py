"""Deterministic Trust Report builder for EUI Phase 6."""

from __future__ import annotations

import uuid
from typing import Any

from app.modules.eui.schemas.educational_context import EducationalContext
from app.modules.eui.schemas.educational_graph import EducationalGraphRelationshipProposal
from app.modules.eui.schemas.knowledge_acquisition import EducationalArtifactCandidate
from app.modules.eui.schemas.platform_capability import (
    CapabilityMode,
    PlatformCapabilityLookupResult,
)
from app.modules.eui.schemas.trust_report import (
    TrustDimension,
    TrustDimensionKey,
    TrustProvenanceReference,
    TrustReport,
    TrustSubjectType,
    TrustWarning,
)
from app.modules.eui.services.trust_report_id import stable_trust_report_id
from app.modules.eui.services.trust_report_policy import (
    collect_dimension_warnings,
    derive_overall_posture,
)


class TrustReportBuilder:
    """Build passive Trust Reports from EUI-owned subject types."""

    def build_for_context(self, context: EducationalContext) -> TrustReport:
        dimensions = {
            "understanding_confidence": _context_understanding_dimension(context),
            "auditability": _context_auditability_dimension(context),
            "evidence_availability": _evidence_dimension(
                bool(context.educational_identity_id or context.curriculum_pack_id),
                reason="context_identity_or_pack_reference",
            ),
            "human_review_status": _human_review_dimension(
                review_required=bool(context.conflicts or context.ambiguities),
                reason="context_conflict_or_ambiguity",
            ),
            "capability_mode": _not_applicable("capability mode is not a context signal"),
            "input_quality": _not_applicable("input quality belongs to acquisition inputs"),
            "extraction_quality": _not_applicable("extraction quality belongs to KAI"),
            "ocr_confidence": _not_applicable("OCR confidence is not a context signal"),
            "language_confidence": _not_applicable("language confidence is not provided"),
            "subject_confidence": _not_applicable("subject confidence is capability-scoped"),
            "reasoning_confidence": _not_applicable("reasoning is not part of Phase 6"),
            "policy_confidence": _not_applicable("policy is not part of Phase 6"),
        }
        review_required = bool(context.conflicts or context.ambiguities)
        return self._report(
            tenant_id=context.tenant_id,
            subject_type="educational_context",
            subject_ref=context.educational_identity_id
            or _string_or_unknown(context.curriculum_pack_id)
            or "context",
            dimensions=dimensions,
            review_required=review_required,
            evidence_available=bool(context.educational_identity_id or context.curriculum_pack_id),
            provenance_refs=(
                TrustProvenanceReference(
                    source=context.provenance.source,
                    source_id=context.provenance.source_id,
                    source_version=context.provenance.source_version,
                    subject_ref=context.educational_identity_id,
                    metadata={"resolved_from": context.provenance.resolved_from},
                ),
            ),
        )

    def build_for_capability_lookup(
        self,
        result: PlatformCapabilityLookupResult,
        *,
        tenant_id: uuid.UUID,
    ) -> TrustReport:
        dimensions = {
            "capability_mode": _capability_dimension(result.mode, matched=result.matched),
            "subject_confidence": _capability_subject_dimension(result),
            "human_review_status": _human_review_dimension(
                review_required=result.review_required,
                reason="capability_review_required",
            ),
            "auditability": _audit_dimension(
                strong=result.authoritative and result.matched,
                reason="capability_registry_lookup",
            ),
            "evidence_availability": _evidence_dimension(
                result.declaration is not None,
                reason="capability_declaration_available",
            ),
            "input_quality": _not_applicable("input quality belongs to acquisition inputs"),
            "extraction_quality": _not_applicable("extraction quality belongs to KAI"),
            "ocr_confidence": _not_applicable("OCR confidence is not a capability signal"),
            "language_confidence": _not_applicable("language confidence is not provided"),
            "understanding_confidence": _not_applicable("understanding is not provided"),
            "reasoning_confidence": _not_applicable("reasoning is not part of Phase 6"),
            "policy_confidence": _not_applicable("policy is not part of Phase 6"),
        }
        return self._report(
            tenant_id=tenant_id,
            subject_type="platform_capability_lookup",
            subject_ref=f"{result.request.domain}:{result.request.capability_key}",
            dimensions=dimensions,
            review_required=result.review_required,
            evidence_available=result.declaration is not None,
            capability_mode=result.mode,
            provenance_refs=(
                TrustProvenanceReference(
                    source="platform_capability_registry",
                    source_id=result.declaration.id if result.declaration else None,
                    source_version=result.registry_version,
                    subject_ref=f"{result.request.domain}:{result.request.capability_key}",
                    metadata={"matched": result.matched, "conflict": result.conflict},
                ),
            ),
        )

    def build_for_kai_candidate(
        self,
        candidate: EducationalArtifactCandidate,
    ) -> TrustReport:
        dimensions = {
            "input_quality": _input_quality_dimension(candidate),
            "extraction_quality": _extraction_dimension(candidate),
            "ocr_confidence": _ocr_dimension(candidate),
            "language_confidence": _confidence_dimension(
                candidate.trust_signals.language_confidence,
                reason="kai_language_confidence",
                applicable=bool(candidate.detected_language or candidate.detected_script),
            ),
            "understanding_confidence": _candidate_understanding_dimension(candidate),
            "subject_confidence": _candidate_subject_dimension(candidate),
            "capability_mode": _capability_mode_dimension(candidate.capability_mode),
            "human_review_status": _human_review_dimension(
                review_required=candidate.trust_signals.review_required
                or candidate.review_status != "candidate",
                reason=f"candidate_review_status:{candidate.review_status}",
            ),
            "evidence_availability": _evidence_dimension(
                bool(candidate.educational_identity_id),
                reason="candidate_identity_reference",
            ),
            "auditability": _audit_dimension(
                strong=bool(candidate.provenance.source),
                reason="candidate_provenance",
            ),
            "reasoning_confidence": _not_applicable("reasoning is not part of KAI"),
            "policy_confidence": _not_applicable("policy is not part of KAI"),
        }
        review_required = (
            candidate.trust_signals.review_required
            or candidate.review_status != "candidate"
        )
        return self._report(
            tenant_id=candidate.tenant_id,
            subject_type="kai_candidate",
            subject_ref=candidate.id,
            dimensions=dimensions,
            review_required=review_required,
            evidence_available=bool(candidate.educational_identity_id),
            capability_mode=candidate.capability_mode,
            provenance_refs=(
                TrustProvenanceReference(
                    source=candidate.provenance.source,
                    source_id=candidate.provenance.source_reference,
                    source_version=candidate.provenance.source_version,
                    subject_ref=candidate.id,
                    metadata={
                        "checksum": candidate.provenance.checksum,
                        "page_number": candidate.provenance.page_number,
                    },
                ),
            ),
        )

    def build_for_ekg_proposal(
        self,
        proposal: EducationalGraphRelationshipProposal,
    ) -> TrustReport:
        dimensions = {
            "evidence_availability": _evidence_dimension(
                proposal.status == "proposed",
                reason=f"ekg_proposal_status:{proposal.status}",
            ),
            "auditability": _audit_dimension(
                strong=bool(proposal.provenance.source),
                reason="ekg_proposal_provenance",
            ),
            "understanding_confidence": _ekg_understanding_dimension(proposal),
            "capability_mode": _capability_mode_dimension(proposal.capability_mode),
            "human_review_status": _human_review_dimension(
                review_required=True,
                reason=f"proposal_authority_posture:{proposal.authority_posture}",
            ),
            "input_quality": _not_applicable("input quality belongs to acquisition inputs"),
            "extraction_quality": _not_applicable("extraction quality belongs to KAI"),
            "ocr_confidence": _not_applicable("OCR confidence is not an EKG signal"),
            "language_confidence": _not_applicable("language confidence is not provided"),
            "subject_confidence": _not_applicable("subject confidence is capability-scoped"),
            "reasoning_confidence": _not_applicable("reasoning is not part of Phase 6"),
            "policy_confidence": _not_applicable("policy is not part of Phase 6"),
        }
        return self._report(
            tenant_id=proposal.tenant_id,
            subject_type="ekg_relationship_proposal",
            subject_ref=proposal.id,
            dimensions=dimensions,
            review_required=True,
            evidence_available=proposal.status == "proposed",
            capability_mode=proposal.capability_mode,
            provenance_refs=(
                TrustProvenanceReference(
                    source=proposal.provenance.source,
                    source_id=proposal.provenance.source_id,
                    source_version=proposal.provenance.source_version,
                    subject_ref=proposal.id,
                    metadata={"relationship_source": proposal.provenance.relationship_source},
                ),
            ),
        )

    def _report(
        self,
        *,
        tenant_id: uuid.UUID,
        subject_type: TrustSubjectType,
        subject_ref: str,
        dimensions: dict[TrustDimensionKey, TrustDimension],
        review_required: bool,
        evidence_available: bool,
        capability_mode: CapabilityMode | None = None,
        provenance_refs: tuple[TrustProvenanceReference, ...] = (),
    ) -> TrustReport:
        overall = derive_overall_posture(dimensions, review_required=review_required)
        warnings = collect_dimension_warnings(dimensions)
        payload = {
            "overall_posture": overall,
            "dimensions": {
                key: dimension.model_dump(mode="json", exclude_none=True)
                for key, dimension in dimensions.items()
            },
            "review_required": review_required,
            "evidence_available": evidence_available,
            "capability_mode": capability_mode,
        }
        return TrustReport(
            id=stable_trust_report_id(
                subject_type=subject_type,
                subject_ref=subject_ref,
                payload=payload,
            ),
            tenant_id=tenant_id,
            subject_type=subject_type,
            subject_ref=subject_ref,
            overall_posture=overall,
            dimensions=dimensions,
            review_required=review_required,
            evidence_available=evidence_available,
            capability_mode=capability_mode,
            consumer_visibility="internal_only",
            provenance_refs=provenance_refs,
            warnings=warnings,
            metadata={
                "authorization": "EUI-PH6-TRUST-AUTH-001",
                "passive": True,
                "report_only": True,
                "runtime_authoritative": False,
            },
        )


def _context_understanding_dimension(context: EducationalContext) -> TrustDimension:
    if context.ambiguities:
        return TrustDimension(
            status="weak",
            reason="context_has_ambiguities",
            warnings=(
                TrustWarning(
                    code="context_ambiguous",
                    severity="warning",
                    message="Educational Context has unresolved ambiguity.",
                ),
            ),
            metadata={"ambiguity_count": len(context.ambiguities)},
        )
    if context.conflicts:
        return TrustDimension(
            status="partial",
            reason="context_has_conflicts",
            warnings=(
                TrustWarning(
                    code="context_conflict",
                    severity="warning",
                    message="Educational Context has precedence conflicts.",
                ),
            ),
            metadata={"conflict_count": len(context.conflicts)},
        )
    return TrustDimension(status="strong", reason="context_resolved")


def _context_auditability_dimension(context: EducationalContext) -> TrustDimension:
    if context.field_sources and context.provenance.source:
        return TrustDimension(status="strong", reason="context_field_sources_available")
    return TrustDimension(status="partial", reason="context_audit_metadata_partial")


def _input_quality_dimension(candidate: EducationalArtifactCandidate) -> TrustDimension:
    quality = candidate.trust_signals.input_quality
    if candidate.source_admission_status == "unsupported":
        return TrustDimension(status="unsupported", reason="source_not_admitted")
    if quality is None:
        return TrustDimension(status="missing", reason="input_quality_missing")
    if quality in {"good", "high", "clear"}:
        return TrustDimension(status="strong", reason=f"input_quality:{quality}")
    if quality in {"low", "poor", "unclear"}:
        return TrustDimension(status="weak", reason=f"input_quality:{quality}")
    return TrustDimension(status="partial", reason=f"input_quality:{quality}")


def _extraction_dimension(candidate: EducationalArtifactCandidate) -> TrustDimension:
    if candidate.extraction_status == "unsupported":
        return TrustDimension(status="unsupported", reason="extraction_unsupported")
    confidence = candidate.trust_signals.extraction_confidence
    if confidence is not None:
        return _confidence_dimension(confidence, reason="kai_extraction_confidence")
    if candidate.extraction_status == "supplied":
        return TrustDimension(status="partial", reason="extraction_supplied_without_confidence")
    if candidate.extraction_status == "partial":
        return TrustDimension(status="weak", reason="extraction_partial")
    return TrustDimension(status="missing", reason="extraction_not_attempted")


def _ocr_dimension(candidate: EducationalArtifactCandidate) -> TrustDimension:
    applicable = candidate.source_type == "ocr_text"
    return _confidence_dimension(
        candidate.trust_signals.extraction_confidence,
        reason="ocr_confidence",
        applicable=applicable,
    )


def _candidate_understanding_dimension(candidate: EducationalArtifactCandidate) -> TrustDimension:
    if candidate.review_status == "unsupported":
        return TrustDimension(status="unsupported", reason="candidate_unsupported")
    if candidate.review_status == "ambiguous":
        return TrustDimension(status="weak", reason="candidate_ambiguous")
    if candidate.trust_signals.ambiguity_count > 0:
        return TrustDimension(
            status="weak",
            reason="candidate_has_ambiguity_signals",
            metadata={"ambiguity_count": candidate.trust_signals.ambiguity_count},
        )
    return TrustDimension(status="partial", reason="candidate_not_authoritative")


def _candidate_subject_dimension(candidate: EducationalArtifactCandidate) -> TrustDimension:
    if candidate.capability_mode == "unsupported":
        return TrustDimension(status="unsupported", reason="capability_unsupported")
    if candidate.capability_mode in {"assist", "checklist", "manual_review", "expansion"}:
        return TrustDimension(
            status="partial",
            reason=f"capability_mode:{candidate.capability_mode}",
        )
    if candidate.capability_mode == "supported" and candidate.capability_matched:
        return TrustDimension(status="strong", reason="capability_supported")
    if candidate.capability_mode is None:
        return TrustDimension(status="missing", reason="capability_not_looked_up")
    return TrustDimension(status="partial", reason=f"capability_mode:{candidate.capability_mode}")


def _capability_dimension(mode: str, *, matched: bool) -> TrustDimension:
    if mode == "unsupported":
        return TrustDimension(status="unsupported", reason="capability_unsupported")
    if mode in {"manual_review", "expansion"}:
        return TrustDimension(status="weak", reason=f"capability_mode:{mode}")
    if mode in {"assist", "checklist"}:
        return TrustDimension(status="partial", reason=f"capability_mode:{mode}")
    if mode == "supported" and matched:
        return TrustDimension(status="strong", reason="capability_supported")
    return TrustDimension(status="missing", reason="capability_not_matched")


def _capability_subject_dimension(result: PlatformCapabilityLookupResult) -> TrustDimension:
    if result.conflict:
        return TrustDimension(status="weak", reason="capability_conflict")
    return _capability_dimension(result.mode, matched=result.matched)


def _capability_mode_dimension(mode: str | None) -> TrustDimension:
    if mode is None:
        return TrustDimension(status="missing", reason="capability_mode_missing")
    return _capability_dimension(mode, matched=True)


def _ekg_understanding_dimension(proposal) -> TrustDimension:
    if proposal.status == "unsupported":
        return TrustDimension(status="unsupported", reason="ekg_proposal_unsupported")
    if proposal.status == "ambiguous":
        return TrustDimension(status="weak", reason="ekg_proposal_ambiguous")
    if proposal.status == "missing_target":
        return TrustDimension(status="missing", reason="ekg_target_missing")
    return TrustDimension(status="partial", reason="ekg_proposal_candidate_only")


def _confidence_dimension(
    confidence: float | None,
    *,
    reason: str,
    applicable: bool = True,
) -> TrustDimension:
    if not applicable:
        return _not_applicable(f"{reason}:not_applicable")
    if confidence is None:
        return TrustDimension(status="missing", reason=f"{reason}:missing")
    if confidence >= 0.9:
        return TrustDimension(status="strong", score=confidence, reason=reason)
    if confidence >= 0.7:
        return TrustDimension(status="partial", score=confidence, reason=reason)
    return TrustDimension(status="weak", score=confidence, reason=reason)


def _human_review_dimension(*, review_required: bool, reason: str) -> TrustDimension:
    if review_required:
        return TrustDimension(
            status="weak",
            reason=reason,
            warnings=(
                TrustWarning(
                    code="manual_review_required",
                    severity="blocker",
                    message="Human review is required before authoritative use.",
                ),
            ),
        )
    return TrustDimension(status="strong", reason="no_manual_review_signal")


def _evidence_dimension(available: bool, *, reason: str) -> TrustDimension:
    if available:
        return TrustDimension(status="strong", reason=reason)
    return TrustDimension(status="missing", reason=f"{reason}:missing")


def _audit_dimension(*, strong: bool, reason: str) -> TrustDimension:
    if strong:
        return TrustDimension(status="strong", reason=reason)
    return TrustDimension(status="partial", reason=f"{reason}:partial")


def _not_applicable(reason: str) -> TrustDimension:
    return TrustDimension(status="not_applicable", reason=reason)


def _string_or_unknown(value: Any) -> str:
    if value is None:
        return "unknown"
    return str(value)
