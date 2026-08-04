"""Track-A live benchmark runner — safety and scoring behavior.

These tests cover the parts that protect real student data: manifest
validation, repository-path refusal, and offline candidate scoring. No test
calls a provider.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

_RUNNER_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_ocr_track_a_benchmark.py"
_spec = importlib.util.spec_from_file_location("run_ocr_track_a_benchmark", _RUNNER_PATH)
runner = importlib.util.module_from_spec(_spec)
sys.modules["run_ocr_track_a_benchmark"] = runner
_spec.loader.exec_module(runner)


def _sample(**overrides):
    base = {
        "sample_id": "track-a-0001",
        "ground_truth": {"answers": {"1": "photosynthesis", "2": ""}},
        "question_texts": {"1": "Define photosynthesis", "2": "Draw the diagram"},
        "max_marks": {"1": 2, "2": 3},
    }
    base.update(overrides)
    return base


# ── Manifest safety ──────────────────────────────────────────────


def test_manifest_inside_repository_is_refused(tmp_path):
    inside = runner._REPO_ROOT / "tmp-manifest-test.json"
    with pytest.raises(runner.ManifestError, match="outside git"):
        try:
            inside.write_text("{}", encoding="utf-8")
            runner._load_manifest(inside)
        finally:
            inside.unlink(missing_ok=True)


def test_manifest_outside_repository_loads(tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"version": "track-a.real.v1", "samples": []}))
    payload = runner._load_manifest(manifest)
    assert payload["version"] == "track-a.real.v1"


def test_sample_with_identity_field_is_refused(tmp_path):
    with pytest.raises(runner.ManifestError, match="student_name"):
        runner.validate_live_sample(
            _sample(student_name="A Real Child"), index=0, base_dir=tmp_path
        )


def test_sample_without_anonymized_id_is_refused(tmp_path):
    with pytest.raises(runner.ManifestError, match="track-a-"):
        runner.validate_live_sample(
            _sample(sample_id="rahul-class7-page1"), index=0, base_dir=tmp_path
        )


def test_sample_image_inside_repository_is_refused(tmp_path):
    inside_image = runner._REPO_ROOT / "assets"
    with pytest.raises(runner.ManifestError, match="inside the repository"):
        runner.validate_live_sample(
            _sample(image_path=str(inside_image / "sheet.png")),
            index=0,
            base_dir=tmp_path,
        )


def test_sample_missing_image_is_refused(tmp_path):
    with pytest.raises(runner.ManifestError, match="does not exist"):
        runner.validate_live_sample(
            _sample(image_path=str(tmp_path / "missing.png")), index=0, base_dir=tmp_path
        )


def test_sample_without_ground_truth_is_refused(tmp_path):
    with pytest.raises(runner.ManifestError, match="ground_truth"):
        runner.validate_live_sample(
            {"sample_id": "track-a-0002"}, index=0, base_dir=tmp_path
        )


def test_valid_offline_sample_normalizes(tmp_path):
    sample = runner.validate_live_sample(_sample(), index=0, base_dir=tmp_path)
    assert sample["sample_id"] == "track-a-0001"
    assert sample["image_path"] is None
    assert sample["ground_truth"] == {"1": "photosynthesis", "2": ""}


# ── Offline candidate scoring ────────────────────────────────────


@pytest.mark.asyncio
async def test_offline_candidate_scores_from_manifest_outputs(tmp_path):
    """qwen/surya outputs embedded in the manifest are scored, not re-run."""
    sample = runner.validate_live_sample(
        _sample(
            candidate_outputs={
                "qwen2_5_vl_7b": {"answers": {"1": "photosynthesis", "2": ""}}
            }
        ),
        index=0,
        base_dir=tmp_path,
    )
    summary = await runner.run_candidate(
        "qwen2_5_vl_7b", [sample], dataset_version="track-a.test.v1", model="unused"
    )
    assert summary["execution_mode"] == "offline_scored"
    assert summary["per_question_extraction_accuracy"] == 1.0
    assert summary["failure_rate"] == 0.0
    assert summary["mean_latency_ms"] is None


@pytest.mark.asyncio
async def test_offline_candidate_without_outputs_counts_as_failure(tmp_path):
    sample = runner.validate_live_sample(_sample(), index=0, base_dir=tmp_path)
    summary = await runner.run_candidate(
        "surya_2", [sample], dataset_version="track-a.test.v1", model="unused"
    )
    assert summary["failure_rate"] == 1.0
    assert summary["schema_validity_rate"] == 0.0


@pytest.mark.asyncio
async def test_imperfect_offline_output_is_penalized(tmp_path):
    """A hallucinated answer on a blank question shows up in the metrics."""
    sample = runner.validate_live_sample(
        _sample(
            candidate_outputs={
                "qwen2_5_vl_7b": {
                    "answers": {"1": "photosynthesis", "2": "made up text"}
                }
            }
        ),
        index=0,
        base_dir=tmp_path,
    )
    summary = await runner.run_candidate(
        "qwen2_5_vl_7b", [sample], dataset_version="track-a.test.v1", model="unused"
    )
    assert summary["hallucination_count"] == 1
    assert summary["blank_answer_accuracy"] == 0.0
    assert "hallucination_detected" in summary["quality_flags"]


# ── Report output ────────────────────────────────────────────────


def test_report_is_aggregate_only(tmp_path):
    report_path = runner._write_report(
        tmp_path / "out",
        run_id="track-a-test-001",
        dataset_version="track-a.test.v1",
        sample_count=2,
        summaries=[
            {
                "candidate_label": "gemini_flash",
                "character_error_rate": 0.1,
                "word_error_rate": 0.2,
            }
        ],
    )
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["run_id"] == "track-a-test-001"
    assert payload["sample_count"] == 2
    # The report must never carry answer text keys.
    text = report_path.read_text(encoding="utf-8")
    assert "ground_truth" not in text
    assert "answers" not in text


# ── Production prompt reuse ──────────────────────────────────────


def test_benchmark_uses_production_prompt_shape():
    """The benchmark must exercise the exact prompt production OCR uses."""
    from app.modules.examinations.services.answer_sheet_vision import transcription_prompt

    prompt = transcription_prompt(
        [{"no": "1", "max_marks": 2}], {"1": {"question_text": "Define photosynthesis"}}
    )
    assert "Return JSON only" in prompt
    assert "Q1 (2 marks): Define photosynthesis" in prompt
