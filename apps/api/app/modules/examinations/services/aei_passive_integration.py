"""AEI Integration Wave 1 passive observer.

Wave 1 executes the complete AEI pipeline alongside the existing answer-sheet
evaluation flow. It captures outputs for validation only and must never influence
marks, gradebook, mastery, teacher-visible behavior, or runtime success.
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from threading import Lock
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.platform_metrics import platform_metrics
from app.db.models.examination import Exam
from app.db.models.question_paper import QuestionPaper
from app.modules.ai.services.question_bank_service import fetch_rubrics_for_paper
from app.modules.examinations.schemas.academic_answer import AcademicAnswer
from app.modules.examinations.schemas.academic_reasoning_result import (
    AcademicReasoningResult,
)
from app.modules.examinations.services.academic_reasoning_engine import (
    AcademicReasoningEngine,
)
from app.modules.examinations.services.academic_understanding_engine import (
    AcademicUnderstandingEngine,
)
from app.modules.examinations.services.evaluation_policy import EvaluationPolicyEngine
from app.modules.examinations.services.teacher_review import create_teacher_review_decision

logger = structlog.get_logger()

AEI_PASSIVE_METRIC_TASK = "aei_passive_integration"
AEI_SHADOW_METRIC_TASK = "aei_shadow_mode"
DEFAULT_CAPTURE_LIMIT = 100
SHADOW_CONFIDENCE_THRESHOLD = 0.75


@dataclass(frozen=True)
class AEIShadowQuestionComparison:
    """One question's Wave 2 production-vs-AEI comparison."""

    question_no: str
    comparison_status: str
    difference_categories: tuple[str, ...]
    production_method: str
    production_confidence: float | None
    production_review_signal: bool
    production_marks_suggested: float | None
    production_max_marks: float | None
    aei_decision: str
    aei_manual_review_required: bool
    aei_supported_capability: bool
    metadata: dict[str, Any]


@dataclass(frozen=True)
class AEIShadowEvaluationComparison:
    """Bounded Wave 2 shadow comparison summary for one evaluation."""

    question_count: int
    agreement_count: int
    difference_count: int
    unsupported_capability_count: int
    manual_review_delta_count: int
    comparisons: tuple[AEIShadowQuestionComparison, ...]


@dataclass(frozen=True)
class AEIPassiveQuestionCapture:
    """One question's passive AEI result."""

    question_no: str
    academic_answer: dict[str, Any]
    academic_reasoning_result: dict[str, Any]
    policy_decision: dict[str, Any]
    teacher_review_decision: dict[str, Any]


@dataclass(frozen=True)
class AEIPassiveEvaluationCapture:
    """One evaluation's bounded passive AEI capture."""

    evaluation_id: str
    school_id: str
    exam_id: str
    student_id: str
    question_count: int
    duration_ms: float
    questions: tuple[AEIPassiveQuestionCapture, ...]
    shadow_comparison: AEIShadowEvaluationComparison | None = None


class AEIPassiveCaptureRegistry:
    """Bounded in-memory passive capture registry for Wave 1 validation."""

    def __init__(self, *, limit: int = DEFAULT_CAPTURE_LIMIT) -> None:
        self._captures: deque[AEIPassiveEvaluationCapture] = deque(maxlen=limit)
        self._lock = Lock()

    def record(self, capture: AEIPassiveEvaluationCapture) -> None:
        with self._lock:
            self._captures.append(capture)

    def snapshot(self) -> list[AEIPassiveEvaluationCapture]:
        with self._lock:
            return list(self._captures)

    def clear(self) -> None:
        with self._lock:
            self._captures.clear()


aei_passive_capture_registry = AEIPassiveCaptureRegistry()


async def observe_answer_sheet_evaluation(
    *,
    enabled: bool,
    db: AsyncSession,
    evaluation_id: UUID,
    school_id: UUID,
    exam: Exam,
    student_id: UUID,
    student_answers: dict[str, str],
    suggestions: dict[str, dict],
    shadow_enabled: bool = False,
) -> AEIPassiveEvaluationCapture | None:
    """Run AEI passively and isolate all AEI failures from production evaluation."""

    if not enabled and not shadow_enabled:
        return None

    started = time.perf_counter()
    platform_metrics.record_job_event(task=AEI_PASSIVE_METRIC_TASK, status="invoked")
    if shadow_enabled:
        platform_metrics.record_job_event(task=AEI_SHADOW_METRIC_TASK, status="invoked")
    try:
        capture = await _build_passive_capture(
            db=db,
            evaluation_id=evaluation_id,
            school_id=school_id,
            exam=exam,
            student_id=student_id,
            student_answers=dict(student_answers),
            suggestions={key: dict(value) for key, value in suggestions.items()},
            started=started,
            shadow_enabled=shadow_enabled,
        )
        aei_passive_capture_registry.record(capture)
        platform_metrics.record_job_event(
            task=AEI_PASSIVE_METRIC_TASK,
            status="completed",
            duration_ms=capture.duration_ms,
        )
        if shadow_enabled and capture.shadow_comparison is not None:
            platform_metrics.record_job_event(
                task=AEI_SHADOW_METRIC_TASK,
                status="completed",
                duration_ms=capture.duration_ms,
            )
            if capture.shadow_comparison.difference_count:
                platform_metrics.record_job_event(
                    task=AEI_SHADOW_METRIC_TASK,
                    status="difference",
                )
        logger.info(
            "aei_passive_integration_completed",
            evaluation_id=str(evaluation_id),
            school_id=str(school_id),
            exam_id=str(exam.id),
            student_id=str(student_id),
            question_count=capture.question_count,
            duration_ms=round(capture.duration_ms, 2),
            shadow_enabled=shadow_enabled,
            shadow_difference_count=(
                capture.shadow_comparison.difference_count
                if capture.shadow_comparison is not None
                else None
            ),
        )
        return capture
    except Exception:
        duration_ms = (time.perf_counter() - started) * 1000
        platform_metrics.record_job_event(
            task=AEI_PASSIVE_METRIC_TASK,
            status="failed",
            duration_ms=duration_ms,
        )
        if shadow_enabled:
            platform_metrics.record_job_event(
                task=AEI_SHADOW_METRIC_TASK,
                status="failed",
                duration_ms=duration_ms,
            )
        logger.exception(
            "aei_passive_integration_failed",
            evaluation_id=str(evaluation_id),
            school_id=str(school_id),
            exam_id=str(exam.id),
            student_id=str(student_id),
            duration_ms=round(duration_ms, 2),
        )
        return None


async def _build_passive_capture(
    *,
    db: AsyncSession,
    evaluation_id: UUID,
    school_id: UUID,
    exam: Exam,
    student_id: UUID,
    student_answers: dict[str, str],
    suggestions: dict[str, dict],
    started: float,
    shadow_enabled: bool = False,
) -> AEIPassiveEvaluationCapture:
    paper = await _question_paper(db, school_id=school_id, exam=exam)
    rubrics = await fetch_rubrics_for_paper(
        db,
        school_id=school_id,
        paper_id=exam.source_paper_id,
    )
    understanding_engine = AcademicUnderstandingEngine()
    reasoning_engine = AcademicReasoningEngine()
    policy_engine = EvaluationPolicyEngine()

    captures: list[AEIPassiveQuestionCapture] = []
    shadow_comparisons: list[AEIShadowQuestionComparison] = []
    for question in exam.question_schema or []:
        question_no = str(question["no"])
        rubric = rubrics.get(question_no, {})
        suggestion = suggestions.get(question_no, {})
        answer = AcademicAnswer(
            raw_input=str(student_answers.get(question_no, "")).strip(),
            subject=_subject_name(paper),
            question_type=_question_type(question, rubric),
            visual_type=_visual_type(question, rubric),
            metadata={
                "reasoning_context": _reasoning_context(rubric),
                "passive_capture": {
                    "evaluation_id": str(evaluation_id),
                    "question_no": question_no,
                    "suggestion_method": suggestion.get("method"),
                },
            },
        )
        understood = understanding_engine.understand(answer)
        reasoning = reasoning_engine.reason(understood)
        reasoning = _attach_suggestion_confidence(reasoning, suggestion)
        policy_decision = policy_engine.decide(reasoning)
        teacher_review_decision = create_teacher_review_decision(
            policy_decision,
            audit_metadata={
                "review_source": "aei_passive_integration",
                "evaluation_id": str(evaluation_id),
                "question_no": question_no,
            },
        )
        captures.append(
            AEIPassiveQuestionCapture(
                question_no=question_no,
                academic_answer=understood.model_dump(mode="json"),
                academic_reasoning_result=reasoning.model_dump(mode="json"),
                policy_decision=policy_decision.model_dump(mode="json"),
                teacher_review_decision=teacher_review_decision.model_dump(mode="json"),
            )
        )
        if shadow_enabled:
            shadow_comparisons.append(
                _compare_shadow_question(
                    question_no=question_no,
                    suggestion=suggestion,
                    policy_decision=policy_decision.model_dump(mode="json"),
                )
            )

    return AEIPassiveEvaluationCapture(
        evaluation_id=str(evaluation_id),
        school_id=str(school_id),
        exam_id=str(exam.id),
        student_id=str(student_id),
        question_count=len(captures),
        duration_ms=(time.perf_counter() - started) * 1000,
        questions=tuple(captures),
        shadow_comparison=(
            _summarize_shadow_comparisons(shadow_comparisons)
            if shadow_enabled
            else None
        ),
    )


async def _question_paper(
    db: AsyncSession,
    *,
    school_id: UUID,
    exam: Exam,
) -> QuestionPaper | None:
    if not exam.source_paper_id:
        return None
    return (
        await db.execute(
            select(QuestionPaper).where(
                QuestionPaper.id == exam.source_paper_id,
                QuestionPaper.school_id == school_id,
            )
        )
    ).scalar_one_or_none()


def _attach_suggestion_confidence(
    reasoning: AcademicReasoningResult,
    suggestion: dict[str, Any],
) -> AcademicReasoningResult:
    confidence = suggestion.get("confidence")
    if not isinstance(confidence, (int, float)) or isinstance(confidence, bool):
        return reasoning
    data = reasoning.model_dump()
    metadata = dict(data.get("metadata") or {})
    metadata["confidence"] = float(confidence)
    data["metadata"] = metadata
    return AcademicReasoningResult.model_validate(data)


def _subject_name(paper: QuestionPaper | None) -> str | None:
    if paper and paper.subject_name:
        return str(paper.subject_name)
    return None


def _question_type(question: dict[str, Any], rubric: dict[str, Any]) -> str:
    return str(rubric.get("question_type") or question.get("type") or "short")


def _visual_type(question: dict[str, Any], rubric: dict[str, Any]) -> str | None:
    raw_type = str(rubric.get("question_type") or question.get("type") or "").lower()
    if raw_type in {"diagram", "diagrams"}:
        return "diagrams"
    if raw_type in {"graph", "graphs"}:
        return "graphs"
    if raw_type in {"map", "maps"}:
        return "maps"
    return None


def _reasoning_context(rubric: dict[str, Any]) -> dict[str, Any]:
    context: dict[str, Any] = {}
    for key in (
        "answer_key",
        "acceptable_answers",
        "units",
        "checklist",
        "visual_observations",
    ):
        if key in rubric:
            context[key] = rubric[key]
    return context


def _compare_shadow_question(
    *,
    question_no: str,
    suggestion: dict[str, Any],
    policy_decision: dict[str, Any],
) -> AEIShadowQuestionComparison:
    production_method = str(suggestion.get("method") or "unknown")
    production_confidence = _optional_float(suggestion.get("confidence"))
    production_review_signal = _production_review_signal(
        method=production_method,
        confidence=production_confidence,
    )
    aei_decision = str(policy_decision.get("decision") or "unknown")
    aei_manual_review_required = bool(policy_decision.get("manual_review_required"))
    aei_supported_capability = bool(policy_decision.get("supported_capability"))
    categories = _difference_categories(
        production_method=production_method,
        production_confidence=production_confidence,
        production_review_signal=production_review_signal,
        aei_decision=aei_decision,
        aei_manual_review_required=aei_manual_review_required,
        aei_supported_capability=aei_supported_capability,
    )
    comparison_status = "agreement" if not categories else "difference"
    return AEIShadowQuestionComparison(
        question_no=question_no,
        comparison_status=comparison_status,
        difference_categories=categories,
        production_method=production_method,
        production_confidence=production_confidence,
        production_review_signal=production_review_signal,
        production_marks_suggested=_optional_float(suggestion.get("marks_suggested")),
        production_max_marks=_optional_float(suggestion.get("max_marks")),
        aei_decision=aei_decision,
        aei_manual_review_required=aei_manual_review_required,
        aei_supported_capability=aei_supported_capability,
        metadata={
            "policy_reason": policy_decision.get("reason"),
            "policy_capability_mode": policy_decision.get("capability_mode"),
        },
    )


def _summarize_shadow_comparisons(
    comparisons: list[AEIShadowQuestionComparison],
) -> AEIShadowEvaluationComparison:
    agreement_count = sum(
        1 for comparison in comparisons if comparison.comparison_status == "agreement"
    )
    difference_count = len(comparisons) - agreement_count
    unsupported_capability_count = sum(
        1 for comparison in comparisons if not comparison.aei_supported_capability
    )
    manual_review_delta_count = sum(
        1
        for comparison in comparisons
        if "manual_review_signal_delta" in comparison.difference_categories
    )
    return AEIShadowEvaluationComparison(
        question_count=len(comparisons),
        agreement_count=agreement_count,
        difference_count=difference_count,
        unsupported_capability_count=unsupported_capability_count,
        manual_review_delta_count=manual_review_delta_count,
        comparisons=tuple(comparisons),
    )


def _difference_categories(
    *,
    production_method: str,
    production_confidence: float | None,
    production_review_signal: bool,
    aei_decision: str,
    aei_manual_review_required: bool,
    aei_supported_capability: bool,
) -> tuple[str, ...]:
    categories: list[str] = []
    if not aei_supported_capability or aei_decision == "unsupported":
        categories.append("capability_unsupported")
    if production_review_signal != aei_manual_review_required:
        categories.append("manual_review_signal_delta")
        if production_method == "heuristic_fallback":
            categories.append("production_heuristic_fallback")
        if (
            production_confidence is not None
            and production_confidence < SHADOW_CONFIDENCE_THRESHOLD
        ):
            categories.append("production_low_confidence")
    return tuple(categories)


def _production_review_signal(*, method: str, confidence: float | None) -> bool:
    if method == "heuristic_fallback":
        return True
    return confidence is not None and confidence < SHADOW_CONFIDENCE_THRESHOLD


def _optional_float(value: Any) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return None
