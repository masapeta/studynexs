import json
from pathlib import Path

from app.modules.examinations.services.subject_capability_registry import SubjectCapabilityRegistry

GOLDEN_CASES_PATH = Path(__file__).parent / "golden" / "aei_v1" / "pilot_trust_cases.json"


def _load_golden_cases() -> dict:
    with GOLDEN_CASES_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_golden_harness_cases_are_schema_valid():
    data = _load_golden_cases()

    assert data["version"] == "aei-golden-v1"
    assert data["cases"]

    case_ids: set[str] = set()
    for case in data["cases"]:
        assert case["id"] not in case_ids
        case_ids.add(case["id"])
        assert case["subject"]
        assert case["capability"]
        assert "raw_answer" in case["input"]
        assert case["input"]["question_type"]
        assert isinstance(case["rubric"], dict)
        assert case["expected"]["capability_mode"]
        assert case["expected"]["reasoning_type"]
        assert isinstance(case["expected"]["manual_review_required"], bool)


def test_golden_harness_cases_match_subject_capability_registry():
    registry = SubjectCapabilityRegistry.load_default()
    data = _load_golden_cases()

    for case in data["cases"]:
        expected = case["expected"]
        capability = registry.resolve(case["subject"], case["capability"])

        assert capability.mode == expected["capability_mode"], case["id"]
        assert capability.teacher_review_required == expected["manual_review_required"], case["id"]


def test_golden_harness_contains_required_pilot_trust_families():
    data = _load_golden_cases()
    subjects = {case["subject"] for case in data["cases"]}
    capabilities = {case["capability"] for case in data["cases"]}

    assert {"mathematics", "chemistry", "biology", "geography"} <= subjects
    assert {"hindi", "telugu", "sanskrit"} <= subjects
    assert "numeric_equivalence" in capabilities
    assert "units" in capabilities
    assert "scientific_notation" in capabilities
    assert "reaction_balancing" in capabilities
    assert "diagrams" in capabilities
    assert "maps" in capabilities
    assert "handwriting_ocr" in capabilities
