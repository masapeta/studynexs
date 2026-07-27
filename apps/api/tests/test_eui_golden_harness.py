"""EUI Golden Harness - Educational Identity deterministic ID cases."""

from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest

from app.modules.eui.schemas.educational_context import (
    EducationalContext,
    EducationalContextAmbiguity,
    EducationalContextConflict,
    EducationalContextProvenance,
    EducationalContextReference,
)
from app.modules.eui.schemas.educational_graph import (
    EducationalGraphReference,
    EducationalGraphRelationshipReference,
)
from app.modules.eui.schemas.educational_identity import (
    EducationalIdentity,
    EducationalIdentityProvenance,
)
from app.modules.eui.schemas.knowledge_acquisition import KnowledgeAcquisitionInputReference
from app.modules.eui.schemas.platform_capability import PlatformCapabilityLookupRequest
from app.modules.eui.services.educational_context_resolver import EducationalContextResolver
from app.modules.eui.services.educational_graph_resolver import (
    EducationalGraphProposalResolver,
)
from app.modules.eui.services.educational_identity_id import stable_identity_id
from app.modules.eui.services.knowledge_acquisition_builder import (
    KnowledgeAcquisitionCandidateBuilder,
)
from app.modules.eui.services.platform_capability_lookup import PlatformCapabilityLookupService
from app.modules.eui.services.trust_report_builder import TrustReportBuilder

GOLDEN_DIR = Path(__file__).parent / "golden" / "eui_v1"


def test_eui_identity_golden_harness_cases_are_deterministic_and_unique():
    payload = json.loads((GOLDEN_DIR / "educational_identity_cases.json").read_text())

    assert payload["version"] == "eui-identity-golden-v1"
    assert payload["authorization"] == "EUI-PH1-AUTH-001"
    case_ids = [case["id"] for case in payload["cases"]]
    assert len(case_ids) == len(set(case_ids))

    expected_ids: set[str] = set()
    for case in payload["cases"]:
        actual = stable_identity_id(**case["input"])
        assert actual == case["expected_id"], case["id"]
        expected_ids.add(case["expected_id"])

    assert len(expected_ids) == len(payload["cases"])


@pytest.mark.asyncio
async def test_eui_context_golden_harness_cases_are_deterministic():
    payload = json.loads((GOLDEN_DIR / "educational_context_cases.json").read_text())

    assert payload["version"] == "eui-context-golden-v1"
    assert payload["authorization"] == "EUI-PH1-SP2-AUTH-001"
    case_ids = [case["id"] for case in payload["cases"]]
    assert len(case_ids) == len(set(case_ids))

    resolver = EducationalContextResolver()
    for case in payload["cases"]:
        school_id = uuid.UUID(case["school_id"])
        identity = _identity_from_case(school_id, case.get("identity"))
        reference = EducationalContextReference(
            school_id=school_id,
            educational_identity=identity,
            **case.get("reference", {}),
        )
        context = await resolver.resolve(reference)
        expected = case["expected"]

        assert context.resolution_status == expected["resolution_status"], case["id"]
        assert len(context.conflicts) == expected["conflict_count"], case["id"]
        assert len(context.ambiguities) == expected["ambiguity_count"], case["id"]
        for field in (
            "grade",
            "subject",
            "assessment_mode",
            "language_medium",
            "evidence_posture",
        ):
            if field in expected:
                assert getattr(context, field) == expected[field], case["id"]


def test_eui_platform_capability_golden_harness_cases_are_deterministic():
    payload = json.loads((GOLDEN_DIR / "platform_capability_registry_cases.json").read_text())

    assert payload["version"] == "eui-platform-capability-golden-v1"
    assert payload["authorization"] == "EUI-PH1-SP3-AUTH-001"
    case_ids = [case["id"] for case in payload["cases"]]
    assert len(case_ids) == len(set(case_ids))

    service = PlatformCapabilityLookupService()
    for case in payload["cases"]:
        result = service.lookup(PlatformCapabilityLookupRequest(**case["request"]))
        expected = case["expected"]

        assert result.mode == expected["mode"], case["id"]
        assert result.matched is expected["matched"], case["id"]
        assert result.conflict is expected["conflict"], case["id"]


def test_eui_kai_golden_harness_cases_are_deterministic():
    payload = json.loads((GOLDEN_DIR / "kai_candidate_cases.json").read_text(encoding="utf-8"))

    assert payload["version"] == "eui-kai-candidate-golden-v1"
    assert payload["authorization"] == "EUI-PH4-KAI-AUTH-001"
    case_ids = [case["id"] for case in payload["cases"]]
    assert len(case_ids) == len(set(case_ids))

    tenant_id = uuid.UUID(payload["tenant_id"])
    builder = KnowledgeAcquisitionCandidateBuilder()
    for case in payload["cases"]:
        candidate = builder.build(
            KnowledgeAcquisitionInputReference(
                tenant_id=tenant_id,
                **case["input"],
            )
        )
        expected = case["expected"]

        assert candidate.source_admission_status == expected["source_admission_status"], case["id"]
        assert candidate.extraction_status == expected["extraction_status"], case["id"]
        assert candidate.review_status == expected["review_status"], case["id"]
        assert candidate.capability_mode == expected["capability_mode"], case["id"]
        assert candidate.capability_matched is expected["capability_matched"], case["id"]
        assert candidate.authoritative is False, case["id"]


def test_eui_ekg_golden_harness_cases_are_deterministic():
    payload = json.loads(
        (GOLDEN_DIR / "ekg_relationship_proposal_cases.json").read_text(encoding="utf-8")
    )

    assert payload["version"] == "eui-ekg-proposal-golden-v1"
    assert payload["authorization"] == "EUI-PH5-EKG-AUTH-001"
    case_ids = [case["id"] for case in payload["cases"]]
    assert len(case_ids) == len(set(case_ids))

    tenant_id = uuid.UUID(payload["tenant_id"])
    resolver = EducationalGraphProposalResolver()
    kai_builder = KnowledgeAcquisitionCandidateBuilder()
    proposal_ids: set[str] = set()
    for case in payload["cases"]:
        reference_payload = case["reference"]
        candidate = None
        if "kai_candidate_input" in reference_payload:
            candidate = kai_builder.build(
                KnowledgeAcquisitionInputReference(
                    tenant_id=tenant_id,
                    **reference_payload["kai_candidate_input"],
                )
            )
        reference = EducationalGraphRelationshipReference(
            tenant_id=tenant_id,
            educational_identity=_identity_from_case(
                tenant_id,
                reference_payload.get("identity"),
            ),
            educational_identity_id=reference_payload.get("educational_identity_id"),
            kai_candidate=candidate,
            candidate_target_references=tuple(
                EducationalGraphReference(**target)
                for target in reference_payload.get("candidate_target_references", ())
            ),
        )
        proposal = resolver.propose(reference)
        proposal_again = resolver.propose(reference)
        expected = case["expected"]

        assert proposal.id == proposal_again.id, case["id"]
        proposal_ids.add(proposal.id)
        assert proposal.relationship_category == expected["relationship_category"], case["id"]
        assert proposal.status == expected["status"], case["id"]
        assert proposal.authority_posture == expected["authority_posture"], case["id"]
        assert proposal.to_reference.reference_type == expected["to_reference_type"], case["id"]
        assert proposal.to_reference.id == expected.get("to_reference_id"), case["id"]
        assert proposal.to_reference.node_type == expected.get("to_node_type"), case["id"]
        assert len(proposal.ambiguities) == expected["ambiguity_count"], case["id"]
        assert proposal.authoritative is False, case["id"]

    assert len(proposal_ids) == len(payload["cases"])


def test_eui_trust_report_golden_harness_cases_are_deterministic():
    payload = json.loads((GOLDEN_DIR / "trust_report_cases.json").read_text(encoding="utf-8"))

    assert payload["version"] == "eui-trust-report-golden-v1"
    assert payload["authorization"] == "EUI-PH6-TRUST-AUTH-001"
    case_ids = [case["id"] for case in payload["cases"]]
    assert len(case_ids) == len(set(case_ids))

    tenant_id = uuid.UUID(payload["tenant_id"])
    trust_builder = TrustReportBuilder()
    kai_builder = KnowledgeAcquisitionCandidateBuilder()
    capability_service = PlatformCapabilityLookupService()
    ekg_resolver = EducationalGraphProposalResolver()
    report_ids: set[str] = set()
    for case in payload["cases"]:
        report = _trust_report_from_case(
            case,
            tenant_id=tenant_id,
            trust_builder=trust_builder,
            kai_builder=kai_builder,
            capability_service=capability_service,
            ekg_resolver=ekg_resolver,
        )
        report_again = _trust_report_from_case(
            case,
            tenant_id=tenant_id,
            trust_builder=trust_builder,
            kai_builder=kai_builder,
            capability_service=capability_service,
            ekg_resolver=ekg_resolver,
        )
        expected = case["expected"]

        assert report.id == report_again.id, case["id"]
        assert report.id.startswith("trust-report://"), case["id"]
        report_ids.add(report.id)
        assert report.subject_type == expected["subject_type"], case["id"]
        assert report.overall_posture == expected["overall_posture"], case["id"]
        assert report.review_required is expected["review_required"], case["id"]
        assert report.consumer_visibility == expected["consumer_visibility"], case["id"]
        assert report.authoritative is expected["authoritative"], case["id"]
        if "capability_mode" in expected:
            assert report.capability_mode == expected["capability_mode"], case["id"]
        if "dimension" in expected:
            dimension = report.dimensions[expected["dimension"]]
            assert dimension.status == expected["dimension_status"], case["id"]
        if "provenance_count" in expected:
            assert len(report.provenance_refs) == expected["provenance_count"], case["id"]

    assert len(report_ids) == len(payload["cases"])


def _trust_report_from_case(
    case: dict,
    *,
    tenant_id: uuid.UUID,
    trust_builder: TrustReportBuilder,
    kai_builder: KnowledgeAcquisitionCandidateBuilder,
    capability_service: PlatformCapabilityLookupService,
    ekg_resolver: EducationalGraphProposalResolver,
):
    kind = case["kind"]
    if kind == "educational_context":
        return trust_builder.build_for_context(
            _educational_context_from_case(tenant_id, case["input"])
        )
    if kind == "platform_capability_lookup":
        result = capability_service.lookup(PlatformCapabilityLookupRequest(**case["request"]))
        return trust_builder.build_for_capability_lookup(result, tenant_id=tenant_id)
    if kind == "kai_candidate":
        candidate = kai_builder.build(
            KnowledgeAcquisitionInputReference(tenant_id=tenant_id, **case["input"])
        )
        return trust_builder.build_for_kai_candidate(candidate)
    if kind == "ekg_relationship_proposal":
        reference_payload = case["reference"]
        proposal = ekg_resolver.propose(
            EducationalGraphRelationshipReference(
                tenant_id=tenant_id,
                educational_identity_id=reference_payload.get("educational_identity_id"),
                candidate_target_references=tuple(
                    EducationalGraphReference(**target)
                    for target in reference_payload.get("candidate_target_references", ())
                ),
            )
        )
        return trust_builder.build_for_ekg_proposal(proposal)
    raise AssertionError(f"Unknown Trust Report golden kind: {kind}")


def _educational_context_from_case(
    tenant_id: uuid.UUID,
    payload: dict,
) -> EducationalContext:
    provenance_payload = payload["provenance"]
    return EducationalContext(
        tenant_id=tenant_id,
        resolution_status=payload["resolution_status"],
        board=payload.get("board"),
        curriculum=payload.get("curriculum"),
        curriculum_version=payload.get("curriculum_version"),
        grade=payload.get("grade"),
        subject=payload.get("subject"),
        educational_identity_id=payload.get("educational_identity_id"),
        field_sources=payload.get("field_sources", {}),
        conflicts=tuple(
            EducationalContextConflict(**conflict)
            for conflict in payload.get("conflicts", ())
        ),
        ambiguities=tuple(
            EducationalContextAmbiguity(**ambiguity)
            for ambiguity in payload.get("ambiguities", ())
        ),
        provenance=EducationalContextProvenance(**provenance_payload),
    )


def _identity_from_case(
    school_id: uuid.UUID,
    payload: dict | None,
) -> EducationalIdentity | None:
    if payload is None:
        return None
    return EducationalIdentity(
        id=payload["id"],
        tenant_id=school_id,
        board=payload["board"],
        curriculum=payload["curriculum"],
        curriculum_version=payload["curriculum_version"],
        grade=payload["grade"],
        subject=payload["subject"],
        chapter=payload.get("chapter"),
        topic=payload.get("topic"),
        concepts=tuple(payload.get("concepts", ())),
        competencies=tuple(payload.get("competencies", ())),
        learning_objectives=tuple(payload.get("learning_objectives", ())),
        language=payload.get("language"),
        metadata=payload.get("metadata", {}),
        provenance=EducationalIdentityProvenance(
            source="golden_harness",
            source_id=payload["id"],
            source_version=payload["curriculum_version"],
            resolved_from="golden_case",
        ),
    )
