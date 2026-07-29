"""AEI Handwriting OCR Phase 2 Track-A benchmark foundation."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.core.config import Settings
from app.modules.examinations.services import handwriting_ocr_benchmark as bench


def test_character_and_word_error_rates_are_deterministic():
    assert bench.character_error_rate("cat", "cut") == pytest.approx(1 / 3)
    assert bench.word_error_rate("the cat sat", "the dog sat") == pytest.approx(1 / 3)


def test_score_candidate_answers_exact_match():
    metrics = bench.score_candidate_answers(
        ground_truth_answers={"1": "The SI unit is metre", "2": ""},
        candidate_answers={"1": " the  si unit is METRE ", "2": ""},
    )

    assert metrics.character_error_rate == 0
    assert metrics.word_error_rate == 0
    assert metrics.per_question_extraction_accuracy == 1
    assert metrics.blank_answer_accuracy == 1
    assert metrics.hallucination_count == 0
    assert metrics.schema_validity_rate == 1
    assert metrics.quality_flags == ()


def test_score_candidate_answers_detects_blank_hallucination_and_missing_question():
    metrics = bench.score_candidate_answers(
        ground_truth_answers={"1": "force changes motion", "2": "", "3": "metre"},
        candidate_answers={"1": "force changes motion", "2": "blank"},
    )

    assert metrics.per_question_extraction_accuracy == pytest.approx(1 / 3)
    assert metrics.blank_answer_accuracy == 0
    assert metrics.hallucination_count == 1
    assert "hallucination_detected" in metrics.quality_flags
    assert "missing_question_output" in metrics.quality_flags


def test_schema_invalid_candidate_scores_as_safe_empty_output():
    metrics = bench.score_candidate_answers(
        ground_truth_answers={"1": "force changes motion"},
        candidate_answers={"1": "ignored because schema invalid"},
        schema_valid=False,
    )

    assert metrics.schema_validity_rate == 0
    assert metrics.per_question_extraction_accuracy == 0
    assert "schema_invalid" in metrics.quality_flags


def test_summarize_candidate_run_aggregates_metrics():
    perfect = bench.score_candidate_answers(
        ground_truth_answers={"1": "answer"},
        candidate_answers={"1": "answer"},
    )
    noisy = bench.score_candidate_answers(
        ground_truth_answers={"1": "cat"},
        candidate_answers={"1": "cut"},
    )

    summary = bench.summarize_candidate_run(
        candidate_label="gemini_flash",
        dataset_version="track-a.synthetic.v1",
        sample_metrics=[perfect, noisy],
    )

    assert summary["candidate_label"] == "gemini_flash"
    assert summary["sample_count"] == 2
    assert summary["character_error_rate"] == pytest.approx((0 + 1 / 3) / 2)


def test_summarize_candidate_run_rejects_unknown_candidate():
    metrics = bench.score_candidate_answers(
        ground_truth_answers={"1": "answer"},
        candidate_answers={"1": "answer"},
    )

    with pytest.raises(ValueError, match="Unsupported OCR benchmark candidate"):
        bench.summarize_candidate_run(
            candidate_label="random_model",
            dataset_version="track-a.synthetic.v1",
            sample_metrics=[metrics],
        )


def test_repository_safe_track_a_manifest_fixture_validates():
    payload = _load_fixture()

    result = bench.validate_repository_safe_track_a_manifest(payload)

    assert result == {
        "version": "aei-handwriting-ocr-phase2-track-a.synthetic.v1",
        "sample_count": 2,
    }


def test_repository_safe_manifest_rejects_real_image_reference():
    payload = _load_fixture()
    payload["samples"][0]["image_ref"] = "D:/private/school/student-answer-sheet.jpg"

    with pytest.raises(ValueError, match="image_ref is not repository-safe"):
        bench.validate_repository_safe_track_a_manifest(payload)


def test_repository_safe_manifest_rejects_obvious_pii():
    payload = _load_fixture()
    payload["samples"][0]["ground_truth"]["answers"]["1"] = "student: Ravi 9876543210"

    with pytest.raises(ValueError, match="appears to contain PII"):
        bench.validate_repository_safe_track_a_manifest(payload)


def test_repository_safe_manifest_rejects_forbidden_real_data_keys():
    payload = _load_fixture()
    payload["samples"][0]["image_base64"] = "not allowed"

    with pytest.raises(ValueError, match="forbidden real-data keys"):
        bench.validate_repository_safe_track_a_manifest(payload)


def test_repository_safe_manifest_rejects_nested_forbidden_real_data_keys():
    payload = _load_fixture()
    payload["samples"][0]["candidate_outputs"]["gemini_flash"]["image_base64"] = "not allowed"

    with pytest.raises(ValueError, match="candidate_outputs.gemini_flash.image_base64"):
        bench.validate_repository_safe_track_a_manifest(payload)


def test_repository_safe_manifest_rejects_candidate_output_pii():
    payload = _load_fixture()
    payload["samples"][0]["candidate_outputs"]["gemini_flash"]["answers"]["1"] = (
        "roll no: 17 answer text"
    )

    with pytest.raises(ValueError, match="candidate_outputs.gemini_flash.answers"):
        bench.validate_repository_safe_track_a_manifest(payload)


def test_phase2_does_not_change_phase1_flag_default_or_runtime_source():
    eval_service = Path(
        "app/modules/examinations/services/answer_sheet_eval_service.py"
    ).read_text(encoding="utf-8")

    assert Settings.model_fields["AEI_HANDWRITING_OCR_PHASE1_ENABLED"].default is False
    assert "handwriting_ocr_benchmark" not in eval_service


def _load_fixture() -> dict:
    path = (
        Path(__file__).resolve().parent
        / "golden"
        / "aei_v1"
        / "handwriting_ocr_phase2_track_a_benchmark_cases.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))
