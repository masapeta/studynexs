"""Assessment Intelligence v1.0 Batch E paper-to-evaluation linkage tests.

Batch E is intentionally non-runtime. These tests validate only static linkage
declarations, Golden Harness cases, and governance posture.
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from app.db.models.answer_sheet_evaluation import (
    EVAL_STATUS_APPROVED,
    EVAL_STATUS_SUGGESTED,
)
from app.db.models.question_paper import PaperStatus
from app.modules.examinations.schemas.exam import ExamOut
from app.modules.examinations.services.aei_v1_evidence_ledger import (
    build_approved_evidence_metadata,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
DOC_DIR = REPO_ROOT / "docs" / "product" / "assessment-intelligence"
GOLDEN_CASES = (
    Path(__file__).parent
    / "golden"
    / "assessment_intelligence_v1"
    / "paper_to_evaluation_linkage_readiness_cases.json"
)

DESIGN_BRIEF = (
    DOC_DIR
    / (
        "ASSESSMENT_INTELLIGENCE_V1_BATCH_E_PAPER_TO_EVALUATION_LINKAGE_"
        "READINESS_DESIGN_BRIEF.md"
    )
)
AUTH_CONTRACT = (
    DOC_DIR
    / (
        "ASSESSMENT_INTELLIGENCE_V1_BATCH_E_PAPER_TO_EVALUATION_LINKAGE_"
        "READINESS_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md"
    )
)
DECLARATION_CONTRACT = (
    DOC_DIR
    / "ASSESSMENT_INTELLIGENCE_V1_BATCH_E_PAPER_TO_EVALUATION_LINKAGE_DECLARATION_CONTRACT.md"
)
SCOPE_DECLARATIONS = (
    DOC_DIR
    / "ASSESSMENT_INTELLIGENCE_V1_PAPER_TO_EVALUATION_LINKAGE_SUPPORTED_SCOPE_DECLARATIONS.md"
)

AUTHORIZATION = "ASSESSMENT-V1-BATCH-E-AUTH-001"
ALLOWED_MODES = {"supported", "assist", "manual_review", "unsupported", "expansion"}
SUPPORTED_LINKAGE_POSTURES = {
    "approved_paper_schema",
    "source_paper_schema_evaluation_ready",
    "linked_rubric_context",
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _golden_payload() -> dict:
    return json.loads(GOLDEN_CASES.read_text(encoding="utf-8"))


def _linkage_ids_from_declarations() -> set[str]:
    return set(
        re.findall(r"`(assessment-linkage://[^`]+)`", _read(SCOPE_DECLARATIONS))
    )


def test_batch_e_artifacts_exist():
    for path in (
        DESIGN_BRIEF,
        AUTH_CONTRACT,
        DECLARATION_CONTRACT,
        SCOPE_DECLARATIONS,
        GOLDEN_CASES,
    ):
        assert path.exists(), path


def test_batch_e_authorization_and_design_are_accepted():
    assert "> Status: Accepted" in _read(DESIGN_BRIEF)
    assert "> Status: Accepted" in _read(AUTH_CONTRACT)
    assert f"> Authorization ID: {AUTHORIZATION}" in _read(AUTH_CONTRACT)
    assert "> Implementation authorization: Authorized for Batch E only" in _read(
        AUTH_CONTRACT
    )
    assert "> Runtime behavior changes: Not authorized" in _read(AUTH_CONTRACT)


def test_declaration_contract_contains_required_fields_and_invariants():
    contract = _read(DECLARATION_CONTRACT)
    required_terms = [
        "`linkage_declaration_id`",
        "`support_mode`",
        "`linkage_posture`",
        "`school_id`",
        "`exam_id`",
        "`source_paper_id`",
        "`source_paper_status`",
        "`question_schema_source`",
        "`question_schema_required`",
        "`source_paper_required`",
        "`question_numbers_unique`",
        "`max_marks_preserved`",
        "`educational_identity_posture`",
        "`rubric_source`",
        "`rubric_available`",
        "`can_evaluate_sheets`",
        "`ocr_input_allowed`",
        "`manual_input_allowed`",
        "`input_authority`",
        "`aei_assist_allowed`",
        "`teacher_review_required`",
        "`approved_evidence_required`",
        "`marks_source`",
        "`mastery_source`",
        "`product_claim_allowed`",
        "`runtime_behavior_change`",
        "Linkage creates readiness, not authority",
        "AEI remains the only academic answer-evaluation pipeline",
    ]
    for term in required_terms:
        assert term in contract


def test_scope_declarations_are_explicit_and_block_autonomous_authority():
    declarations = _read(SCOPE_DECLARATIONS)

    for mode in ALLOWED_MODES:
        assert f"`{mode}`" in declarations

    required_claim_terms = [
        "Product claim allowed | Yes, inside this declared scope only",
        "Product claim allowed | No",
        "autonomous grading",
        "autonomous marks",
        "direct parent",
        "direct mastery",
        "EUI source-of-truth adoption",
        "Exam services",
    ]
    for term in required_claim_terms:
        assert term in declarations

    declaration_ids = _linkage_ids_from_declarations()
    assert len(declaration_ids) >= 11
    assert len(declaration_ids) == len(set(declaration_ids))


def test_golden_harness_cases_are_stable_and_reference_declarations():
    payload = _golden_payload()

    assert (
        payload["version"]
        == "assessment-intelligence-v1-batch-e-paper-to-evaluation-linkage-golden-v1"
    )
    assert payload["authorization"] == AUTHORIZATION

    cases = payload["cases"]
    case_ids = [case["id"] for case in cases]
    assert len(cases) >= 11
    assert len(case_ids) == len(set(case_ids))

    declaration_ids = _linkage_ids_from_declarations()
    seen_modes: set[str] = set()
    for case in cases:
        assert case["linkage_declaration_id"] in declaration_ids, case["id"]

        expected = case["expected"]
        mode = expected["mode"]
        seen_modes.add(mode)
        assert mode in ALLOWED_MODES, case["id"]
        assert expected["teacher_authority_required"] is True, case["id"]
        assert expected["teacher_review_required"] is True, case["id"]
        assert expected["evaluation_pipeline"] == "AEI", case["id"]
        assert expected["approved_evidence_required"] is True, case["id"]
        assert expected["input_authority"] == "input_capture_only", case["id"]
        assert expected["marks_source"] == "teacher_approved_decision", case["id"]
        assert expected["mastery_source"] == "approved_marks_and_evidence", case["id"]
        assert expected["autonomous_grading"] is False, case["id"]
        assert expected["autonomous_marks"] is False, case["id"]
        assert expected["direct_parent_evidence"] is False, case["id"]
        assert expected["direct_mastery_update"] is False, case["id"]
        assert expected["runtime_behavior_change"] is False, case["id"]

        if mode != "supported":
            assert expected["product_claim_allowed"] is False, case["id"]

    assert ALLOWED_MODES.issubset(seen_modes)


def test_linkage_posture_required_fields_are_deterministic():
    for case in _golden_payload()["cases"]:
        linkage = case["linkage"]
        expected = case["expected"]
        mode = expected["mode"]
        posture = linkage["linkage_posture"]

        assert linkage["support_mode"] == mode, case["id"]

        if posture in SUPPORTED_LINKAGE_POSTURES:
            assert linkage["source_paper_status"] == PaperStatus.APPROVED.value, case["id"]
            assert mode == "supported", case["id"]
            assert expected["product_claim_allowed"] is True, case["id"]

        if posture == "approved_paper_schema":
            assert linkage["source_paper_required"] is True, case["id"]
            assert linkage["question_schema_source"] == "approved_paper", case["id"]
            assert linkage["question_numbers_unique"] is True, case["id"]
            assert linkage["max_marks_preserved"] is True, case["id"]

        if posture == "source_paper_schema_evaluation_ready":
            assert linkage["source_paper_required"] is True, case["id"]
            assert linkage["question_schema_required"] is True, case["id"]
            assert linkage["can_evaluate_sheets"] is True, case["id"]
            assert linkage["aei_assist_allowed"] is True, case["id"]

        if posture == "linked_rubric_context":
            assert linkage["rubric_source"] == "linked_source_paper", case["id"]
            assert linkage["rubric_available"] is True, case["id"]

        if posture in {"ocr_input_assist", "manual_input_assist"}:
            assert linkage["input_authority"] == "input_capture_only", case["id"]
            assert expected["product_claim_allowed"] is False, case["id"]

        if posture == "manual_schema_review":
            assert linkage["source_paper_required"] is False, case["id"]
            assert linkage["question_schema_source"] == "manual", case["id"]
            assert mode == "manual_review", case["id"]

        if posture == "unsupported_linkage":
            assert linkage.get("unsupported_reason"), case["id"]
            assert mode == "unsupported", case["id"]
            assert expected["product_claim_allowed"] is False, case["id"]

        if posture == "future_expansion":
            assert mode == "expansion", case["id"]
            assert expected["product_claim_allowed"] is False, case["id"]


def test_existing_exam_out_can_evaluate_sheets_requires_source_paper_and_schema():
    source_paper_id = uuid.uuid4()
    base = {
        "id": uuid.uuid4(),
        "class_id": uuid.uuid4(),
        "subject_id": uuid.uuid4(),
        "exam_type": "unit_test",
        "title": "Linked Evaluation",
        "total_marks": 20,
        "date": None,
        "topic": "Measurement",
    }

    linked = ExamOut.from_exam(
        SimpleNamespace(
            **base,
            source_paper_id=source_paper_id,
            question_schema=[{"no": "1", "max_marks": 10}],
        )
    )
    missing_schema = ExamOut.from_exam(
        SimpleNamespace(**base, source_paper_id=source_paper_id, question_schema=None)
    )
    manual_schema = ExamOut.from_exam(
        SimpleNamespace(
            **base,
            source_paper_id=None,
            question_schema=[{"no": "1", "max_marks": 10}],
        )
    )

    assert linked.can_evaluate_sheets is True
    assert linked.has_question_schema is True
    assert missing_schema.can_evaluate_sheets is False
    assert manual_schema.can_evaluate_sheets is False
    assert manual_schema.has_question_schema is True


def test_existing_evidence_helper_blocks_downstream_before_teacher_approval():
    suggested = build_approved_evidence_metadata(
        evaluation_status=EVAL_STATUS_SUGGESTED,
        suggestions={"1": {"marks_suggested": 1, "max_marks": 2}},
        teacher_overrides=None,
        approved_by=None,
        approved_at=None,
    )
    approved = build_approved_evidence_metadata(
        evaluation_status=EVAL_STATUS_APPROVED,
        suggestions={"1": {"marks_suggested": 1, "max_marks": 2}},
        teacher_overrides={},
        approved_by=uuid.uuid4(),
        approved_at=datetime.now(timezone.utc),
    )

    assert suggested["approved_evidence"] is False
    assert suggested["approved_for_downstream"] is False
    assert approved["approved_evidence"] is True
    assert approved["approved_for_downstream"] is True


def test_batch_e_contract_blocks_runtime_surface_ai_and_evaluation_changes():
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
        "OCR engine changes",
        "question-paper generation behavior changes",
        "question-bank service behavior changes",
        "exam service behavior changes",
        "answer-sheet evaluation behavior changes",
        "teacher approval behavior changes",
        "AEI grading behavior changes",
        "AEI confidence behavior changes",
        "AEI teacher-review routing changes",
        "EUI source adoption",
        "marks changes",
        "evidence-ledger behavior changes",
        "mastery updates",
        "Batch F multilingual/bilingual behavior",
    ]
    for item in blocked_items:
        assert item in contract
