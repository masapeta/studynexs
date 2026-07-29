import json
from datetime import datetime
from pathlib import Path

from app.modules.examinations.services.aei_activation_trust import (
    build_activation_trust_evidence,
    validate_and_merge_manual_review_acknowledgements,
)
from app.modules.examinations.services.aei_v1_evidence_ledger import (
    build_approved_evidence_metadata,
    contains_unsafe_evidence_key,
)
from app.modules.examinations.services.aei_v1_language_ocr_assist import (
    apply_language_ocr_assist_metadata,
)
from app.modules.examinations.services.aei_v1_math_normalization import (
    AEI_MATH_EVALUATION_METHOD,
    evaluate_math_normalization,
)
from app.modules.examinations.services.aei_v1_review_policy import (
    apply_review_policy_metadata,
)
from app.modules.examinations.services.aei_v1_visual_science_assist import (
    apply_visual_science_assist_metadata,
)
from app.modules.examinations.services.subject_capability_registry import SubjectCapabilityRegistry

GOLDEN_CASES_PATH = Path(__file__).parent / "golden" / "aei_v1" / "pilot_trust_cases.json"
BATCH_A_MATH_CASES_PATH = (
    Path(__file__).parent / "golden" / "aei_v1" / "batch_a_math_normalization_cases.json"
)
BATCH_B_REVIEW_CASES_PATH = (
    Path(__file__).parent / "golden" / "aei_v1" / "batch_b_review_policy_cases.json"
)
BATCH_C_APPROVED_EVIDENCE_CASES_PATH = (
    Path(__file__).parent / "golden" / "aei_v1" / "batch_c_approved_evidence_cases.json"
)
BATCH_D_LANGUAGE_OCR_CASES_PATH = (
    Path(__file__).parent / "golden" / "aei_v1" / "batch_d_language_ocr_assist_cases.json"
)
BATCH_E_VISUAL_SCIENCE_CASES_PATH = (
    Path(__file__).parent / "golden" / "aei_v1" / "batch_e_visual_science_assist_cases.json"
)
ACTIVATION_TRUST_CASES_PATH = (
    Path(__file__).parent / "golden" / "aei_v1" / "activation_trust_teacher_marked_cases.json"
)


def _load_golden_cases() -> dict:
    with GOLDEN_CASES_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_batch_a_math_cases() -> dict:
    with BATCH_A_MATH_CASES_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_batch_b_review_cases() -> dict:
    with BATCH_B_REVIEW_CASES_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_batch_c_approved_evidence_cases() -> dict:
    with BATCH_C_APPROVED_EVIDENCE_CASES_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_batch_d_language_ocr_cases() -> dict:
    with BATCH_D_LANGUAGE_OCR_CASES_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_batch_e_visual_science_cases() -> dict:
    with BATCH_E_VISUAL_SCIENCE_CASES_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_activation_trust_cases() -> dict:
    with ACTIVATION_TRUST_CASES_PATH.open("r", encoding="utf-8") as handle:
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


def test_batch_b_review_policy_golden_cases_execute_deterministically():
    data = _load_batch_b_review_cases()

    assert data["version"] == "aei-v1-batch-b-review-policy"
    case_ids: set[str] = set()
    for case in data["cases"]:
        assert case["id"] not in case_ids
        case_ids.add(case["id"])

        suggestion = dict(case["input"]["suggestion"])
        enriched = apply_review_policy_metadata({"1": suggestion})["1"]
        expected = case["expected"]

        assert enriched["manual_review_required"] is expected["manual_review_required"]
        assert enriched["capability_mode"] == expected["capability_mode"]
        if "confidence_reason" in expected:
            assert enriched["confidence_reason"] == expected["confidence_reason"]
        if "manual_review_reason" in expected:
            assert enriched["manual_review_reason"] == expected["manual_review_reason"]
        assert enriched["aei_v1_review_policy"]["batch"] == "B"


def test_batch_c_approved_evidence_golden_cases_execute_deterministically():
    data = _load_batch_c_approved_evidence_cases()

    assert data["version"] == "aei-v1-batch-c-approved-evidence"
    case_ids: set[str] = set()
    for case in data["cases"]:
        assert case["id"] not in case_ids
        case_ids.add(case["id"])

        case_input = case["input"]
        metadata = build_approved_evidence_metadata(
            evaluation_status=case_input["evaluation_status"],
            suggestions=case_input["suggestions"],
            teacher_overrides=case_input["teacher_overrides"],
            approved_by=case_input["approved_by"],
            approved_at=case_input["approved_at"],
        )
        expected = case["expected"]

        assert metadata["approved_evidence"] is expected["approved_evidence"], case["id"]
        assert (
            metadata["approved_for_downstream"] is expected["approved_for_downstream"]
        ), case["id"]
        assert metadata["question_count"] == expected["question_count"], case["id"]
        assert metadata["override_count"] == expected["override_count"], case["id"]
        assert (
            metadata["manual_review_required_count"]
            == expected["manual_review_required_count"]
        ), case["id"]
        assert (
            metadata["raw_student_answer_excluded"]
            is expected["raw_student_answer_excluded"]
        ), case["id"]
        assert (
            metadata["downstream_contract"]["source_of_truth"]
            == expected["source_of_truth"]
        ), case["id"]
        assert contains_unsafe_evidence_key(metadata) is False, case["id"]


def test_batch_d_language_ocr_assist_golden_cases_execute_deterministically():
    data = _load_batch_d_language_ocr_cases()

    assert data["version"] == "aei-v1-batch-d-language-ocr-assist"
    case_ids: set[str] = set()
    for case in data["cases"]:
        assert case["id"] not in case_ids
        case_ids.add(case["id"])

        case_input = case["input"]
        enriched = apply_language_ocr_assist_metadata(
            case_input["suggestions"],
            subject=case_input["subject"],
            answer_sources=case_input["answer_sources"],
            ocr_confidence_by_question=case_input["ocr_confidence_by_question"],
        )
        expected = case["expected"]
        suggestion = next(iter(enriched.values()))
        assist = suggestion["aei_v1_language_ocr_assist"]

        assert suggestion["answer_language"] == expected["answer_language"], case["id"]
        assert suggestion["detected_script"] == expected["detected_script"], case["id"]
        assert suggestion["code_mixed"] is expected["code_mixed"], case["id"]
        assert (
            suggestion.get("language_ocr_capability_mode")
            == expected["language_ocr_capability_mode"]
        ), case["id"]
        assert (
            suggestion["teacher_correction_required"]
            is expected["teacher_correction_required"]
        ), case["id"]
        assert (
            bool(suggestion.get("manual_review_required"))
            is expected["manual_review_required"]
        ), case["id"]
        assert (
            assist["autonomous_language_grading"]
            is expected["autonomous_language_grading"]
        ), case["id"]


def test_batch_e_visual_science_assist_golden_cases_execute_deterministically():
    data = _load_batch_e_visual_science_cases()

    assert data["version"] == "aei-v1-batch-e-visual-science-assist"
    case_ids: set[str] = set()
    for case in data["cases"]:
        assert case["id"] not in case_ids
        case_ids.add(case["id"])

        case_input = case["input"]
        enriched = apply_visual_science_assist_metadata(
            case_input["suggestions"],
            subject=case_input["subject"],
            question_contexts=case_input["question_contexts"],
        )
        expected = case["expected"]
        suggestion = next(iter(enriched.values()))
        assist = suggestion["aei_v1_visual_science_assist"]

        assert (
            suggestion["visual_science_capability_mode"]
            == expected["visual_science_capability_mode"]
        ), case["id"]
        assert (
            suggestion["visual_science_reasoning_type"]
            == expected["visual_science_reasoning_type"]
        ), case["id"]
        assert (
            bool(suggestion.get("manual_review_required"))
            is expected["manual_review_required"]
        ), case["id"]
        assert suggestion["assist_only"] is expected["assist_only"], case["id"]
        assert suggestion["checklist_only"] is expected["checklist_only"], case["id"]
        assert (
            assist["autonomous_visual_grading"]
            is expected["autonomous_visual_grading"]
        ), case["id"]
        assert (
            assist["autonomous_science_grading"]
            is expected["autonomous_science_grading"]
        ), case["id"]
        assert (
            assist["autonomous_marks_from_checklist"]
            is expected["autonomous_marks_from_checklist"]
        ), case["id"]


def test_activation_trust_teacher_marked_cases_execute_deterministically():
    data = _load_activation_trust_cases()

    assert data["version"] == "aei-activation-trust-teacher-marked-v1"
    case_ids: set[str] = set()
    for case in data["cases"]:
        assert case["id"] not in case_ids
        case_ids.add(case["id"])

        case_input = case["input"]
        expected = case["expected"]
        suggestions = case_input["suggestions"]
        teacher_overrides = case_input["teacher_overrides"]
        acknowledgements = case_input["manual_review_acknowledgements"]

        if expected["approval_requires_acknowledgement"] and acknowledgements:
            teacher_overrides = validate_and_merge_manual_review_acknowledgements(
                suggestions=suggestions,
                teacher_overrides=teacher_overrides,
                manual_review_acknowledgements=acknowledgements,
                reviewer_identifier="teacher-golden",
                review_timestamp=datetime.fromisoformat("2026-07-29T00:00:00+00:00"),
            )

        evidence = build_activation_trust_evidence(
            suggestions=suggestions,
            teacher_overrides=teacher_overrides,
            manual_review_acknowledgement_required=expected[
                "approval_requires_acknowledgement"
            ],
        )

        assert (
            evidence["manual_review_required_count"]
            == expected["manual_review_required_count"]
        ), case["id"]
        assert (
            evidence["manual_review_acknowledged_count"]
            == expected["manual_review_acknowledged_count"]
        ), case["id"]
        counts = evidence["capability_counts"]
        assert counts["math_normalization"] == expected["math_normalization_count"], case["id"]
        assert counts["language_ocr_assist"] == expected["language_ocr_assist_count"], case["id"]
        assert (
            counts["visual_science_assist"]
            == expected["visual_science_assist_count"]
        ), case["id"]
        assert evidence["autonomous_grading"] is False
        assert evidence["approved_evidence_source"] == "teacher_decision"
