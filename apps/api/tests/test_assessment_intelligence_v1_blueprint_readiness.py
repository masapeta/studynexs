"""Assessment Intelligence v1.0 Batch B blueprint readiness tests.

Batch B is intentionally non-runtime. These tests validate only static
blueprint declarations, Golden Harness cases, and governance posture.
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
    / "blueprint_readiness_cases.json"
)

DESIGN_BRIEF = (
    DOC_DIR / "ASSESSMENT_INTELLIGENCE_V1_BATCH_B_BLUEPRINT_READINESS_DESIGN_BRIEF.md"
)
AUTH_CONTRACT = (
    DOC_DIR
    / (
        "ASSESSMENT_INTELLIGENCE_V1_BATCH_B_BLUEPRINT_READINESS_"
        "IMPLEMENTATION_AUTHORIZATION_CONTRACT.md"
    )
)
DECLARATION_CONTRACT = (
    DOC_DIR / "ASSESSMENT_INTELLIGENCE_V1_BATCH_B_BLUEPRINT_DECLARATION_CONTRACT.md"
)
SCOPE_DECLARATIONS = (
    DOC_DIR / "ASSESSMENT_INTELLIGENCE_V1_BLUEPRINT_SUPPORTED_SCOPE_DECLARATIONS.md"
)

AUTHORIZATION = "ASSESSMENT-V1-BATCH-B-AUTH-001"
ALLOWED_MODES = {
    "supported",
    "assist",
    "manual_review",
    "unsupported",
    "expansion",
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _golden_payload() -> dict:
    return json.loads(GOLDEN_CASES.read_text(encoding="utf-8"))


def _blueprint_ids_from_declarations() -> set[str]:
    return set(re.findall(r"`(assessment-blueprint://[^`]+)`", _read(SCOPE_DECLARATIONS)))


def _printed_marks(case: dict) -> int:
    return sum(
        section["marks_per_question"] * section["question_count"]
        for section in case["blueprint"]["sections"]
    )


def _answer_required_marks(case: dict) -> int:
    return sum(
        section["marks_per_question"] * section["answer_any_count"]
        for section in case["blueprint"]["sections"]
    )


def _internal_choice_sections(case: dict) -> list[str]:
    return [
        section["section_id"]
        for section in case["blueprint"]["sections"]
        if section["answer_any_count"] < section["question_count"]
    ]


def test_batch_b_artifacts_exist():
    for path in (
        DESIGN_BRIEF,
        AUTH_CONTRACT,
        DECLARATION_CONTRACT,
        SCOPE_DECLARATIONS,
        GOLDEN_CASES,
    ):
        assert path.exists(), path


def test_batch_b_authorization_and_design_are_accepted():
    assert "> Status: Accepted" in _read(DESIGN_BRIEF)
    assert "> Status: Accepted" in _read(AUTH_CONTRACT)
    assert f"> Authorization ID: {AUTHORIZATION}" in _read(AUTH_CONTRACT)
    assert "> Implementation authorization: Authorized for Batch B only" in _read(
        AUTH_CONTRACT
    )
    assert "> Runtime behavior changes: Not authorized" in _read(AUTH_CONTRACT)


def test_declaration_contract_contains_required_fields_and_invariants():
    contract = _read(DECLARATION_CONTRACT)
    required_terms = [
        "`blueprint_id`",
        "`board`",
        "`curriculum`",
        "`grade`",
        "`subject`",
        "`paper_type`",
        "`version`",
        "`support_mode`",
        "`total_marks`",
        "`printed_marks_total`",
        "`duration_minutes`",
        "`sections`",
        "`validation_rules`",
        "`product_claim_allowed`",
        "`teacher_authority_required`",
        "`runtime_behavior_change`",
        "printed_section_marks = marks_per_question * question_count",
        "effective_section_marks = marks_per_question * answer_any_count",
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
        "must not claim universal blueprint support",
        "autonomous answer grading",
        "teacher-final authority",
        "Runtime question-paper generation",
    ]
    for term in required_claim_terms:
        assert term in declarations

    declaration_ids = _blueprint_ids_from_declarations()
    assert len(declaration_ids) >= 6
    assert len(declaration_ids) == len(set(declaration_ids))


def test_golden_harness_cases_are_stable_and_reference_declarations():
    payload = _golden_payload()

    assert payload["version"] == "assessment-intelligence-v1-batch-b-blueprint-golden-v1"
    assert payload["authorization"] == AUTHORIZATION

    cases = payload["cases"]
    case_ids = [case["id"] for case in cases]
    assert len(cases) >= 8
    assert len(case_ids) == len(set(case_ids))

    declaration_ids = _blueprint_ids_from_declarations()
    seen_modes: set[str] = set()
    for case in cases:
        assert case["blueprint_id"] in declaration_ids, case["id"]

        expected = case["expected"]
        mode = expected["mode"]
        seen_modes.add(mode)
        assert mode in ALLOWED_MODES, case["id"]
        assert expected["teacher_authority_required"] is True, case["id"]
        assert expected["autonomous_approval"] is False, case["id"]
        assert expected["autonomous_grading"] is False, case["id"]
        assert expected["evaluation_pipeline"] == "AEI", case["id"]
        assert expected["runtime_behavior_change"] is False, case["id"]

        if mode != "supported":
            assert expected["product_claim_allowed"] is False, case["id"]

    assert ALLOWED_MODES.issubset(seen_modes)


def test_blueprint_marks_and_internal_choice_calculations_are_deterministic():
    for case in _golden_payload()["cases"]:
        expected = case["expected"]
        if case["blueprint"]["sections"]:
            assert _printed_marks(case) == expected["printed_marks_total"], case["id"]
            assert _answer_required_marks(case) == expected["answer_required_total"], (
                case["id"]
            )
            assert bool(_internal_choice_sections(case)) is expected.get(
                "internal_choice", False
            ), case["id"]

        if "internal_choice_sections" in expected:
            assert _internal_choice_sections(case) == expected["internal_choice_sections"]


def test_mcq_sections_have_explicit_option_requirements():
    for case in _golden_payload()["cases"]:
        for section in case["blueprint"]["sections"]:
            if section["question_type"] == "mcq":
                assert section["options_required"] == 4, case["id"]


def test_batch_b_contract_blocks_runtime_surface_and_ai_changes():
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
        "runtime blueprint source switching",
        "question-paper generation behavior changes",
        "question-bank runtime behavior changes",
        "exam service behavior changes",
        "AEI behavior changes",
        "EUI source adoption",
        "marks changes",
        "teacher review routing changes",
        "evidence-ledger behavior changes",
        "public product claim expansion",
        "Batch C rubric/model-answer work",
    ]
    for item in blocked_items:
        assert item in contract
