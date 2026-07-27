"""AEI v1.0 Batch A deterministic Maths normalization adapter.

This module is the narrow runtime bridge from the existing answer-sheet
evaluation service into the certified AEI pipeline for supported Maths objective
answers. It reuses:

AcademicAnswer -> Understanding -> Reasoning -> Evaluation Policy

and only converts a supported deterministic match/mismatch into an existing
draft suggestion shape. It does not perform subjective grading, teacher review
routing, evidence-ledger persistence, UI work, or schema changes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.modules.examinations.schemas.academic_answer import AcademicAnswer
from app.modules.examinations.schemas.academic_reasoning_result import (
    AcademicReasoningResult,
)
from app.modules.examinations.schemas.policy_decision import PolicyDecision
from app.modules.examinations.services.academic_reasoning_engine import (
    AcademicReasoningEngine,
)
from app.modules.examinations.services.academic_understanding_engine import (
    AcademicUnderstandingEngine,
)
from app.modules.examinations.services.evaluation_policy import EvaluationPolicyEngine

AEI_MATH_EVALUATION_METHOD = "aei_v1_math_normalization"

_MATH_SUBJECTS = frozenset({"math", "maths", "mathematics"})
_SUPPORTED_QUESTION_TYPES = frozenset(
    {"short", "very_short", "fill_blank", "fill_in_blank", "objective"}
)
_MATCH_RESULTS = frozenset({"equivalent", "matched"})
_MISMATCH_RESULTS = frozenset({"not_equivalent", "not_matched"})
_SUPPORTED_REASONING_TYPES = frozenset(
    {"numeric_equivalence", "scientific_notation", "unit_interpretation"}
)
_UNIT_VALUE_PATTERN = re.compile(
    r"\s*[-+]?[\d\s.,/%eExX×^¼½¾⅓⅔⅛⅜⅝⅞]+?\s*[A-Za-z]+\s*"
)


@dataclass(frozen=True)
class AEIMathNormalizationResult:
    """Batch A draft-suggestion output for the existing evaluation service."""

    marks: float
    feedback: str
    confidence: float
    method: str
    misconception_hint: str | None
    metadata: dict[str, Any]


def evaluate_math_normalization(
    *,
    subject: str | None,
    q_type: str,
    student_answer: str,
    answer_key: str,
    max_marks: float,
    rubric: dict[str, Any],
    question: dict[str, Any] | None = None,
) -> AEIMathNormalizationResult | None:
    """Return a deterministic Maths suggestion, or ``None`` to keep legacy behavior."""

    if not _is_math_subject(subject) or q_type.lower() not in _SUPPORTED_QUESTION_TYPES:
        return None

    context = _reasoning_context(
        rubric=rubric,
        question=question or {},
        answer_key=answer_key,
    )
    if not _has_math_context(context):
        return None

    understood = AcademicUnderstandingEngine().understand(
        AcademicAnswer(
            raw_input=student_answer,
            subject="mathematics",
            question_type=q_type,
            metadata={"reasoning_context": context},
        )
    )
    reasoning = AcademicReasoningEngine().reason(understood)
    if reasoning.reasoning_type not in _SUPPORTED_REASONING_TYPES and student_answer.strip():
        return None

    confidence = _confidence_for_reasoning(reasoning)
    reasoning = _attach_confidence(reasoning, confidence)
    policy = EvaluationPolicyEngine().decide(reasoning)

    marks, feedback = _suggestion_from_reasoning(
        reasoning=reasoning,
        policy=policy,
        max_marks=max_marks,
    )
    return AEIMathNormalizationResult(
        marks=marks,
        feedback=feedback,
        confidence=confidence,
        method=AEI_MATH_EVALUATION_METHOD,
        misconception_hint=_misconception_hint(rubric, marks, max_marks),
        metadata=_suggestion_metadata(
            context=context,
            reasoning=reasoning,
            policy=policy,
        ),
    )


def _reasoning_context(
    *,
    rubric: dict[str, Any],
    question: dict[str, Any],
    answer_key: str,
) -> dict[str, Any]:
    context: dict[str, Any] = {}
    evaluation_config = _merged_config(rubric, question)

    candidate_answer = _first_non_empty(
        answer_key,
        rubric.get("answer_key"),
        question.get("answer_key"),
        evaluation_config.get("answer_key"),
    )
    if candidate_answer is not None:
        context["answer_key"] = candidate_answer

    acceptable_answers = _list_value(
        rubric.get("acceptable_answers"),
        question.get("acceptable_answers"),
        evaluation_config.get("acceptable_answers"),
    )
    if acceptable_answers:
        context["acceptable_answers"] = acceptable_answers

    tolerance = _first_non_empty(
        rubric.get("numeric_tolerance"),
        question.get("numeric_tolerance"),
        evaluation_config.get("numeric_tolerance"),
        rubric.get("tolerance"),
        question.get("tolerance"),
        evaluation_config.get("tolerance"),
    )
    if tolerance is not None:
        context["numeric_tolerance"] = tolerance

    units = _units_config(
        rubric=rubric,
        question=question,
        evaluation_config=evaluation_config,
        candidates=_candidate_answers(context),
    )
    if units:
        context["units"] = units

    return context


def _merged_config(rubric: dict[str, Any], question: dict[str, Any]) -> dict[str, Any]:
    config: dict[str, Any] = {}
    for source in (rubric.get("evaluation_config"), question.get("evaluation_config")):
        if isinstance(source, dict):
            config.update(source)
    return config


def _units_config(
    *,
    rubric: dict[str, Any],
    question: dict[str, Any],
    evaluation_config: dict[str, Any],
    candidates: list[str],
) -> dict[str, Any]:
    raw_units = evaluation_config.get("units")
    units = dict(raw_units) if isinstance(raw_units, dict) else {}

    allowed = _list_value(
        units.get("allowed"),
        units.get("allowed_units"),
        rubric.get("allowed_units"),
        question.get("allowed_units"),
        evaluation_config.get("allowed_units"),
    )
    required = _bool_value(
        units.get("required"),
        units.get("unit_required"),
        rubric.get("unit_required"),
        question.get("unit_required"),
        evaluation_config.get("unit_required"),
    )

    if required is None:
        required = any(_candidate_has_unit(candidate) for candidate in candidates)

    if allowed:
        units["allowed"] = allowed
    if required:
        units["required"] = True
    return units if units else {}


def _has_math_context(context: dict[str, Any]) -> bool:
    candidates = _candidate_answers(context)
    if not candidates:
        return False
    engine = AcademicReasoningEngine()
    for candidate in candidates:
        answer = AcademicAnswer(
            raw_input=candidate,
            subject="mathematics",
            question_type="short",
            metadata={"reasoning_context": context},
        )
        reasoning = engine.reason(AcademicUnderstandingEngine().understand(answer))
        if reasoning.reasoning_type in _SUPPORTED_REASONING_TYPES:
            return True
    return False


def _candidate_answers(context: dict[str, Any]) -> list[str]:
    candidates: list[str] = []
    answer_key = context.get("answer_key")
    if answer_key is not None:
        candidates.append(str(answer_key))
    acceptable = context.get("acceptable_answers", [])
    if isinstance(acceptable, list):
        candidates.extend(str(value) for value in acceptable if value is not None)
    return candidates


def _suggestion_from_reasoning(
    *,
    reasoning: AcademicReasoningResult,
    policy: PolicyDecision,
    max_marks: float,
) -> tuple[float, str]:
    if policy.manual_review_required or policy.decision != "supported":
        return 0.0, _manual_review_feedback(reasoning, policy)
    if reasoning.result in _MATCH_RESULTS:
        return max_marks, "Matches deterministic Maths answer equivalence."
    if reasoning.result in _MISMATCH_RESULTS:
        return 0.0, "Does not match deterministic Maths answer equivalence."
    return 0.0, _manual_review_feedback(reasoning, policy)


def _manual_review_feedback(
    reasoning: AcademicReasoningResult,
    policy: PolicyDecision,
) -> str:
    if reasoning.result == "not_applicable":
        return "Teacher review required: answer could not be normalized deterministically."
    if policy.manual_review_required:
        return f"Teacher review required: {policy.reason}"
    return "Teacher review required: Maths normalization was inconclusive."


def _confidence_for_reasoning(reasoning: AcademicReasoningResult) -> float:
    if reasoning.result in _MATCH_RESULTS:
        return 0.98
    if reasoning.result in _MISMATCH_RESULTS:
        return 0.92
    if reasoning.result == "not_applicable":
        return 0.35
    return 0.55


def _attach_confidence(
    reasoning: AcademicReasoningResult,
    confidence: float,
) -> AcademicReasoningResult:
    data = reasoning.model_dump()
    metadata = dict(data.get("metadata") or {})
    metadata["confidence"] = confidence
    metadata["confidence_threshold"] = 0.75
    data["metadata"] = metadata
    return AcademicReasoningResult.model_validate(data)


def _suggestion_metadata(
    *,
    context: dict[str, Any],
    reasoning: AcademicReasoningResult,
    policy: PolicyDecision,
) -> dict[str, Any]:
    manual_review_reason = policy.reason if policy.manual_review_required else None
    return {
        "normalized_answer": reasoning.interpreted_value,
        "matched_acceptable_answer": reasoning.matched_value,
        "confidence_reason": reasoning.explanation,
        "manual_review_required": policy.manual_review_required,
        "manual_review_reason": manual_review_reason,
        "evaluation_method": AEI_MATH_EVALUATION_METHOD,
        "aei_v1": {
            "batch": "A",
            "capability": reasoning.capability,
            "reasoning_type": reasoning.reasoning_type,
            "reasoning_result": reasoning.result,
            "policy_decision": policy.decision,
            "capability_mode": policy.capability_mode,
            "supported_capability": policy.supported_capability,
            "context_keys": sorted(context.keys()),
        },
    }


def _misconception_hint(rubric: dict[str, Any], marks: float, max_marks: float) -> str | None:
    if marks < max_marks and rubric.get("common_wrong_answers"):
        return str(rubric["common_wrong_answers"][0])
    return None


def _is_math_subject(subject: str | None) -> bool:
    if not subject:
        return False
    return _normalize_label(subject) in _MATH_SUBJECTS


def _candidate_has_unit(value: str) -> bool:
    return bool(_UNIT_VALUE_PATTERN.fullmatch(str(value)))


def _list_value(*values: Any) -> list[str]:
    for value in values:
        if isinstance(value, list):
            return [str(item) for item in value if item is not None and str(item).strip()]
        if isinstance(value, tuple):
            return [str(item) for item in value if item is not None and str(item).strip()]
    return []


def _first_non_empty(*values: Any) -> str | None:
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return None


def _bool_value(*values: Any) -> bool | None:
    for value in values:
        if isinstance(value, bool):
            return value
        if isinstance(value, str) and value.strip().lower() in {"true", "false"}:
            return value.strip().lower() == "true"
    return None


def _normalize_label(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")
