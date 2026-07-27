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
DEFAULT_CAPTURE_LIMIT = 100


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
) -> AEIPassiveEvaluationCapture | None:
    """Run AEI passively and isolate all AEI failures from production evaluation."""

    if not enabled:
        return None

    started = time.perf_counter()
    platform_metrics.record_job_event(task=AEI_PASSIVE_METRIC_TASK, status="invoked")
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
        )
        aei_passive_capture_registry.record(capture)
        platform_metrics.record_job_event(
            task=AEI_PASSIVE_METRIC_TASK,
            status="completed",
            duration_ms=capture.duration_ms,
        )
        logger.info(
            "aei_passive_integration_completed",
            evaluation_id=str(evaluation_id),
            school_id=str(school_id),
            exam_id=str(exam.id),
            student_id=str(student_id),
            question_count=capture.question_count,
            duration_ms=round(capture.duration_ms, 2),
        )
        return capture
    except Exception:
        duration_ms = (time.perf_counter() - started) * 1000
        platform_metrics.record_job_event(
            task=AEI_PASSIVE_METRIC_TASK,
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

    return AEIPassiveEvaluationCapture(
        evaluation_id=str(evaluation_id),
        school_id=str(school_id),
        exam_id=str(exam.id),
        student_id=str(student_id),
        question_count=len(captures),
        duration_ms=(time.perf_counter() - started) * 1000,
        questions=tuple(captures),
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
