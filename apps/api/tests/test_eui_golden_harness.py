"""EUI Golden Harness - Educational Identity deterministic ID cases."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.modules.eui.schemas.aei_consumer_migration import (
    AEIConsumerMigrationComparison,
    AEIConsumerMigrationDifference,
)
from app.modules.eui.schemas.aei_source_readiness import (
    AEISourceReadinessDimensionResult,
    AEISourceReadinessScorecard,
)
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
from app.modules.eui.services.aei_consumer_migration import (
    AEIConsumerMigrationAdapter,
)
from app.modules.eui.services.aei_consumer_migration_evidence import (
    AEIConsumerMigrationEvidenceBinder,
)
from app.modules.eui.services.aei_divergence_readiness import (
    AEIDivergenceReadinessReviewService,
)
from app.modules.eui.services.aei_source_readiness_candidate import (
    AEISourceReadinessCandidateService,
)
from app.modules.eui.services.aei_source_readiness_trial import (
    AEISourceReadinessTrialService,
)
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


def test_eui_aei_consumer_migration_golden_harness_cases_are_deterministic():
    payload = json.loads(
        (GOLDEN_DIR / "aei_consumer_migration_cases.json").read_text(encoding="utf-8")
    )

    assert payload["version"] == "eui-aei-consumer-migration-golden-v1"
    assert payload["authorization"] == "EUI-PH7A-AEI-DUAL-READ-AUTH-001"
    case_ids = [case["id"] for case in payload["cases"]]
    assert len(case_ids) == len(set(case_ids))

    tenant_id = uuid.UUID(payload["tenant_id"])
    adapter = AEIConsumerMigrationAdapter()
    comparison_ids: set[str] = set()
    for case in payload["cases"]:
        comparison = adapter.build_comparison(
            tenant_id=tenant_id,
            subject_type=case["subject_type"],
            subject_ref=case["subject_ref"],
            legacy_summary=case["legacy_summary"],
            eui_summary=case["eui_summary"],
        )
        comparison_again = adapter.build_comparison(
            tenant_id=tenant_id,
            subject_type=case["subject_type"],
            subject_ref=case["subject_ref"],
            legacy_summary=case["legacy_summary"],
            eui_summary=case["eui_summary"],
        )
        expected = case["expected"]

        assert comparison.id == comparison_again.id, case["id"]
        assert comparison.id.startswith("eui-aei-migration://"), case["id"]
        comparison_ids.add(comparison.id)
        assert sorted(comparison.difference_types) == sorted(
            expected["difference_types"]
        ), case["id"]
        assert comparison.has_blockers is expected["has_blockers"], case["id"]
        assert _migration_capture_status(comparison) == expected["status"], case["id"]
        assert comparison.authoritative is False, case["id"]
        assert comparison.source_switch_active is False, case["id"]

    assert len(comparison_ids) == len(payload["cases"])


@pytest.mark.asyncio
async def test_eui_aei_rich_evidence_golden_harness_cases_are_deterministic():
    payload = json.loads(
        (GOLDEN_DIR / "aei_rich_evidence_binding_cases.json").read_text(
            encoding="utf-8"
        )
    )

    assert payload["version"] == "eui-aei-rich-evidence-golden-v1"
    assert payload["authorization"] == "EUI-PH7B-AEI-RICH-EVIDENCE-AUTH-001"
    case_ids = [case["id"] for case in payload["cases"]]
    assert len(case_ids) == len(set(case_ids))

    tenant_id = uuid.UUID(payload["tenant_id"])
    binder = AEIConsumerMigrationEvidenceBinder()
    bundle_ids: set[tuple[str, str, str]] = set()
    for case in payload["cases"]:
        result = await binder.bind(
            enabled=True,
            db=None,
            tenant_id=tenant_id,
            subject_type=case["subject_type"],
            subject_ref=case["subject_ref"],
            artifact_id=uuid.uuid5(uuid.NAMESPACE_URL, case["subject_ref"]),
            exam=_exam_from_case(case.get("exam")),
            question_paper=_paper_from_case(case.get("question_paper")),
        )
        result_again = await binder.bind(
            enabled=True,
            db=None,
            tenant_id=tenant_id,
            subject_type=case["subject_type"],
            subject_ref=case["subject_ref"],
            artifact_id=uuid.uuid5(uuid.NAMESPACE_URL, case["subject_ref"]),
            exam=_exam_from_case(case.get("exam")),
            question_paper=_paper_from_case(case.get("question_paper")),
        )
        assert result is not None, case["id"]
        assert result_again is not None, case["id"]
        bundle = result.bundle
        bundle_again = result_again.bundle
        expected = case["expected"]

        assert bundle.status == expected["status"], case["id"]
        assert bundle.context_status == expected["context_status"], case["id"]
        assert bundle.capability_mode == expected["capability_mode"], case["id"]
        assert bundle.capability_matched is expected["capability_matched"], case["id"]
        assert sorted(bundle.missing_evidence) == sorted(
            expected["missing_evidence"]
        ), case["id"]
        assert sorted(bundle.ambiguous_evidence) == sorted(
            expected["ambiguous_evidence"]
        ), case["id"]
        assert bundle.trust_consumer_visibility == expected[
            "trust_consumer_visibility"
        ], case["id"]
        assert bundle.authoritative is False, case["id"]
        assert bundle.query_budget["per_question_db_traversal"] is False, case["id"]
        assert bundle.model_copy(update={"duration_ms": 0.0}) == bundle_again.model_copy(
            update={"duration_ms": 0.0}
        ), case["id"]
        bundle_ids.add((case["subject_ref"], bundle.status, str(bundle.capability_mode)))

    assert len(bundle_ids) == len(payload["cases"])


def test_eui_aei_divergence_readiness_golden_harness_cases_are_deterministic():
    payload = json.loads(
        (GOLDEN_DIR / "aei_divergence_readiness_cases.json").read_text(
            encoding="utf-8"
        )
    )

    assert payload["version"] == "eui-aei-divergence-readiness-golden-v1"
    assert payload["authorization"] == "EUI-PH7C-AEI-DIVERGENCE-READINESS-AUTH-001"
    case_ids = [case["id"] for case in payload["cases"]]
    assert len(case_ids) == len(set(case_ids))

    tenant_id = uuid.UUID(payload["tenant_id"])
    service = AEIDivergenceReadinessReviewService()
    scorecard_ids: set[str] = set()
    for case in payload["cases"]:
        comparisons = tuple(
            _readiness_comparison_from_case(tenant_id, comparison)
            for comparison in case["comparisons"]
        )
        scorecard = service.review(
            tenant_id=tenant_id,
            subject_type=case["subject_type"],
            scope_ref=case["scope_ref"],
            comparisons=comparisons,
        )
        scorecard_again = service.review(
            tenant_id=tenant_id,
            subject_type=case["subject_type"],
            scope_ref=case["scope_ref"],
            comparisons=comparisons,
        )
        expected = case["expected"]

        assert scorecard.id == scorecard_again.id, case["id"]
        assert scorecard.id.startswith("eui-aei-readiness://"), case["id"]
        scorecard_ids.add(scorecard.id)
        assert scorecard.review_posture == expected["review_posture"], case["id"]
        assert scorecard.eligible is expected["eligible"], case["id"]
        assert sorted(scorecard.blocker_categories) == sorted(
            expected["blocker_categories"]
        ), case["id"]
        assert scorecard.authoritative is False, case["id"]
        assert scorecard.internal_only is True, case["id"]
        assert scorecard.source_switch_active is False, case["id"]

    assert len(scorecard_ids) == len(payload["cases"])


def test_eui_aei_source_readiness_candidate_golden_harness_cases_are_deterministic():
    payload = json.loads(
        (GOLDEN_DIR / "aei_source_readiness_candidate_cases.json").read_text(
            encoding="utf-8"
        )
    )

    assert payload["version"] == "eui-aei-source-readiness-candidate-golden-v1"
    assert payload["authorization"] == "EUI-PH7D-NARROW-AEI-SOURCE-READINESS-AUTH-001"
    case_ids = [case["id"] for case in payload["cases"]]
    assert len(case_ids) == len(set(case_ids))

    tenant_id = uuid.UUID(payload["tenant_id"])
    service = AEISourceReadinessCandidateService()
    candidate_ids: set[str] = set()
    for case in payload["cases"]:
        scorecard = _source_readiness_scorecard_from_case(
            tenant_id,
            case["subject_type"],
            case["scope_ref"],
            case["scorecard"],
        )
        candidate = service.build(
            scorecard=scorecard,
            candidate_scope=case.get("candidate_scope", "context_metadata_only"),
            source_switch_requested=case.get("source_switch_requested", False),
        )
        candidate_again = service.build(
            scorecard=scorecard,
            candidate_scope=case.get("candidate_scope", "context_metadata_only"),
            source_switch_requested=case.get("source_switch_requested", False),
        )
        expected = case["expected"]

        assert candidate.id == candidate_again.id, case["id"]
        assert candidate.id.startswith("eui-aei-source-candidate://"), case["id"]
        candidate_ids.add(candidate.id)
        assert candidate.candidate_state == expected["candidate_state"], case["id"]
        assert candidate.ready_for_internal_trial is expected[
            "ready_for_internal_trial"
        ], case["id"]
        assert sorted(candidate.blocked_evidence_classes) == sorted(
            expected["blocked_evidence_classes"]
        ), case["id"]
        assert candidate.source_switch_active is expected["source_switch_active"], case["id"]
        assert candidate.authoritative is False, case["id"]
        assert candidate.internal_only is True, case["id"]
        assert candidate.metadata["raw_content_captured"] is False, case["id"]

    assert len(candidate_ids) == len(payload["cases"])


def test_eui_aei_source_readiness_trial_golden_harness_cases_are_deterministic():
    payload = json.loads(
        (GOLDEN_DIR / "aei_source_readiness_trial_cases.json").read_text(
            encoding="utf-8"
        )
    )

    assert payload["version"] == "eui-aei-source-readiness-trial-golden-v1"
    assert (
        payload["authorization"]
        == "EUI-PH7E-NARROW-AEI-SOURCE-READINESS-TRIAL-AUTH-001"
    )
    case_ids = [case["id"] for case in payload["cases"]]
    assert len(case_ids) == len(set(case_ids))

    tenant_id = uuid.UUID(payload["tenant_id"])
    candidate_service = AEISourceReadinessCandidateService()
    trial_service = AEISourceReadinessTrialService()
    trial_ids: set[str] = set()
    for case in payload["cases"]:
        candidate_payload = case.get("candidate")
        candidate = None
        if candidate_payload is not None:
            scorecard = _source_readiness_scorecard_from_case(
                tenant_id,
                case["subject_type"],
                case["scope_ref"],
                candidate_payload["scorecard"],
            )
            candidate = candidate_service.build(
                scorecard=scorecard,
                candidate_scope=candidate_payload.get(
                    "candidate_scope", "context_metadata_only"
                ),
                source_switch_requested=case.get("source_switch_requested", False),
            )

        result = trial_service.build(
            candidate=candidate,
            tenant_id=tenant_id,
            subject_type=case["subject_type"],
            scope_ref=case["scope_ref"],
            source_switch_requested=case.get("source_switch_requested", False),
            legacy_source_of_truth_confirmed=case.get(
                "legacy_source_of_truth_confirmed", True
            ),
            trial_enabled=case.get("trial_enabled", True),
        )
        result_again = trial_service.build(
            candidate=candidate,
            tenant_id=tenant_id,
            subject_type=case["subject_type"],
            scope_ref=case["scope_ref"],
            source_switch_requested=case.get("source_switch_requested", False),
            legacy_source_of_truth_confirmed=case.get(
                "legacy_source_of_truth_confirmed", True
            ),
            trial_enabled=case.get("trial_enabled", True),
        )
        expected = case["expected"]

        assert result.id == result_again.id, case["id"]
        assert result.id.startswith("eui-aei-source-trial://"), case["id"]
        trial_ids.add(result.id)
        assert result.trial_state == expected["trial_state"], case["id"]
        assert result.trial_ready is expected["trial_ready"], case["id"]
        assert sorted(result.selected_evidence_classes) == sorted(
            expected["selected_evidence_classes"]
        ), case["id"]
        assert sorted(result.blocked_evidence_classes) == sorted(
            expected["blocked_evidence_classes"]
        ), case["id"]
        assert result.source_switch_active is expected["source_switch_active"], case["id"]
        assert result.authoritative is False, case["id"]
        assert result.internal_only is True, case["id"]
        assert result.metadata["raw_content_captured"] is False, case["id"]

    assert len(trial_ids) == len(payload["cases"])


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


def _migration_capture_status(comparison) -> str:  # noqa: ANN001
    if any(difference.difference_type == "unsafe" for difference in comparison.differences):
        return "unsafe_difference"
    if comparison.difference_types != ("equivalent",):
        return "diverged"
    return "completed"


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


def _paper_from_case(payload: dict | None):
    if payload is None:
        return None
    return SimpleNamespace(**payload)


def _exam_from_case(payload: dict | None):
    if payload is None:
        return None
    exam_type = payload.get("exam_type")
    return SimpleNamespace(
        exam_type=SimpleNamespace(value=exam_type) if exam_type else None,
        topic=payload.get("topic"),
        source_paper_id=None,
    )


def _readiness_comparison_from_case(
    tenant_id: uuid.UUID,
    payload: dict,
) -> AEIConsumerMigrationComparison:
    complete_evidence = payload.get("complete_evidence", True)
    trust_visibility = payload.get("trust_consumer_visibility", "internal_only")
    capability_mode = payload.get("capability_mode")
    difference_type = payload["difference_type"]
    return AEIConsumerMigrationComparison(
        id=payload["id"],
        tenant_id=tenant_id,
        subject_type="answer_sheet_evaluation",
        subject_ref=payload["id"].rsplit("/", 1)[-1],
        eui_summary={
            "available": complete_evidence,
            "rich_evidence_available": complete_evidence,
            "query_budget": {"per_question_db_traversal": False},
        },
        differences=(
            AEIConsumerMigrationDifference(
                difference_type=difference_type,
                reason=f"{difference_type}_golden_case",
                blocker=difference_type in {"product_impacting", "unsafe"},
            ),
        ),
        eui_identity_present=complete_evidence,
        eui_context_present=complete_evidence,
        capability_mode=capability_mode if complete_evidence else None,
        trust_posture="trusted" if complete_evidence else None,
        trust_consumer_visibility=trust_visibility if complete_evidence else None,
    )


def _source_readiness_scorecard_from_case(
    tenant_id: uuid.UUID,
    subject_type: str,
    scope_ref: str,
    payload: dict,
) -> AEISourceReadinessScorecard:
    review_posture = payload["review_posture"]
    eligible = payload["eligible"]
    dimensions = tuple(
        AEISourceReadinessDimensionResult(
            dimension=dimension["dimension"],
            status=dimension["status"],
            reason=f"{dimension['dimension']}_{dimension['status']}_golden_case",
            blocker=str(dimension["status"]).startswith("blocked"),
        )
        for dimension in payload.get("dimensions", ())
    )
    return AEISourceReadinessScorecard(
        id=f"eui-aei-readiness://answer-sheet-evaluation/{scope_ref.rsplit(':', 1)[-1]}",
        tenant_id=tenant_id,
        subject_type=subject_type,  # type: ignore[arg-type]
        scope_ref=scope_ref,
        review_posture=review_posture,  # type: ignore[arg-type]
        eligible=eligible,
        evidence_window_required=2,
        evidence_window_count=2 if eligible else 1,
        reviewed_comparison_ids=("comparison-a", "comparison-b") if eligible else (),
        dimensions=dimensions,
        blocker_categories=tuple(payload.get("blocker_categories", ())),
        source_flag_enabled=payload.get("source_flag_enabled", False),
    )
