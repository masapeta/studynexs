"""Repository-safe benchmark helpers for AEI Handwriting OCR Phase 2.

Phase 2 is a validation foundation only.  These helpers score already-produced
OCR candidate outputs against teacher-verified transcription truth.  They do not
call Gemini, Qwen, Surya, or any other provider, and they are not imported by the
production answer-sheet evaluation path.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any, Mapping

OCR_BENCHMARK_CANDIDATES = frozenset({"gemini_flash", "qwen2_5_vl_7b", "surya_2"})

_SAFE_SAMPLE_ID = re.compile(r"^(?:synthetic-)?track-a-[a-z0-9][a-z0-9-]{2,80}$")
_REPOSITORY_SAFE_IMAGE_PREFIXES = ("synthetic://", "fixture://", "template://")
_FORBIDDEN_REAL_DATA_KEYS = frozenset(
    {
        "image_bytes",
        "image_base64",
        "raw_image",
        "student_name",
        "student_full_name",
        "roll_number",
        "admission_number",
        "phone",
        "phone_number",
        "school_name",
    }
)
_OBVIOUS_PII = re.compile(
    r"([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}|"
    r"(?:\+?91[-\s]?)?[6-9]\d{9}|"
    r"\b(?:student|school|roll\s*no|admission\s*no)\s*[:#])",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class OCRBenchmarkMetrics:
    """Aggregate transcription metrics for one OCR candidate output."""

    question_count: int
    character_error_rate: float
    word_error_rate: float
    per_question_extraction_accuracy: float
    blank_answer_accuracy: float
    hallucination_count: int
    hallucination_rate: float
    schema_validity_rate: float
    exact_match_count: int
    blank_answer_count: int
    quality_flags: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def character_error_rate(expected: str, observed: str) -> float:
    """Return deterministic character error rate after whitespace normalization."""

    expected_text = _normalize_text(expected)
    observed_text = _normalize_text(observed)
    return _safe_rate(_levenshtein(tuple(expected_text), tuple(observed_text)), len(expected_text))


def word_error_rate(expected: str, observed: str) -> float:
    """Return deterministic word error rate after whitespace normalization."""

    expected_words = tuple(_normalize_text(expected).split())
    observed_words = tuple(_normalize_text(observed).split())
    return _safe_rate(_levenshtein(expected_words, observed_words), len(expected_words))


def score_candidate_answers(
    *,
    ground_truth_answers: Mapping[str, str],
    candidate_answers: Mapping[str, str] | None,
    schema_valid: bool = True,
) -> OCRBenchmarkMetrics:
    """Score one OCR candidate output against teacher-verified transcription truth.

    The score is transcription-only. It does not grade, route teacher review, or
    make provider-adoption decisions.
    """

    truth = _normalize_answer_map(ground_truth_answers)
    observed = _normalize_answer_map(candidate_answers or {}) if schema_valid else {}
    question_ids = tuple(sorted(truth))
    question_count = len(question_ids)

    char_errors = 0
    char_total = 0
    word_errors = 0
    word_total = 0
    exact_matches = 0
    blank_total = 0
    blank_matches = 0
    hallucinations = 0

    for qid in question_ids:
        expected = truth[qid]
        actual = observed.get(qid, "")

        char_errors += _levenshtein(tuple(expected), tuple(actual))
        char_total += len(expected)

        expected_words = tuple(expected.split())
        actual_words = tuple(actual.split())
        word_errors += _levenshtein(expected_words, actual_words)
        word_total += len(expected_words)

        if expected == actual:
            exact_matches += 1

        if not expected:
            blank_total += 1
            if not actual:
                blank_matches += 1
            else:
                hallucinations += 1

    for qid, actual in observed.items():
        if qid not in truth and actual:
            hallucinations += 1

    flags: list[str] = []
    if not schema_valid:
        flags.append("schema_invalid")
    if hallucinations:
        flags.append("hallucination_detected")
    if any(qid not in observed for qid in question_ids):
        flags.append("missing_question_output")

    denominator_for_hallucination = max(1, question_count + len(set(observed) - set(truth)))

    return OCRBenchmarkMetrics(
        question_count=question_count,
        character_error_rate=_safe_rate(char_errors, char_total),
        word_error_rate=_safe_rate(word_errors, word_total),
        per_question_extraction_accuracy=_safe_rate(exact_matches, question_count),
        blank_answer_accuracy=1.0 if blank_total == 0 else _safe_rate(blank_matches, blank_total),
        hallucination_count=hallucinations,
        hallucination_rate=_safe_rate(hallucinations, denominator_for_hallucination),
        schema_validity_rate=1.0 if schema_valid else 0.0,
        exact_match_count=exact_matches,
        blank_answer_count=blank_total,
        quality_flags=tuple(flags),
    )


def summarize_candidate_run(
    *,
    candidate_label: str,
    dataset_version: str,
    sample_metrics: list[OCRBenchmarkMetrics],
) -> dict[str, Any]:
    """Aggregate sample metrics for a repository-safe benchmark report."""

    if candidate_label not in OCR_BENCHMARK_CANDIDATES:
        raise ValueError(f"Unsupported OCR benchmark candidate: {candidate_label}")
    if not dataset_version.strip():
        raise ValueError("dataset_version is required")
    if not sample_metrics:
        raise ValueError("sample_metrics must not be empty")

    count = len(sample_metrics)
    return {
        "candidate_label": candidate_label,
        "dataset_version": dataset_version.strip(),
        "sample_count": count,
        "character_error_rate": _mean(m.character_error_rate for m in sample_metrics),
        "word_error_rate": _mean(m.word_error_rate for m in sample_metrics),
        "per_question_extraction_accuracy": _mean(
            m.per_question_extraction_accuracy for m in sample_metrics
        ),
        "blank_answer_accuracy": _mean(m.blank_answer_accuracy for m in sample_metrics),
        "hallucination_rate": _mean(m.hallucination_rate for m in sample_metrics),
        "schema_validity_rate": _mean(m.schema_validity_rate for m in sample_metrics),
        "hallucination_count": sum(m.hallucination_count for m in sample_metrics),
        "quality_flags": tuple(
            sorted({flag for metric in sample_metrics for flag in metric.quality_flags})
        ),
    }


def validate_repository_safe_track_a_manifest(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a repository-safe Track-A manifest without accepting real data.

    This validator is intentionally conservative. It is for committed synthetic
    fixtures and schema examples. Real Track-A data must live outside git and
    should be processed only by separately authorized offline benchmark runs.
    """

    errors: list[str] = []
    version = str(payload.get("version") or "").strip()
    samples = payload.get("samples")

    if not version:
        errors.append("version is required")
    if not isinstance(samples, list) or not samples:
        errors.append("samples must be a non-empty list")
    elif samples:
        for index, sample in enumerate(samples):
            _validate_repository_safe_sample(sample, index=index, errors=errors)

    if errors:
        raise ValueError("; ".join(errors))

    return {
        "version": version,
        "sample_count": len(samples if isinstance(samples, list) else []),
    }


def _validate_repository_safe_sample(sample: Any, *, index: int, errors: list[str]) -> None:
    if not isinstance(sample, Mapping):
        errors.append(f"samples[{index}] must be an object")
        return

    forbidden_keys = _find_forbidden_real_data_keys(sample)
    if forbidden_keys:
        errors.append(f"samples[{index}] contains forbidden real-data keys: {forbidden_keys}")

    sample_id = str(sample.get("sample_id") or "").strip()
    if not _SAFE_SAMPLE_ID.fullmatch(sample_id):
        errors.append(f"samples[{index}].sample_id is not a safe Track-A identifier")

    image_ref = str(sample.get("image_ref") or "").strip()
    if image_ref and not image_ref.startswith(_REPOSITORY_SAFE_IMAGE_PREFIXES):
        errors.append(f"samples[{index}].image_ref is not repository-safe")

    ground_truth = sample.get("ground_truth")
    answers = ground_truth.get("answers") if isinstance(ground_truth, Mapping) else None
    if not isinstance(answers, Mapping):
        errors.append(f"samples[{index}].ground_truth.answers is required")
        return

    for qid, answer in answers.items():
        if not str(qid).strip():
            errors.append(f"samples[{index}] contains blank question id")
        if _OBVIOUS_PII.search(str(answer or "")):
            errors.append(f"samples[{index}].ground_truth.answers appears to contain PII")

    candidate_outputs = sample.get("candidate_outputs")
    if isinstance(candidate_outputs, Mapping):
        for candidate, output in candidate_outputs.items():
            if not isinstance(output, Mapping):
                continue
            candidate_answers = output.get("answers")
            if not isinstance(candidate_answers, Mapping):
                continue
            for answer in candidate_answers.values():
                if _OBVIOUS_PII.search(str(answer or "")):
                    errors.append(
                        f"samples[{index}].candidate_outputs.{candidate}.answers "
                        "appears to contain PII"
                    )


def _normalize_answer_map(values: Mapping[str, str]) -> dict[str, str]:
    return {
        str(key).strip(): _normalize_text(str(value or ""))
        for key, value in values.items()
        if str(key).strip()
    }


def _find_forbidden_real_data_keys(value: Any, *, prefix: str = "") -> list[str]:
    if isinstance(value, Mapping):
        matches: list[str] = []
        for key, nested in value.items():
            key_text = str(key)
            path = f"{prefix}.{key_text}" if prefix else key_text
            if key_text in _FORBIDDEN_REAL_DATA_KEYS:
                matches.append(path)
            matches.extend(_find_forbidden_real_data_keys(nested, prefix=path))
        return sorted(matches)
    if isinstance(value, list):
        matches = []
        for index, nested in enumerate(value):
            path = f"{prefix}[{index}]" if prefix else f"[{index}]"
            matches.extend(_find_forbidden_real_data_keys(nested, prefix=path))
        return sorted(matches)
    return []


def _normalize_text(value: str) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _safe_rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0 if numerator == 0 else 1.0
    return numerator / denominator


def _mean(values: Any) -> float:
    collected = tuple(values)
    return sum(collected) / len(collected)


def _levenshtein(expected: tuple[Any, ...], observed: tuple[Any, ...]) -> int:
    if expected == observed:
        return 0
    if not expected:
        return len(observed)
    if not observed:
        return len(expected)

    previous = list(range(len(observed) + 1))
    for index, expected_item in enumerate(expected, start=1):
        current = [index]
        for observed_index, observed_item in enumerate(observed, start=1):
            insert_cost = current[observed_index - 1] + 1
            delete_cost = previous[observed_index] + 1
            substitute_cost = previous[observed_index - 1] + (
                0 if expected_item == observed_item else 1
            )
            current.append(min(insert_cost, delete_cost, substitute_cost))
        previous = current
    return previous[-1]
