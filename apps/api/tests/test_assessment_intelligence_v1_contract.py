"""Assessment Intelligence v1.0 Batch A static contract tests.

Batch A is intentionally non-runtime. These tests validate only the accepted
contract, supported-scope matrix, and Golden Harness starter cases.
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
    / "assessment_contract_cases.json"
)

READINESS_REVIEW = DOC_DIR / "ASSESSMENT_INTELLIGENCE_V1_PRODUCTION_READINESS_REVIEW.md"
DESIGN_BRIEF = DOC_DIR / "ASSESSMENT_INTELLIGENCE_V1_IMPLEMENTATION_DESIGN_BRIEF.md"
AUTH_CONTRACT = (
    DOC_DIR
    / "ASSESSMENT_INTELLIGENCE_V1_BATCH_A_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md"
)
CANONICAL_CONTRACT = DOC_DIR / "ASSESSMENT_INTELLIGENCE_V1_CANONICAL_CONTRACT.md"
CAPABILITY_MATRIX = DOC_DIR / "ASSESSMENT_INTELLIGENCE_V1_SUPPORTED_SCOPE_CAPABILITY_MATRIX.md"

AUTHORIZATION = "ASSESSMENT-V1-BATCH-A-AUTH-001"
ALLOWED_MODES = {
    "supported",
    "assist",
    "checklist",
    "manual_review",
    "unsupported",
    "expansion",
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_assessment_intelligence_v1_batch_a_artifacts_exist():
    for path in (
        READINESS_REVIEW,
        DESIGN_BRIEF,
        AUTH_CONTRACT,
        CANONICAL_CONTRACT,
        CAPABILITY_MATRIX,
        GOLDEN_CASES,
    ):
        assert path.exists(), path


def test_assessment_intelligence_v1_planning_artifacts_are_accepted():
    assert "> Status: Accepted" in _read(READINESS_REVIEW)
    assert "> Status: Accepted" in _read(DESIGN_BRIEF)
    assert "> Status: Accepted" in _read(AUTH_CONTRACT)
    assert f"> Authorization ID: {AUTHORIZATION}" in _read(AUTH_CONTRACT)
    assert "> Implementation authorization: Authorized for Batch A only" in _read(AUTH_CONTRACT)


def test_canonical_contract_contains_required_field_groups_and_invariants():
    contract = _read(CANONICAL_CONTRACT)
    required_sections = [
        "Identity fields",
        "Curriculum fields",
        "Blueprint fields",
        "Question fields",
        "Answer key fields",
        "Rubric fields",
        "Provenance fields",
        "Evaluation linkage fields",
        "Support posture fields",
    ]
    for section in required_sections:
        assert section in contract

    required_terms = [
        "`tenant_id`",
        "`educational_identity_id`",
        "`blueprint_id`",
        "`answer_key`",
        "`model_answer`",
        "`rubric_posture`",
        "`grounding_sources`",
        "`evaluation_pipeline`",
        "`approved_evidence_required`",
        "`runtime_authority`",
        "Answer evaluation must flow through AEI",
        "Parent/student/principal consumers may receive only approved evidence",
    ]
    for term in required_terms:
        assert term in contract


def test_supported_scope_matrix_declares_modes_and_avoids_universal_claims():
    matrix = _read(CAPABILITY_MATRIX)

    for mode in ALLOWED_MODES:
        assert f"`{mode}`" in matrix

    assert "must not claim" in matrix.lower()
    assert "universal board support" in matrix.lower()
    assert "universal bilingual or multilingual generation" in matrix.lower()
    assert "autonomous answer grading" in matrix.lower()
    assert "teacher final authority" in matrix.lower()


def test_golden_harness_cases_are_stable_and_governance_safe():
    payload = json.loads(GOLDEN_CASES.read_text(encoding="utf-8"))

    assert payload["version"] == "assessment-intelligence-v1-batch-a-golden-v1"
    assert payload["authorization"] == AUTHORIZATION

    cases = payload["cases"]
    case_ids = [case["id"] for case in cases]
    assert len(cases) >= 9
    assert len(case_ids) == len(set(case_ids))

    matrix_ids = set(re.findall(r"`(assessment://[^`]+)`", _read(CAPABILITY_MATRIX)))
    assert matrix_ids

    seen_modes: set[str] = set()
    for case in cases:
        assert case["capability_id"] in matrix_ids, case["id"]
        assert case["contract_focus"], case["id"]

        expected = case["expected"]
        mode = expected["mode"]
        seen_modes.add(mode)
        assert mode in ALLOWED_MODES, case["id"]
        assert expected["teacher_authority_required"] is True, case["id"]
        assert expected["authoritative_without_approval"] is False, case["id"]
        assert expected["autonomous_grading"] is False, case["id"]
        assert expected["evaluation_pipeline"] == "AEI", case["id"]
        assert expected["downstream_evidence_source"] == "teacher_approved_evidence", case["id"]
        assert expected["runtime_behavior_change"] is False, case["id"]

    assert {"supported", "assist", "manual_review", "unsupported"}.issubset(seen_modes)


def test_batch_a_contract_blocks_runtime_and_surface_changes():
    contract = _read(AUTH_CONTRACT)
    blocked_items = [
        "database schema changes",
        "API contract changes",
        "UI changes",
        "runtime behavior changes",
        "feature flag changes",
        "LLM inference",
        "question paper generation behavior changes",
        "question bank runtime behavior changes",
        "exam service behavior changes",
        "AEI behavior changes",
        "EUI source adoption",
        "marks changes",
        "teacher review routing changes",
        "evidence ledger behavior changes",
        "parent/student visibility changes",
    ]
    for item in blocked_items:
        assert item in contract
