"""Assessment Intelligence v1.0 Batch G-B browser-proof fixture tests.

These tests validate the reproducible Reference tenant fixture definition only.
They do not require database access and do not create tenant data.
"""

from __future__ import annotations

import importlib.util
from decimal import Decimal
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_SCRIPT = REPO_ROOT / "apps" / "api" / "scripts" / (
    "seed_assessment_browser_proof_fixture.py"
)
DOC_DIR = REPO_ROOT / "docs" / "product" / "assessment-intelligence"
DESIGN_BRIEF = DOC_DIR / (
    "ASSESSMENT_INTELLIGENCE_V1_BATCH_G_B_REPRODUCIBLE_REFERENCE_FIXTURE_"
    "DESIGN_BRIEF.md"
)
AUTH_CONTRACT = DOC_DIR / (
    "ASSESSMENT_INTELLIGENCE_V1_BATCH_G_B_REPRODUCIBLE_REFERENCE_FIXTURE_"
    "IMPLEMENTATION_AUTHORIZATION_CONTRACT.md"
)
CERTIFICATION_REPORT = DOC_DIR / (
    "ASSESSMENT_INTELLIGENCE_V1_BATCH_G_B_REPRODUCIBLE_REFERENCE_FIXTURE_"
    "CERTIFICATION_REPORT.md"
)


def _fixture_module():
    spec = importlib.util.spec_from_file_location(
        "seed_assessment_browser_proof_fixture",
        FIXTURE_SCRIPT,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_batch_g_b_artifacts_exist():
    for path in (FIXTURE_SCRIPT, DESIGN_BRIEF, AUTH_CONTRACT, CERTIFICATION_REPORT):
        assert path.exists(), path


def test_batch_g_b_docs_preserve_narrow_governance_boundary():
    design = _read(DESIGN_BRIEF)
    contract = _read(AUTH_CONTRACT)

    assert "> Status: Accepted" in design
    assert "> Status: Accepted" in contract
    assert "> Implementation authorization: Authorized for Batch G-B only" in contract
    assert "> Runtime behavior changes: Not authorized" in contract

    blocked_terms = [
        "database schema changes",
        "API contract changes",
        "UI changes",
        "runtime product behavior changes",
        "marks changes",
        "answer-sheet evaluation behavior changes",
        "AEI behavior changes",
        "EUI source adoption",
        "evidence-ledger behavior changes",
        "product claim expansion",
    ]
    for term in blocked_terms:
        assert term in contract


def test_fixture_scope_matches_browser_proof_primary_scope():
    fixture = _fixture_module()

    assert fixture.TENANT_SLUG == "reference"
    assert fixture.SCHOOL_BOARD == "SSC"
    assert fixture.FIXTURE_CURRICULUM == "Telangana reference material"
    assert fixture.FIXTURE_GRADE == "Class 6"
    assert fixture.FIXTURE_SUBJECT == "Science"
    assert fixture.FIXTURE_PAPER_TYPE == "Unit Test"
    assert fixture.FIXTURE_LANGUAGE == "English"
    assert fixture.fixture_scope() == {
        "board": "SSC",
        "curriculum": "Telangana reference material",
        "grade": "6",
        "subject": "Science",
        "paper_type": "Unit Test",
        "language": "English",
    }


def test_fixture_question_schema_is_deterministic_and_evaluation_ready():
    fixture = _fixture_module()
    schema = fixture.build_question_schema()

    assert fixture.fixture_total_marks() == Decimal("20")
    assert fixture.FIXTURE_TOTAL_MARKS == Decimal("20")
    assert len(schema) == 12
    assert sum(Decimal(str(item["max_marks"])) for item in schema) == Decimal("20.0")
    assert [item["no"] for item in schema] == [str(i) for i in range(1, 13)]
    assert all(item["topic"] for item in schema)
    assert all(isinstance(item["max_marks"], float) for item in schema)


def test_fixture_paper_body_has_answer_keys_without_authoritative_marks():
    fixture = _fixture_module()

    questions = [
        question
        for section in fixture.FIXTURE_SECTIONS
        for question in section["questions"]
    ]
    assert len(questions) == 12
    assert all(question["answer_key"] for question in questions)
    assert all(question["marks"] > 0 for question in questions)
    assert not any("marks_obtained" in question for question in questions)
    assert not any("teacher_override" in question for question in questions)
    assert not any("student_id" in question for question in questions)

