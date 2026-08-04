"""AEI Handwriting OCR Phase 2 — live Track-A benchmark runner.

Authorized by AEI-HANDWRITING-OCR-PHASE2-LIVE-RUN-AUTH-001. This script:

- loads a secured Track-A manifest from OUTSIDE the repository;
- transcribes each page with the requested candidates and scores the output
  against teacher-verified truth using the certified Phase 2 metrics;
- writes an AGGREGATE-ONLY report next to the manifest (never into git).

Candidate execution:

- ``gemini_flash`` runs live through the StudyNexs AI Gateway using the exact
  production transcription prompt and parser, so the benchmark measures the
  pipeline production would use — not a bespoke one.
- ``qwen2_5_vl_7b`` / ``surya_2`` are scored from pre-produced outputs embedded
  in the manifest (``candidate_outputs.<label>.answers``). Those models run on
  separate GPU environments; this runner scores their outputs identically
  rather than pretending to host them.

Data handling (binding, from the authorization contract):

- raw OCR text from real sheets is NEVER logged or printed;
- outputs are refused inside the repository working tree;
- per-sample raw outputs are NOT written unless --keep-raw is passed, and then
  only to the secured output directory for audit.

Usage:
    python scripts/run_ocr_track_a_benchmark.py \
        --manifest D:/secure/track-a/manifest.json \
        --candidates gemini_flash \
        --run-id track-a-live-001
"""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import sys
import time
from datetime import date
from pathlib import Path
from typing import Any

# Allow `python scripts/...` execution from apps/api.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.modules.examinations.services.handwriting_ocr_benchmark import (  # noqa: E402
    OCR_BENCHMARK_CANDIDATES,
    OCRBenchmarkMetrics,
    score_candidate_answers,
    summarize_candidate_run,
)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
_MIME_BY_SUFFIX = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}
_LIVE_CANDIDATES = {"gemini_flash"}


class ManifestError(ValueError):
    """The secured manifest is not usable; the message never quotes answer text."""


def _load_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ManifestError(f"Manifest not found: {path}")
    if _is_inside_repo(path):
        raise ManifestError(
            "Manifest lives inside the repository working tree. Real Track-A "
            "data must stay outside git — move it to secured storage."
        )
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ManifestError(f"Manifest is not valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ManifestError("Manifest root must be an object")
    return payload


def _is_inside_repo(path: Path) -> bool:
    try:
        path.resolve().relative_to(_REPO_ROOT)
        return True
    except ValueError:
        return False


def validate_live_sample(sample: Any, *, index: int, base_dir: Path) -> dict[str, Any]:
    """Validate one secured sample. Errors describe structure, never content."""
    if not isinstance(sample, dict):
        raise ManifestError(f"samples[{index}] must be an object")

    sample_id = str(sample.get("sample_id") or "").strip()
    if not sample_id.startswith("track-a-"):
        raise ManifestError(
            f"samples[{index}].sample_id must be an anonymized 'track-a-*' identifier"
        )

    for key in ("student_name", "roll_number", "admission_number", "school_name", "phone"):
        if key in sample:
            raise ManifestError(
                f"samples[{index}] carries identity field '{key}' — redact it "
                "before benchmarking (data handling guide §4)"
            )

    truth = sample.get("ground_truth")
    answers = truth.get("answers") if isinstance(truth, dict) else None
    if not isinstance(answers, dict) or not answers:
        raise ManifestError(f"samples[{index}].ground_truth.answers is required")

    image_path: Path | None = None
    image_ref = str(sample.get("image_path") or "").strip()
    if image_ref:
        candidate_path = Path(image_ref)
        image_path = (
            candidate_path if candidate_path.is_absolute() else (base_dir / image_ref).resolve()
        )
        if _is_inside_repo(image_path):
            raise ManifestError(
                f"samples[{index}].image_path points inside the repository — "
                "real sheets must not enter git"
            )
        if not image_path.exists():
            raise ManifestError(f"samples[{index}].image_path does not exist")
        if image_path.suffix.lower() not in _IMAGE_SUFFIXES:
            raise ManifestError(
                f"samples[{index}].image_path must be one of {sorted(_IMAGE_SUFFIXES)}"
            )

    return {
        "sample_id": sample_id,
        "image_path": image_path,
        "ground_truth": {str(k): str(v or "") for k, v in answers.items()},
        "question_texts": {
            str(k): str(v or "")
            for k, v in (sample.get("question_texts") or {}).items()
        },
        "max_marks": {
            str(k): v for k, v in (sample.get("max_marks") or {}).items()
        },
        "candidate_outputs": sample.get("candidate_outputs") or {},
    }


def _prompt_inputs(sample: dict[str, Any]) -> tuple[list[dict], dict[str, dict]]:
    """Build the production prompt inputs from the manifest's question context."""
    question_schema = [
        {"no": qid, "max_marks": sample["max_marks"].get(qid, "?")}
        for qid in sorted(sample["ground_truth"], key=_qsort)
    ]
    rubrics = {
        qid: {"question_text": sample["question_texts"].get(qid, "")}
        for qid in sample["ground_truth"]
    }
    return question_schema, rubrics


def _qsort(qid: str):
    return (0, int(qid)) if qid.isdigit() else (1, qid)


async def _transcribe_live(
    sample: dict[str, Any], *, model: str
) -> tuple[dict[str, str], bool, float | None]:
    """Gemini Flash through the gateway. Returns (answers, schema_valid, latency_ms)."""
    # Imported here so offline scoring works without provider SDKs installed.
    from app.modules.ai.gateway import LLMImage, LLMMessage, generate_llm
    from app.modules.examinations.services.answer_sheet_vision import (
        parse_vision_answers,
        transcription_prompt,
    )

    image_path: Path = sample["image_path"]
    question_schema, rubrics = _prompt_inputs(sample)
    prompt = transcription_prompt(question_schema, rubrics)
    mime = _MIME_BY_SUFFIX[image_path.suffix.lower()]
    messages = [
        LLMMessage(
            role="user",
            content=prompt,
            images=[LLMImage(data=image_path.read_bytes(), mime_type=mime)],
        )
    ]
    started = time.perf_counter()
    result = await generate_llm(
        messages,
        model=model,
        provider_name="gemini",
        temperature=0.1,
        max_tokens=4096,
        json_mode=True,
        feature="ocr_track_a_benchmark",
        caller="run_ocr_track_a_benchmark",
    )
    latency_ms = (time.perf_counter() - started) * 1000
    answers = parse_vision_answers(result.text)
    return answers, bool(answers), latency_ms


def _offline_answers(sample: dict[str, Any], candidate: str) -> tuple[dict[str, str], bool]:
    output = sample["candidate_outputs"].get(candidate)
    answers = output.get("answers") if isinstance(output, dict) else None
    if not isinstance(answers, dict):
        return {}, False
    return {str(k): str(v or "") for k, v in answers.items()}, True


async def run_candidate(
    candidate: str,
    samples: list[dict[str, Any]],
    *,
    dataset_version: str,
    model: str,
) -> dict[str, Any]:
    per_sample: list[OCRBenchmarkMetrics] = []
    latencies: list[float] = []
    failures = 0

    for sample in samples:
        answers: dict[str, str] = {}
        schema_valid = False
        latency_ms: float | None = None

        if candidate in _LIVE_CANDIDATES:
            if sample["image_path"] is None:
                failures += 1
            else:
                try:
                    answers, schema_valid, latency_ms = await _transcribe_live(
                        sample, model=model
                    )
                except Exception:
                    # Never print the exception payload — it may echo prompt content.
                    failures += 1
        else:
            answers, schema_valid = _offline_answers(sample, candidate)
            if not schema_valid:
                failures += 1

        per_sample.append(
            score_candidate_answers(
                ground_truth_answers=sample["ground_truth"],
                candidate_answers=answers,
                schema_valid=schema_valid,
            )
        )
        if latency_ms is not None:
            latencies.append(latency_ms)

        # Progress without content: sample id + flags only.
        flags = ",".join(per_sample[-1].quality_flags) or "ok"
        print(f"  {sample['sample_id']}: {candidate} -> {flags}")

    summary = summarize_candidate_run(
        candidate_label=candidate,
        dataset_version=dataset_version,
        sample_metrics=per_sample,
    )
    summary["failure_rate"] = round(failures / len(samples), 4) if samples else 0.0
    summary["mean_latency_ms"] = (
        round(statistics.mean(latencies), 1) if latencies else None
    )
    summary["execution_mode"] = (
        "live_gateway" if candidate in _LIVE_CANDIDATES else "offline_scored"
    )
    return summary


def _write_report(
    out_dir: Path,
    *,
    run_id: str,
    dataset_version: str,
    sample_count: int,
    summaries: list[dict[str, Any]],
) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "run_id": run_id,
        "run_date": date.today().isoformat(),
        "dataset_version": dataset_version,
        "sample_count": sample_count,
        "candidates": summaries,
        "note": (
            "Aggregate-only Track-A benchmark output. Repository-safe fields only; "
            "raw transcriptions were not persisted."
        ),
    }
    report_path = out_dir / f"{run_id}-aggregate.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return report_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, help="Secured manifest path (outside git)")
    parser.add_argument(
        "--candidates",
        default="gemini_flash",
        help="Comma-separated candidate labels: " + ", ".join(sorted(OCR_BENCHMARK_CANDIDATES)),
    )
    parser.add_argument("--run-id", required=True, help="e.g. track-a-live-001")
    parser.add_argument(
        "--model",
        default="",
        help="Gemini model override (default: AI_VISION_PRIMARY_MODEL or gemini-3.6-flash)",
    )
    parser.add_argument(
        "--out", default="", help="Output directory (default: alongside the manifest)"
    )
    parser.add_argument(
        "--limit", type=int, default=0, help="Benchmark only the first N samples (smoke run)"
    )
    args = parser.parse_args()

    candidates = [c.strip() for c in args.candidates.split(",") if c.strip()]
    unknown = set(candidates) - OCR_BENCHMARK_CANDIDATES
    if unknown:
        print(f"Unknown candidates: {sorted(unknown)}", file=sys.stderr)
        return 2

    manifest_path = Path(args.manifest)
    try:
        payload = _load_manifest(manifest_path)
        dataset_version = str(payload.get("version") or "").strip()
        if not dataset_version:
            raise ManifestError("Manifest 'version' is required (e.g. track-a.real.v1)")
        raw_samples = payload.get("samples")
        if not isinstance(raw_samples, list) or not raw_samples:
            raise ManifestError("Manifest 'samples' must be a non-empty list")
        samples = [
            validate_live_sample(s, index=i, base_dir=manifest_path.parent)
            for i, s in enumerate(raw_samples)
        ]
    except ManifestError as exc:
        print(f"Manifest rejected: {exc}", file=sys.stderr)
        return 2

    if args.limit > 0:
        samples = samples[: args.limit]

    out_dir = Path(args.out) if args.out else manifest_path.parent / "benchmark-output"
    if _is_inside_repo(out_dir):
        print(
            "Output directory is inside the repository — refused. Benchmark output "
            "belongs in secured storage; copy only the reviewed aggregate into git.",
            file=sys.stderr,
        )
        return 2

    from app.core.config import get_settings

    model = args.model or get_settings().AI_VISION_PRIMARY_MODEL or "gemini-3.6-flash"
    if "gemini_flash" in candidates and not get_settings().GEMINI_API_KEY:
        print("gemini_flash requested but GEMINI_API_KEY is not set.", file=sys.stderr)
        return 2

    print(f"Track-A benchmark {args.run_id}: {len(samples)} sample(s), dataset {dataset_version}")
    summaries: list[dict[str, Any]] = []
    for candidate in candidates:
        print(f"Candidate: {candidate}")
        summaries.append(
            asyncio.run(
                run_candidate(
                    candidate, samples, dataset_version=dataset_version, model=model
                )
            )
        )

    report_path = _write_report(
        out_dir,
        run_id=args.run_id,
        dataset_version=dataset_version,
        sample_count=len(samples),
        summaries=summaries,
    )

    print("\nAggregate results:")
    for summary in summaries:
        print(
            f"  {summary['candidate_label']}: "
            f"CER {summary['character_error_rate']:.3f} · "
            f"WER {summary['word_error_rate']:.3f} · "
            f"extraction {summary['per_question_extraction_accuracy']:.3f} · "
            f"hallucination {summary['hallucination_rate']:.3f} · "
            f"failures {summary['failure_rate']:.3f}"
        )
    print(f"\nAggregate report: {report_path}")
    print("Next: fill the report template from this aggregate and submit for review.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
