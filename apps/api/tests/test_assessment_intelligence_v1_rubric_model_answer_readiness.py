"""Assessment Intelligence v1.0 Batch C rubric/model-answer readiness tests.

Batch C is intentionally non-runtime. These tests validate only static rubric
and model-answer declarations, Golden Harness cases, and governance posture.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DOC_DIR = REPO_ROOT / "docs" / "product" / "assessment-intelligence"
GOLDEN_CASES = (
    Path(__file__).parent
    / "golden"
    / "assessment_intelligence_v1"
    / "rubric_model_answer_readiness_cases.json"
)

DESIGN_BRIEF = (
    DOC_DIR
    / "ASSESSMENT_INTELLIGENCE_V1_BATCH_C_RUBRIC_MODEL_ANSWER_READINESS_DESIGN_BRIEF.md"
)
AUTH_CONTRACT = (
    DOC_DIR
    / (
        "ASSESSMENT_INTELLIGENCE_V1_BATCH_C_RUBRIC_MODEL_ANSWER_READINESS_"
        "IMPLEMENTATION_AUTHORIZATION_CONTRACT.md"
    )
)
DECLARATION_CONTRACT = (
    DOC_DIR / "ASSESSMENT_INTELLIGENCE_V1_BATCH_C_RUBRIC_MODEL_ANSWER_DECLARATION_CONTRACT.md"
)
SCOPE_DECLARATIONS = (
    DOC_DIR / "ASSESSMENT_INTELLIGENCE_V1_RUBRIC_MODEL_ANSWER_SUPPORTED_SCOPE_DECLARATIONS.md"
)

AUTHORIZATION = "ASSESSMENT-V1-BATCH-C-AUTH-001"
ALLOWED_MODES = {
    "supported",
    "assist",
    "checklist",
    "manual_review",
    "unsupported",
    "expansion",
}
REQUIRES_ANSWER_KEY = {"objective_key", "numeric_answer"}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _golden_payload() -> dict:
    return json.loads(GOLDEN_CASES.read_text(encoding="utf-8"))


def _rubric_ids_from_declarations() -> set[str]:
    return set(re.findall(r"`(assessment-rubric://[^`]+)`", _read(SCOPE_DECLARATIONS)))


def _criteria_marks_total(case: dict) -> int:
    return sum(int(criterion["marks"]) for criterion in case["rubric"].get("criteria", []))


def test_batch_c_artifacts_exist():
    for path in (
        DESIGN_BRIEF,
        AUTH_CONTRACT,
        DECLARATION_CONTRACT,
        SCOPE_DECLARATIONS,
        GOLDEN_CASES,
    ):
        assert path.exists(), path


def test_batch_c_authorization_and_design_are_accepted():
    assert "> Status: Accepted" in _read(DESIGN_BRIEF)
    assert "> Status: Accepted" in _read(AUTH_CONTRACT)
    assert f"> Authorization ID: {AUTHORIZATION}" in _read(AUTH_CONTRACT)
    assert "> Implementation authorization: Authorized for Batch C only" in _read(
        AUTH_CONTRACT
    )
    assert "> Runtime behavior changes: Not authorized" in _read(AUTH_CONTRACT)


def test_declaration_contract_contains_required_fields_and_invariants():
    contract = _read(DECLARATION_CONTRACT)
    required_terms = [
        "`rubric_id`",
        "`blueprint_id`",
        "`question_type`",
        "`marks`",
        "`rubric_posture`",
        "`support_mode`",
        "`answer_key`",
        "`model_answer`",
        "`acceptable_answers`",
        "`numeric_tolerance`",
        "`unit_posture`",
        "`scientific_notation_posture`",
        "`criteria`",
        "`checklist_items`",
        "`manual_review_reason`",
        "`unsupported_reason`",
        "`teacher_review_required`",
        "`evaluation_pipeline`",
        "`approved_evidence_required`",
        "`product_claim_allowed`",
        "`runtime_behavior_change`",
        "AEI remains the only academic answer-evaluation pipeline",
    ]
    for term in required_terms:
        assert term in contract


def test_scope_declarations_are_explicit_and_non_universal():
    declarations = _read(SCOPE_DECLARATIONS)

    for mode in ALLOWED_MODES:
        assert f"`{mode}`" in declarations

    required_claim_terms = [
        "Product claim allowed | Yes, inside this declared scope only",
        "Product claim allowed | No",
        "must not claim universal subjective grading",
        "autonomous answer grading",
        "direct parent/student evidence before teacher approval",
        "Runtime answer-sheet evaluation",
    ]
    for term in required_claim_terms:
        assert term in declarations

    declaration_ids = _rubric_ids_from_declarations()
    assert len(declaration_ids) >= 10
    assert len(declaration_ids) == len(set(declaration_ids))


def test_golden_harness_cases_are_stable_and_reference_declarations():
    payload = _golden_payload()

    assert payload["version"] == "assessment-intelligence-v1-batch-c-rubric-golden-v1"
    assert payload["authorization"] == AUTHORIZATION

    cases = payload["cases"]
    case_ids = [case["id"] for case in cases]
    assert len(cases) >= 10
    assert len(case_ids) == len(set(case_ids))

    declaration_ids = _rubric_ids_from_declarations()
    seen_modes: set[str] = set()
    for case in cases:
        assert case["rubric_id"] in declaration_ids, case["id"]

        expected = case["expected"]
        mode = expected["mode"]
        seen_modes.add(mode)
        assert mode in ALLOWED_MODES, case["id"]
        assert expected["teacher_authority_required"] is True, case["id"]
        assert expected["evaluation_pipeline"] == "AEI", case["id"]
        assert expected["approved_evidence_required"] is True, case["id"]
        assert expected["autonomous_approval"] is False, case["id"]
        assert expected["autonomous_grading"] is False, case["id"]
        assert expected["direct_marks_update"] is False, case["id"]
        assert expected["direct_parent_evidence"] is False, case["id"]
        assert expected["direct_mastery_update"] is False, case["id"]
        assert expected["runtime_behavior_change"] is False, case["id"]

        if mode != "supported":
            assert expected["product_claim_allowed"] is False, case["id"]

    assert ALLOWED_MODES.issubset(seen_modes)


def test_rubric_posture_required_fields_are_deterministic():
    for case in _golden_payload()["cases"]:
        rubric = case["rubric"]
        posture = rubric["rubric_posture"]

        if posture in REQUIRES_ANSWER_KEY:
            assert rubric.get("answer_key"), case["id"]
        if posture == "objective_key" and case["scope"]["question_type"] == "mcq":
            assert rubric.get("options_required") == 4, case["id"]
        if posture == "model_answer":
            assert rubric.get("model_answer"), case["id"]
        if posture == "criterion_rubric":
            assert rubric.get("criteria"), case["id"]
            assert _criteria_marks_total(case) == rubric["marks"], case["id"]
            assert _criteria_marks_total(case) == case["expected"]["criteria_marks_total"]
        if posture == "checklist":
            assert len(rubric.get("checklist_items", [])) == case["expected"][
                "checklist_item_count"
            ]
        if posture == "manual_review":
            assert rubric.get("manual_review_reason"), case["id"]
        if posture == "unsupported":
            assert rubric.get("unsupported_reason"), case["id"]


def test_numeric_answer_metadata_is_explicit_when_claimed():
    for case in _golden_payload()["cases"]:
        rubric = case["rubric"]
        if case["case_type"] == "acceptable_answers":
            assert len(rubric["acceptable_answers"]) == case["expected"][
                "acceptable_answer_count"
            ]
        if case["case_type"] == "unit_scientific_notation":
            assert rubric.get("numeric_tolerance") is not None, case["id"]
            assert rubric.get("unit_posture"), case["id"]
            assert rubric.get("scientific_notation_posture"), case["id"]


def test_batch_c_contract_blocks_runtime_surface_ai_and_evaluation_changes():
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
        "rubric generation",
        "runtime rubric source switching",
        "answer-sheet evaluation behavior changes",
        "question-paper generation behavior changes",
        "question-bank runtime behavior changes",
        "exam service behavior changes",
        "AEI behavior changes",
        "EUI source adoption",
        "marks changes",
        "teacher review routing changes",
        "evidence-ledger behavior changes",
        "public product claim expansion",
        "Batch D question-bank/reuse readiness",
    ]
    for item in blocked_items:
        assert item in contract
