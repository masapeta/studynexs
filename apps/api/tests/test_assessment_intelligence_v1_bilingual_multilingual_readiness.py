"""Assessment Intelligence v1.0 Batch F bilingual/multilingual readiness tests.

Batch F is intentionally non-runtime. These tests validate only static language
posture declarations, Golden Harness cases, and no-overclaim governance.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DOC_DIR = REPO_ROOT / "docs" / "product" / "assessment-intelligence"
EUI_REGISTRY = (
    REPO_ROOT
    / "apps"
    / "api"
    / "app"
    / "modules"
    / "eui"
    / "registry"
    / "platform_capability_registry.v1.json"
)
GOLDEN_CASES = (
    Path(__file__).parent
    / "golden"
    / "assessment_intelligence_v1"
    / "bilingual_multilingual_assessment_readiness_cases.json"
)

DESIGN_BRIEF = (
    DOC_DIR
    / (
        "ASSESSMENT_INTELLIGENCE_V1_BATCH_F_BILINGUAL_MULTILINGUAL_ASSESSMENT_"
        "READINESS_DESIGN_BRIEF.md"
    )
)
AUTH_CONTRACT = (
    DOC_DIR
    / (
        "ASSESSMENT_INTELLIGENCE_V1_BATCH_F_BILINGUAL_MULTILINGUAL_ASSESSMENT_"
        "READINESS_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md"
    )
)
DECLARATION_CONTRACT = (
    DOC_DIR
    / (
        "ASSESSMENT_INTELLIGENCE_V1_BATCH_F_BILINGUAL_MULTILINGUAL_ASSESSMENT_"
        "DECLARATION_CONTRACT.md"
    )
)
SCOPE_DECLARATIONS = (
    DOC_DIR
    / "ASSESSMENT_INTELLIGENCE_V1_BILINGUAL_MULTILINGUAL_SUPPORTED_SCOPE_DECLARATIONS.md"
)
CAPABILITY_MATRIX = (
    DOC_DIR / "ASSESSMENT_INTELLIGENCE_V1_SUPPORTED_SCOPE_CAPABILITY_MATRIX.md"
)

AUTHORIZATION = "ASSESSMENT-V1-BATCH-F-AUTH-001"
ALLOWED_MODES = {"supported", "assist", "manual_review", "unsupported", "expansion"}
SUPPORTED_LANGUAGE_POSTURES = {
    "english_assessment_contract",
    "english_grounded_paper",
    "english_answer_context",
}
REQUIRED_EXPECTED_FLAGS = [
    "teacher_authority_required",
    "teacher_review_required",
    "approved_evidence_required",
    "product_claim_allowed",
    "translation_execution",
    "ocr_execution",
    "autonomous_language_grading",
    "autonomous_paper_approval",
    "autonomous_marks",
    "direct_parent_evidence",
    "direct_mastery_update",
    "eui_source_adoption",
    "runtime_behavior_change",
    "aei_language_ocr_relationship",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _golden_payload() -> dict:
    return json.loads(GOLDEN_CASES.read_text(encoding="utf-8"))


def _language_ids_from_declarations() -> set[str]:
    return set(
        re.findall(r"`(assessment-language://[^`]+)`", _read(SCOPE_DECLARATIONS))
    )


def _platform_capability_ids() -> set[str]:
    payload = json.loads(EUI_REGISTRY.read_text(encoding="utf-8"))
    return {declaration["id"] for declaration in payload["declarations"]}


def test_batch_f_artifacts_exist():
    for path in (
        DESIGN_BRIEF,
        AUTH_CONTRACT,
        DECLARATION_CONTRACT,
        SCOPE_DECLARATIONS,
        GOLDEN_CASES,
    ):
        assert path.exists(), path


def test_batch_f_authorization_and_design_are_accepted():
    assert "> Status: Accepted" in _read(DESIGN_BRIEF)
    assert "> Status: Accepted" in _read(AUTH_CONTRACT)
    assert f"> Authorization ID: {AUTHORIZATION}" in _read(AUTH_CONTRACT)
    assert "> Implementation authorization: Authorized for Batch F only" in _read(
        AUTH_CONTRACT
    )
    assert "> Runtime behavior changes: Not authorized" in _read(AUTH_CONTRACT)


def test_declaration_contract_contains_required_fields_and_invariants():
    contract = _read(DECLARATION_CONTRACT)
    required_terms = [
        "`language_declaration_id`",
        "`support_mode`",
        "`assessment_language_posture`",
        "`school_id`",
        "`board`",
        "`curriculum`",
        "`curriculum_version`",
        "`grade`",
        "`subject`",
        "`paper_type`",
        "`primary_language`",
        "`secondary_language`",
        "`script`",
        "`language_medium`",
        "`question_text_language`",
        "`instructions_language`",
        "`answer_key_language`",
        "`model_answer_language`",
        "`rubric_language`",
        "`translation_source`",
        "`code_mixed_allowed`",
        "`aei_language_ocr_posture`",
        "`teacher_review_required`",
        "`approved_evidence_required`",
        "`product_claim_allowed`",
        "`runtime_behavior_change`",
        "Assessment language posture is readiness metadata, not translation authority",
        "AEI remains the only academic answer-evaluation pipeline",
    ]
    for term in required_terms:
        assert term in contract


def test_scope_declarations_are_explicit_and_block_overclaiming():
    declarations = _read(SCOPE_DECLARATIONS)

    for mode in ALLOWED_MODES:
        assert f"`{mode}`" in declarations

    required_claim_terms = [
        "Product claim allowed | Yes, inside this declared scope only",
        "Product claim allowed | No",
        "automatic question-paper translation",
        "automatic rubric/model-answer translation",
        "universal multilingual assessment",
        "autonomous language grading",
        "autonomous marks",
        "direct parent evidence",
        "direct mastery updates",
        "EUI source-of-truth adoption",
    ]
    for term in required_claim_terms:
        assert term in declarations

    declaration_ids = _language_ids_from_declarations()
    assert len(declaration_ids) >= 14
    assert len(declaration_ids) == len(set(declaration_ids))


def test_golden_harness_cases_are_stable_and_reference_declarations():
    payload = _golden_payload()

    assert (
        payload["version"]
        == "assessment-intelligence-v1-batch-f-bilingual-multilingual-golden-v1"
    )
    assert payload["authorization"] == AUTHORIZATION

    cases = payload["cases"]
    case_ids = [case["id"] for case in cases]
    assert len(cases) >= 14
    assert len(case_ids) == len(set(case_ids))

    declaration_ids = _language_ids_from_declarations()
    seen_modes: set[str] = set()
    for case in cases:
        assert case["language_declaration_id"] in declaration_ids, case["id"]

        expected = case["expected"]
        for field in REQUIRED_EXPECTED_FLAGS:
            assert field in expected, f"{case['id']} missing {field}"

        mode = expected["mode"]
        seen_modes.add(mode)
        assert mode in ALLOWED_MODES, case["id"]
        assert expected["teacher_authority_required"] is True, case["id"]
        assert expected["teacher_review_required"] is True, case["id"]
        assert expected["approved_evidence_required"] is True, case["id"]
        assert expected["translation_execution"] is False, case["id"]
        assert expected["ocr_execution"] is False, case["id"]
        assert expected["autonomous_language_grading"] is False, case["id"]
        assert expected["autonomous_paper_approval"] is False, case["id"]
        assert expected["autonomous_marks"] is False, case["id"]
        assert expected["direct_parent_evidence"] is False, case["id"]
        assert expected["direct_mastery_update"] is False, case["id"]
        assert expected["eui_source_adoption"] is False, case["id"]
        assert expected["runtime_behavior_change"] is False, case["id"]

        if mode != "supported":
            assert expected["product_claim_allowed"] is False, case["id"]

    assert ALLOWED_MODES.issubset(seen_modes)


def test_language_posture_rules_are_deterministic():
    for case in _golden_payload()["cases"]:
        expected = case["expected"]
        language = case["language"]
        mode = expected["mode"]
        posture = expected["assessment_language_posture"]

        assert language["question_text"], case["id"]
        assert language["instructions"], case["id"]
        assert language["answer_key"], case["id"]
        assert language["model_answer"], case["id"]
        assert language["rubric"], case["id"]
        assert language["translation_source"], case["id"]

        if posture in SUPPORTED_LANGUAGE_POSTURES:
            assert mode == "supported", case["id"]
            assert expected["product_claim_allowed"] is True, case["id"]
            assert language["primary"] == "English", case["id"]
            assert language["translation_source"] == "not_applicable", case["id"]

        if mode in {"assist", "manual_review"}:
            assert expected["product_claim_allowed"] is False, case["id"]
            assert expected["teacher_review_required"] is True, case["id"]

        if mode == "unsupported":
            assert "unsupported_reason" in expected, case["id"]
            assert expected["product_claim_allowed"] is False, case["id"]

        if mode == "expansion":
            assert "expansion_trigger" in expected, case["id"]
            assert expected["product_claim_allowed"] is False, case["id"]


def test_existing_assessment_capability_matrix_preserves_language_posture():
    matrix = _read(CAPABILITY_MATRIX)

    expected_terms = [
        "Languages | English supported",
        "`assessment://language/bilingual-paper-generation/cbse/ncf2023/general/v1`",
        "`manual_review`",
        "`assessment://language/universal-multilingual-assessment/v1`",
        "`unsupported`",
        "Do not claim production bilingual generation until later certification",
        "No universal multilingual assessment claim",
    ]
    for term in expected_terms:
        assert term in matrix


def test_existing_platform_registry_contains_referenced_language_assist_capabilities():
    capability_ids = _platform_capability_ids()

    expected_capabilities = {
        "pc://eui/language/printed_ocr/hindi/devanagari",
        "pc://eui/language/handwriting_ocr/hindi/devanagari",
        "pc://eui/language/handwriting_ocr/telugu",
        "pc://eui/language/handwriting_ocr/sanskrit/devanagari",
    }
    assert expected_capabilities.issubset(capability_ids)


def test_batch_f_contract_blocks_runtime_and_behavior_changes():
    contract = _read(AUTH_CONTRACT)
    blocked_terms = [
        "database schema changes",
        "API contract changes",
        "UI changes",
        "runtime behavior changes",
        "feature flags",
        "translation engine integration",
        "new OCR behavior",
        "AI provider changes",
        "LLM inference",
        "question-paper generation behavior changes",
        "bilingual paper generation behavior changes",
        "AEI language/OCR behavior changes",
        "marks changes",
        "teacher review routing changes",
        "evidence-ledger behavior changes",
        "parent/student visibility changes",
        "mastery updates",
        "browser workflow changes",
        "public bilingual/multilingual product claim expansion",
        "Batch G teacher workflow/browser proof",
    ]
    for term in blocked_terms:
        assert term in contract

