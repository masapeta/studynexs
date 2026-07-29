"""Assessment Intelligence v1.0 Batch D question-bank reuse readiness tests.

Batch D is intentionally non-runtime. These tests validate only static
question-bank/reuse declarations, Golden Harness cases, and governance posture.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from app.db.models.question_bank import (
    BANK_APPROVAL_STATUSES,
    BANK_STATUS_APPROVED,
    QuestionSource,
)
from app.modules.ai.services.question_bank_service import content_fingerprint

REPO_ROOT = Path(__file__).resolve().parents[3]
DOC_DIR = REPO_ROOT / "docs" / "product" / "assessment-intelligence"
GOLDEN_CASES = (
    Path(__file__).parent
    / "golden"
    / "assessment_intelligence_v1"
    / "question_bank_reuse_readiness_cases.json"
)

DESIGN_BRIEF = (
    DOC_DIR
    / "ASSESSMENT_INTELLIGENCE_V1_BATCH_D_QUESTION_BANK_REUSE_READINESS_DESIGN_BRIEF.md"
)
AUTH_CONTRACT = (
    DOC_DIR
    / (
        "ASSESSMENT_INTELLIGENCE_V1_BATCH_D_QUESTION_BANK_REUSE_READINESS_"
        "IMPLEMENTATION_AUTHORIZATION_CONTRACT.md"
    )
)
DECLARATION_CONTRACT = (
    DOC_DIR / "ASSESSMENT_INTELLIGENCE_V1_BATCH_D_QUESTION_BANK_REUSE_DECLARATION_CONTRACT.md"
)
SCOPE_DECLARATIONS = (
    DOC_DIR / "ASSESSMENT_INTELLIGENCE_V1_QUESTION_BANK_REUSE_SUPPORTED_SCOPE_DECLARATIONS.md"
)

AUTHORIZATION = "ASSESSMENT-V1-BATCH-D-AUTH-001"
ALLOWED_MODES = {"supported", "assist", "manual_review", "unsupported", "expansion"}
SUPPORTED_REUSE_POSTURES = {
    "approved_paper_ingestion",
    "idempotent_reapproval",
    "same_school_reuse",
    "blueprint_slot_compose",
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _golden_payload() -> dict:
    return json.loads(GOLDEN_CASES.read_text(encoding="utf-8"))


def _reuse_ids_from_declarations() -> set[str]:
    return set(
        re.findall(r"`(assessment-bank-reuse://[^`]+)`", _read(SCOPE_DECLARATIONS))
    )


def test_batch_d_artifacts_exist():
    for path in (
        DESIGN_BRIEF,
        AUTH_CONTRACT,
        DECLARATION_CONTRACT,
        SCOPE_DECLARATIONS,
        GOLDEN_CASES,
    ):
        assert path.exists(), path


def test_batch_d_authorization_and_design_are_accepted():
    assert "> Status: Accepted" in _read(DESIGN_BRIEF)
    assert "> Status: Accepted" in _read(AUTH_CONTRACT)
    assert f"> Authorization ID: {AUTHORIZATION}" in _read(AUTH_CONTRACT)
    assert "> Implementation authorization: Authorized for Batch D only" in _read(
        AUTH_CONTRACT
    )
    assert "> Runtime behavior changes: Not authorized" in _read(AUTH_CONTRACT)


def test_declaration_contract_contains_required_fields_and_invariants():
    contract = _read(DECLARATION_CONTRACT)
    required_terms = [
        "`reuse_declaration_id`",
        "`support_mode`",
        "`bank_item_id`",
        "`source_paper_id`",
        "`source_question_bank_item_id`",
        "`school_id`",
        "`class_id`",
        "`subject_id`",
        "`educational_identity_id`",
        "`source`",
        "`approval_status`",
        "`content_fingerprint`",
        "`usage_count`",
        "`used_in_paper_ids`",
        "`answer_context_available`",
        "`blueprint_slot_id`",
        "`marks_match`",
        "`type_match`",
        "`topic_overlap`",
        "`gap_fill_provenance`",
        "`reuse_review_required`",
        "`evaluation_pipeline`",
        "`approved_evidence_required`",
        "`product_claim_allowed`",
        "`runtime_behavior_change`",
        "Previous approval is provenance, not authority",
        "AEI remains the only academic answer-evaluation pipeline",
    ]
    for term in required_terms:
        assert term in contract


def test_scope_declarations_are_explicit_school_private_and_non_marketplace():
    declarations = _read(SCOPE_DECLARATIONS)

    for mode in ALLOWED_MODES:
        assert f"`{mode}`" in declarations

    required_claim_terms = [
        "Product claim allowed | Yes, inside this declared scope only",
        "Product claim allowed | No",
        "must not claim a global, cross-school, marketplace, or universal",
        "automatic approval of reused questions in a new paper",
        "cross-school reuse",
        "global question marketplace",
        "Question-paper generation",
    ]
    for term in required_claim_terms:
        assert term in declarations

    declaration_ids = _reuse_ids_from_declarations()
    assert len(declaration_ids) >= 10
    assert len(declaration_ids) == len(set(declaration_ids))


def test_golden_harness_cases_are_stable_and_reference_declarations():
    payload = _golden_payload()

    assert (
        payload["version"]
        == "assessment-intelligence-v1-batch-d-question-bank-reuse-golden-v1"
    )
    assert payload["authorization"] == AUTHORIZATION

    cases = payload["cases"]
    case_ids = [case["id"] for case in cases]
    assert len(cases) >= 10
    assert len(case_ids) == len(set(case_ids))

    declaration_ids = _reuse_ids_from_declarations()
    seen_modes: set[str] = set()
    for case in cases:
        assert case["reuse_declaration_id"] in declaration_ids, case["id"]

        expected = case["expected"]
        mode = expected["mode"]
        seen_modes.add(mode)
        assert mode in ALLOWED_MODES, case["id"]
        assert expected["teacher_authority_required"] is True, case["id"]
        assert expected["reuse_review_required"] is True, case["id"]
        assert expected["evaluation_pipeline"] == "AEI", case["id"]
        assert expected["approved_evidence_required"] is True, case["id"]
        assert expected["autonomous_paper_approval"] is False, case["id"]
        assert expected["autonomous_question_approval"] is False, case["id"]
        assert expected["autonomous_grading"] is False, case["id"]
        assert expected["direct_marks_update"] is False, case["id"]
        assert expected["direct_parent_evidence"] is False, case["id"]
        assert expected["direct_mastery_update"] is False, case["id"]
        assert expected["runtime_behavior_change"] is False, case["id"]

        if mode != "supported":
            assert expected["product_claim_allowed"] is False, case["id"]

    assert ALLOWED_MODES.issubset(seen_modes)


def test_reuse_posture_required_fields_are_deterministic():
    for case in _golden_payload()["cases"]:
        reuse = case["reuse"]
        expected = case["expected"]
        mode = expected["mode"]
        posture = reuse["reuse_posture"]

        assert reuse["support_mode"] == mode, case["id"]

        if posture in SUPPORTED_REUSE_POSTURES:
            assert reuse["approval_status"] == BANK_STATUS_APPROVED, case["id"]
            assert mode == "supported", case["id"]
            assert expected["product_claim_allowed"] is True, case["id"]

        if posture == "approved_paper_ingestion":
            assert reuse["source_paper_required"] is True, case["id"]
            assert reuse["source_bank_item_required"] is False, case["id"]

        if posture in {"same_school_reuse", "blueprint_slot_compose"}:
            assert reuse["source_bank_item_required"] is True, case["id"]

        if case["case_type"] == "blueprint_slot_compose":
            assert reuse["marks_match"] is True, case["id"]
            assert reuse["type_match"] is True, case["id"]

        if posture == "gap_fill_assist":
            assert reuse["gap_fill_provenance"] == "generated_gap_fill", case["id"]
            assert reuse["represented_as_bank_reuse"] is False, case["id"]
            assert expected["product_claim_allowed"] is False, case["id"]

        if posture == "changed_context_review":
            assert reuse["changed_context_conflict_recorded"] is True, case["id"]
            assert mode == "manual_review", case["id"]

        if posture == "unsupported_reuse":
            assert reuse.get("unsupported_reason"), case["id"]
            assert mode == "unsupported", case["id"]
            assert expected["product_claim_allowed"] is False, case["id"]

        if posture == "future_expansion":
            assert mode == "expansion", case["id"]
            assert expected["product_claim_allowed"] is False, case["id"]


def test_existing_question_bank_constants_match_declared_batch_d_posture():
    assert BANK_STATUS_APPROVED == "approved"
    assert BANK_APPROVAL_STATUSES == frozenset({BANK_STATUS_APPROVED})

    source_values = {source.value for source in QuestionSource}
    assert {"ai", "teacher", "previous_paper"}.issubset(source_values)


def test_content_fingerprint_is_stable_for_same_question_content():
    first = content_fingerprint(
        question_text="  What IS Velocity? ",
        marks=2,
        question_type="Short",
    )
    second = content_fingerprint(
        question_text="what is velocity?",
        marks=2.0,
        question_type="short",
    )
    changed_marks = content_fingerprint(
        question_text="what is velocity?",
        marks=3.0,
        question_type="short",
    )

    assert first == second
    assert first != changed_marks


def test_batch_d_contract_blocks_runtime_surface_ai_and_evaluation_changes():
    contract = _read(AUTH_CONTRACT)
    blocked_items = [
        "database schema changes",
        "API contract changes",
        "UI changes",
        "runtime behavior changes",
        "feature flags",
        "AI provider changes",
        "LLM inference",
        "LLM prompt changes",
        "question generation behavior changes",
        "question-paper generation behavior changes",
        "question-bank service behavior changes",
        "paper approval behavior changes",
        "answer-sheet evaluation behavior changes",
        "exam service behavior changes",
        "AEI behavior changes",
        "EUI source adoption",
        "marks changes",
        "teacher review routing changes",
        "evidence-ledger behavior changes",
        "global question bank",
        "cross-school question marketplace",
        "Batch E paper-to-evaluation linkage",
    ]
    for item in blocked_items:
        assert item in contract
