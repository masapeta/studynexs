from pathlib import Path

from app.modules.examinations.services import subject_capability_registry
from app.modules.examinations.services.subject_capability_registry import (
    DEFAULT_REGISTRY_PATH,
    DEFAULT_REGISTRY_VERSION,
    SubjectCapabilityRegistry,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
AEI_DOC = REPO_ROOT / "docs" / "architecture" / "AEI.md"
AEI_ADR = (
    REPO_ROOT
    / "docs"
    / "decisions"
    / "ADR-0001-academic-evaluation-intelligence-architecture-freeze.md"
)
GOLDEN_CASES = Path(__file__).parent / "golden" / "aei_v1" / "pilot_trust_cases.json"


def test_aei_foundation_artifacts_exist():
    assert AEI_DOC.exists()
    assert AEI_ADR.exists()
    assert DEFAULT_REGISTRY_PATH.exists()
    assert GOLDEN_CASES.exists()


def test_registry_version_and_default_path_are_centralized():
    assert DEFAULT_REGISTRY_VERSION == "v1"
    assert DEFAULT_REGISTRY_PATH.name == "subject_capability_registry.v1.json"
    registry = SubjectCapabilityRegistry.load_default()
    assert registry.version == "aei-subject-capabilities-v1"


def test_registry_service_remains_dependency_light():
    source = Path(subject_capability_registry.__file__).read_text(encoding="utf-8").lower()

    forbidden_imports = [
        "fastapi",
        "sqlalchemy",
        "app.modules.ai",
        "answer_sheet_eval_service",
        "evaluation_engine",
    ]

    for forbidden in forbidden_imports:
        assert forbidden not in source


def test_aei_terms_are_consistent_in_architecture_docs():
    doc = AEI_DOC.read_text(encoding="utf-8")
    adr = AEI_ADR.read_text(encoding="utf-8")
    combined = f"{doc}\n{adr}"

    required_terms = [
        "Academic Evaluation Intelligence",
        "Subject Capability Registry",
        "AcademicAnswer",
        "Academic Understanding Engine",
        "Academic Reasoning Layer",
        "Evaluation Policy",
        "Teacher Review",
        "Evidence Ledger",
        "Golden Harness",
    ]

    for term in required_terms:
        assert term in combined
