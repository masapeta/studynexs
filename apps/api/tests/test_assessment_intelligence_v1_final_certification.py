"""Assessment Intelligence v1.0 final certification tests.

Batch H is intentionally certification-only. These tests validate the final
certification and product-claim boundary artifacts without touching runtime
behavior.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DOC_DIR = REPO_ROOT / "docs" / "product" / "assessment-intelligence"

DESIGN_BRIEF = DOC_DIR / (
    "ASSESSMENT_INTELLIGENCE_V1_BATCH_H_FINAL_CERTIFICATION_DESIGN_BRIEF.md"
)
AUTH_CONTRACT = DOC_DIR / (
    "ASSESSMENT_INTELLIGENCE_V1_BATCH_H_FINAL_CERTIFICATION_"
    "IMPLEMENTATION_AUTHORIZATION_CONTRACT.md"
)
FINAL_CERTIFICATION = DOC_DIR / "ASSESSMENT_INTELLIGENCE_V1_FINAL_CERTIFICATION_REPORT.md"
PRODUCT_CLAIM_BOUNDARY = DOC_DIR / "ASSESSMENT_INTELLIGENCE_V1_PRODUCT_CLAIM_BOUNDARY.md"

CERTIFICATION_REPORTS = [
    "ASSESSMENT_INTELLIGENCE_V1_BATCH_A_CONTRACT_CAPABILITY_MATRIX_CERTIFICATION_REPORT.md",
    "ASSESSMENT_INTELLIGENCE_V1_BATCH_B_BLUEPRINT_READINESS_CERTIFICATION_REPORT.md",
    "ASSESSMENT_INTELLIGENCE_V1_BATCH_C_RUBRIC_MODEL_ANSWER_READINESS_CERTIFICATION_REPORT.md",
    "ASSESSMENT_INTELLIGENCE_V1_BATCH_D_QUESTION_BANK_REUSE_READINESS_CERTIFICATION_REPORT.md",
    "ASSESSMENT_INTELLIGENCE_V1_BATCH_E_PAPER_TO_EVALUATION_LINKAGE_READINESS_CERTIFICATION_REPORT.md",
    "ASSESSMENT_INTELLIGENCE_V1_BATCH_F_BILINGUAL_MULTILINGUAL_ASSESSMENT_READINESS_CERTIFICATION_REPORT.md",
    "ASSESSMENT_INTELLIGENCE_V1_BATCH_G_TEACHER_WORKFLOW_BROWSER_PROOF_CERTIFICATION_REPORT.md",
    "ASSESSMENT_INTELLIGENCE_V1_BATCH_G_B_REPRODUCIBLE_REFERENCE_FIXTURE_CERTIFICATION_REPORT.md",
]

SUPPORT_ARTIFACTS = [
    "ASSESSMENT_INTELLIGENCE_V1_CANONICAL_CONTRACT.md",
    "ASSESSMENT_INTELLIGENCE_V1_SUPPORTED_SCOPE_CAPABILITY_MATRIX.md",
    "ASSESSMENT_INTELLIGENCE_V1_BLUEPRINT_SUPPORTED_SCOPE_DECLARATIONS.md",
    "ASSESSMENT_INTELLIGENCE_V1_RUBRIC_MODEL_ANSWER_SUPPORTED_SCOPE_DECLARATIONS.md",
    "ASSESSMENT_INTELLIGENCE_V1_QUESTION_BANK_REUSE_SUPPORTED_SCOPE_DECLARATIONS.md",
    "ASSESSMENT_INTELLIGENCE_V1_PAPER_TO_EVALUATION_LINKAGE_SUPPORTED_SCOPE_DECLARATIONS.md",
    "ASSESSMENT_INTELLIGENCE_V1_BILINGUAL_MULTILINGUAL_SUPPORTED_SCOPE_DECLARATIONS.md",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_batch_h_artifacts_exist():
    for path in (
        DESIGN_BRIEF,
        AUTH_CONTRACT,
        FINAL_CERTIFICATION,
        PRODUCT_CLAIM_BOUNDARY,
    ):
        assert path.exists(), path

    for name in CERTIFICATION_REPORTS + SUPPORT_ARTIFACTS:
        assert (DOC_DIR / name).exists(), name


def test_batch_h_authorization_is_accepted_and_runtime_changes_blocked():
    design = _read(DESIGN_BRIEF)
    contract = _read(AUTH_CONTRACT)

    assert "> Status: Accepted" in design
    assert "> Implementation: Authorized by `ASSESSMENT-V1-BATCH-H-AUTH-001`" in design
    assert "> Status: Accepted" in contract
    assert "> Authorization ID: ASSESSMENT-V1-BATCH-H-AUTH-001" in contract
    assert "> Implementation authorization: Authorized for Batch H only" in contract
    assert "> Runtime behavior changes: Not authorized" in contract

    excluded_terms = [
        "database schema changes",
        "API contract changes",
        "production UI changes",
        "runtime product behavior changes",
        "question-paper generation behavior changes",
        "answer-sheet evaluation behavior changes",
        "AEI behavior changes",
        "EUI behavior changes",
        "marks changes",
        "evidence-ledger behavior changes",
        "OCR behavior changes",
        "translation behavior changes",
    ]
    for term in excluded_terms:
        assert term in contract


def test_final_certification_references_all_prior_batches_and_boundaries():
    report = _read(FINAL_CERTIFICATION)

    assert "> Status: Certified" in report
    assert "> Authorization: ASSESSMENT-V1-BATCH-H-AUTH-001" in report
    assert "Assessment Intelligence v1.0 is certified as production-ready" in report
    assert "declared supported scope" in report
    assert "Teacher authority remains the final academic authority" in report
    assert "AEI preserved as the academic answer-evaluation pipeline" in report
    assert "approved evidence preserved as the downstream source of truth" in report

    for name in CERTIFICATION_REPORTS:
        assert name in report

    assert "ASSESSMENT_INTELLIGENCE_V1_PRODUCT_CLAIM_BOUNDARY.md" in report


def test_product_claim_boundary_allows_only_certified_supported_claims():
    boundary = _read(PRODUCT_CLAIM_BOUNDARY)

    allowed_terms = [
        "Grounded draft question-paper generation",
        "Teacher review and approval workflow",
        "Approved school-private question-bank reuse",
        "Explicit blueprint readiness where declared",
        "Rubric and model-answer readiness where declared",
        "Paper-to-evaluation linkage through approved papers and AEI",
        "Browser-proven teacher assessment workflow",
        "Approved-evidence-only downstream posture",
    ]
    for term in allowed_terms:
        assert term in boundary

    assert "certified supported scope" in boundary
    assert "Teacher" in boundary
    assert "AEI" in boundary
    assert "Approved Evidence" in boundary


def test_product_claim_boundary_blocks_universal_and_autonomous_claims():
    boundary = _read(PRODUCT_CLAIM_BOUNDARY)

    blocked_claims = [
        "universal board support",
        "universal grade support",
        "universal subject support",
        "universal blueprint support",
        "universal bilingual assessment generation",
        "universal multilingual assessment generation",
        "automatic question-paper translation as production-ready",
        "automatic rubric translation as production-ready",
        "automatic model-answer translation as production-ready",
        "autonomous paper approval",
        "autonomous answer grading",
        "autonomous OCR-based marks",
        "autonomous handwriting-based marks",
        "autonomous diagram grading",
        "autonomous visual/science grading",
        "public parent/student evidence before teacher approval",
        "downstream mastery updates from unapproved AI suggestions",
        "bypassing AEI for academic answer evaluation",
        "EUI source-of-truth adoption",
    ]
    for claim in blocked_claims:
        assert claim in boundary

    unsafe_wording = (
        "StudyNexs automatically creates and grades all assessments for every board,"
    )
    assert unsafe_wording in boundary


def test_final_certification_blocks_runtime_api_ui_and_authority_drift():
    report = _read(FINAL_CERTIFICATION)

    expected_boundary_results = [
        "| AEI answer-evaluation authority | Preserved |",
        "| Teacher final authority | Preserved |",
        "| Approved evidence downstream source | Preserved |",
        "| EUI source adoption | Not authorized / not introduced |",
        "| Schema changes | None |",
        "| API changes | None |",
        "| Production UI changes | None |",
        "| Runtime behavior changes | None |",
        "| Marks behavior changes | None |",
        "| Teacher-review routing changes | None |",
        "| Evidence-ledger behavior changes | None |",
        "| AI provider changes | None |",
        "| OCR behavior changes | None |",
        "| Translation behavior changes | None |",
    ]
    for result in expected_boundary_results:
        assert result in report

