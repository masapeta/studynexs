"""EUI Phase 6 - deterministic Trust Report builders."""

from __future__ import annotations

import uuid

from app.modules.eui.schemas.educational_context import (
    EducationalContext,
    EducationalContextAmbiguity,
    EducationalContextConflict,
    EducationalContextProvenance,
)
from app.modules.eui.schemas.educational_graph import (
    EducationalGraphReference,
    EducationalGraphRelationshipReference,
)
from app.modules.eui.schemas.knowledge_acquisition import KnowledgeAcquisitionInputReference
from app.modules.eui.schemas.platform_capability import PlatformCapabilityLookupRequest
from app.modules.eui.services.educational_graph_resolver import EducationalGraphProposalResolver
from app.modules.eui.services.knowledge_acquisition_builder import (
    KnowledgeAcquisitionCandidateBuilder,
)
from app.modules.eui.services.platform_capability_lookup import PlatformCapabilityLookupService
from app.modules.eui.services.trust_report_builder import TrustReportBuilder


def test_builder_maps_resolved_context_to_trusted_internal_report():
    context = _context()

    report = TrustReportBuilder().build_for_context(context)

    assert report.subject_type == "educational_context"
    assert report.overall_posture == "trusted"
    assert report.review_required is False
    assert report.consumer_visibility == "internal_only"
    assert report.authoritative is False
    assert report.provenance_refs[0].source == "context_resolver"


def test_builder_maps_context_ambiguity_to_manual_review_without_authority():
    context = _context(
        ambiguities=(
            EducationalContextAmbiguity(
                reason="multiple_candidate_contexts",
                candidates=("ctx-a", "ctx-b"),
            ),
        )
    )

    report = TrustReportBuilder().build_for_context(context)

    assert report.overall_posture == "manual_review_required"
    assert report.review_required is True
    assert report.dimensions["understanding_confidence"].status == "weak"
    assert {warning.code for warning in report.warnings} == {
        "context_ambiguous",
        "manual_review_required",
    }
    assert report.consumer_visibility == "internal_only"


def test_builder_maps_capability_supported_to_trusted_report():
    result = PlatformCapabilityLookupService().lookup(
        PlatformCapabilityLookupRequest(
            domain="Mathematics",
            capability_key="Numeric Normalization",
            board="CBSE",
            curriculum="NCF2023",
            grade="10",
            subject="Mathematics",
        )
    )

    report = TrustReportBuilder().build_for_capability_lookup(
        result,
        tenant_id=_tenant_id(),
    )

    assert report.overall_posture == "trusted"
    assert report.review_required is False
    assert report.capability_mode == "supported"
    assert report.dimensions["capability_mode"].status == "strong"


def test_builder_maps_unsupported_capability_to_unsupported_even_with_evidence():
    result = PlatformCapabilityLookupService().lookup(
        PlatformCapabilityLookupRequest(
            domain="commerce",
            capability_key="ledger_auto_grading",
            subject="Commerce",
        )
    )

    report = TrustReportBuilder().build_for_capability_lookup(
        result,
        tenant_id=_tenant_id(),
    )

    assert report.overall_posture == "unsupported"
    assert report.review_required is True
    assert report.capability_mode == "unsupported"
    assert report.dimensions["capability_mode"].status == "unsupported"


def test_builder_maps_kai_low_confidence_ocr_to_manual_review_report():
    candidate = KnowledgeAcquisitionCandidateBuilder().build(
        KnowledgeAcquisitionInputReference(
            tenant_id=_tenant_id(),
            source_type="ocr_text",
            artifact_type="worksheet",
            supplied_extracted_text="blurred OCR text",
            detected_language="Hindi",
            detected_script="Devanagari",
            educational_identity_id="ei://cbse/ncf2023/g6/hindi/ch01",
            educational_context_summary={"language": "Hindi", "subject": "Hindi"},
            capability_domain="language",
            capability_key="printed_ocr",
            metadata={"capability_input_type": "printed_text"},
            input_quality="poor",
            extraction_confidence=0.42,
            language_confidence=0.58,
        )
    )

    report = TrustReportBuilder().build_for_kai_candidate(candidate)

    assert report.subject_type == "kai_candidate"
    assert report.overall_posture == "manual_review_required"
    assert report.review_required is True
    assert report.dimensions["ocr_confidence"].status == "weak"
    assert report.dimensions["language_confidence"].status == "weak"
    assert report.provenance_refs[0].source == "kai_phase_4_passive_candidate_builder"
    assert "blurred OCR text" not in report.id
    assert "blurred OCR text" not in str(report.model_dump(mode="json"))


def test_builder_keeps_ekg_proposal_non_authoritative_and_review_required():
    proposal = EducationalGraphProposalResolver().propose(
        EducationalGraphRelationshipReference(
            tenant_id=_tenant_id(),
            educational_identity_id="ei://cbse/ncf2023/g6/science/ch05",
            candidate_target_references=(
                EducationalGraphReference(
                    reference_type="kg_node",
                    id=str(uuid.uuid4()),
                    node_type="concept",
                    label="SI Units",
                ),
            ),
        )
    )

    report = TrustReportBuilder().build_for_ekg_proposal(proposal)

    assert report.subject_type == "ekg_relationship_proposal"
    assert report.overall_posture == "manual_review_required"
    assert report.review_required is True
    assert report.authoritative is False
    assert report.dimensions["human_review_status"].status == "weak"


def test_trust_report_ids_are_deterministic_for_same_subject_and_signals():
    context = _context()
    builder = TrustReportBuilder()

    assert builder.build_for_context(context).id == builder.build_for_context(context).id


def _context(
    *,
    conflicts: tuple[EducationalContextConflict, ...] = (),
    ambiguities: tuple[EducationalContextAmbiguity, ...] = (),
) -> EducationalContext:
    return EducationalContext(
        tenant_id=_tenant_id(),
        resolution_status="ambiguous" if ambiguities else "resolved",
        board="CBSE",
        curriculum="NCF2023",
        curriculum_version="2024",
        grade="6",
        subject="Science",
        educational_identity_id="ei://cbse/ncf2023/g6/science/ch05",
        field_sources={"grade": "educational_identity", "subject": "educational_identity"},
        conflicts=conflicts,
        ambiguities=ambiguities,
        provenance=EducationalContextProvenance(
            source="context_resolver",
            resolved_from="educational_identity",
            source_id="ei://cbse/ncf2023/g6/science/ch05",
            source_version="2024",
        ),
    )


def _tenant_id() -> uuid.UUID:
    return uuid.UUID("11111111-1111-4111-8111-111111111111")
