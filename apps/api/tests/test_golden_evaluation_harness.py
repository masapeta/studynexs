import json
from pathlib import Path

from app.modules.examinations.services.aei_v1_math_normalization import (
    AEI_MATH_EVALUATION_METHOD,
    evaluate_math_normalization,
)
from app.modules.examinations.services.subject_capability_registry import SubjectCapabilityRegistry

GOLDEN_CASES_PATH = Path(__file__).parent / "golden" / "aei_v1" / "pilot_trust_cases.json"
BATCH_A_MATH_CASES_PATH = (
    Path(__file__).parent / "golden" / "aei_v1" / "batch_a_math_normalization_cases.json"
)


def _load_golden_cases() -> dict:
    with GOLDEN_CASES_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_batch_a_math_cases() -> dict:
    with BATCH_A_MATH_CASES_PATH.open("r", encoding="utf-8") as handle:
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


def test_batch_a_math_normalization_golden_cases_execute_deterministically():
    data = _load_batch_a_math_cases()

    assert data["version"] == "aei-v1-batch-a-math-normalization"
    case_ids: set[str] = set()
    for case in data["cases"]:
        assert case["id"] not in case_ids
        case_ids.add(case["id"])

        rubric = dict(case["rubric"])
        max_marks = float(rubric.pop("max_marks"))
        result = evaluate_math_normalization(
            subject=case["subject"],
            q_type=case["input"]["question_type"],
            student_answer=case["input"]["raw_answer"],
            answer_key=str(rubric.get("answer_key") or ""),
            max_marks=max_marks,
            rubric=rubric,
        )

        assert result is not None, case["id"]
        assert result.method == AEI_MATH_EVALUATION_METHOD
        assert result.marks == case["expected"]["marks"], case["id"]
        assert (
            result.metadata["manual_review_required"]
            is case["expected"]["manual_review_required"]
        ), case["id"]
        if "normalized_answer" in case["expected"]:
            assert result.metadata["normalized_answer"] == case["expected"]["normalized_answer"]
        if "matched_acceptable_answer" in case["expected"]:
            assert (
                result.metadata["matched_acceptable_answer"]
                == case["expected"]["matched_acceptable_answer"]
            )
