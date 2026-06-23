"""Answer sheet evaluation — vision OCR, async jobs, HITL approve, misconception extract."""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Environment, get_settings
from app.core.tenant_scope import TenantScope
from app.db.models.answer_sheet_evaluation import (
    EVAL_STATUS_APPROVED,
    EVAL_STATUS_FAILED,
    EVAL_STATUS_PROCESSING,
    EVAL_STATUS_SUGGESTED,
    AnswerSheetEvaluation,
)
from app.db.models.examination import Exam, ExamMark
from app.db.models.school import School
from app.modules.ai.services.ai_credits import (
    assert_credits_for_charge,
    check_ai_credits,
    credits_for_purpose,
)
from app.modules.ai.services.question_bank_service import fetch_rubrics_for_paper
from app.modules.examinations.schemas.evaluation import EvaluationApprove
from app.modules.examinations.schemas.exam import MarkEntry
from app.modules.examinations.services.answer_sheet_vision import (
    extract_answers_from_image,
    is_image_mime,
)
from app.modules.examinations.services.exam_service import ExamService
from app.modules.examinations.services.misconception_service import extract_from_evaluation
from app.modules.files.services.file_service import FileService

logger = structlog.get_logger()
settings = get_settings()

_WHITESPACE = re.compile(r"\s+")
_OBJECTIVE_TYPES = frozenset({"mcq", "fill_blank", "true_false", "fill_in_blank"})


class EvalError(ValueError):
    """Evaluation cannot proceed."""


def _normalize(text: str) -> str:
    return _WHITESPACE.sub(" ", text.strip().lower())


def _mcq_letter(answer: str, options: list | None) -> str | None:
    raw = answer.strip()
    if len(raw) == 1 and raw.upper() in "ABCDEFGH":
        return raw.upper()
    if not options:
        return raw.upper() if raw else None
    norm = _normalize(raw)
    for idx, opt in enumerate(options):
        if _normalize(str(opt)) == norm:
            return chr(ord("A") + idx)
    return raw.upper() if raw else None


def grade_objective(
    *,
    q_type: str,
    student_answer: str,
    answer_key: str,
    max_marks: float,
    options: list | None = None,
) -> tuple[float, str, float]:
    if not student_answer.strip():
        return 0.0, "No answer provided.", 0.9

    q = q_type.lower()
    key = answer_key.strip()
    if q == "mcq":
        student_letter = _mcq_letter(student_answer, options)
        key_letter = _mcq_letter(key, options) or key.upper()
        if student_letter and key_letter and student_letter == key_letter:
            return max_marks, "Correct option selected.", 0.98
        return 0.0, f"Selected {student_letter or student_answer}; expected {key_letter or key}.", 0.95

    if q in ("true_false", "fill_blank", "fill_in_blank"):
        if _normalize(student_answer) == _normalize(key):
            return max_marks, "Correct answer.", 0.98
        return 0.0, f"Expected '{key}'.", 0.95

    if _normalize(student_answer) == _normalize(key):
        return max_marks, "Matches model answer.", 0.95
    return 0.0, "Does not match model answer.", 0.85


def grade_subjective_heuristic(
    *,
    student_answer: str,
    answer_key: str,
    max_marks: float,
) -> tuple[float, str, float]:
    if not student_answer.strip():
        return 0.0, "No answer provided.", 0.9
    if not answer_key.strip():
        return 0.0, "No model answer on file — teacher must mark manually.", 0.3

    key_tokens = {t for t in re.findall(r"[a-z0-9]+", _normalize(answer_key)) if len(t) > 2}
    ans_tokens = {t for t in re.findall(r"[a-z0-9]+", _normalize(student_answer)) if len(t) > 2}
    if not key_tokens:
        return 0.0, "Review manually.", 0.4

    overlap = len(key_tokens & ans_tokens) / len(key_tokens)
    if overlap >= 0.7:
        return max_marks, "Strong match to model answer.", 0.75
    if overlap >= 0.4:
        return round(max_marks * 0.5, 2), "Partial match — review suggested.", 0.55
    return 0.0, "Weak match to model answer.", 0.6


def _build_summary(suggestions: dict[str, dict]) -> str:
    weak = [
        f"Q{qno}: {s.get('feedback', '')}"
        for qno, s in sorted(suggestions.items(), key=lambda x: int(x[0]) if x[0].isdigit() else x[0])
        if float(s.get("marks_suggested", 0)) < float(s.get("max_marks", 0))
    ]
    if not weak:
        return "All questions appear fully correct per rubric."
    return "Areas to review:\n" + "\n".join(weak[:8])


class AnswerSheetEvalService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_and_evaluate(
        self,
        *,
        school_id: uuid.UUID,
        exam_id: uuid.UUID,
        student_id: uuid.UUID,
        created_by: uuid.UUID,
        role: str,
        school: School,
        file_id: uuid.UUID | None = None,
        student_answers: dict[str, str] | None = None,
    ) -> AnswerSheetEvaluation:
        scope = TenantScope(self.db, school_id)
        exam = await scope.exam(exam_id)
        if not exam.source_paper_id:
            raise EvalError("Exam is not linked to an approved AI question paper")
        if not exam.question_schema:
            raise EvalError("Exam has no question schema")
        if not file_id and not (student_answers or {}):
            raise EvalError("Upload an answer sheet image or provide student answers")

        await scope.students_in_class(exam.class_id, [student_id])
        await check_ai_credits(
            self.db, school, user_id=created_by, role=role, purpose_tag="exam_evaluation"
        )

        existing = (
            await self.db.execute(
                select(AnswerSheetEvaluation)
                .where(
                    AnswerSheetEvaluation.exam_id == exam_id,
                    AnswerSheetEvaluation.student_id == student_id,
                    AnswerSheetEvaluation.school_id == school_id,
                )
                .with_for_update()
            )
        ).scalar_one_or_none()
        if existing and existing.status == EVAL_STATUS_APPROVED:
            raise EvalError("Marks already approved for this student — edit marks directly")
        if existing and existing.status == EVAL_STATUS_PROCESSING:
            raise EvalError("Evaluation already in progress for this student")

        if existing:
            row = existing
            row.file_id = file_id
            row.input_answers = dict(student_answers or {})
            row.status = EVAL_STATUS_PROCESSING
            row.ai_suggestions = None
            row.correction_summary = None
            row.teacher_overrides = None
            row.error_message = None
            row.job_id = None
            row.created_by = created_by
        else:
            row = AnswerSheetEvaluation(
                school_id=school_id,
                exam_id=exam_id,
                student_id=student_id,
                file_id=file_id,
                input_answers=dict(student_answers or {}),
                created_by=created_by,
                status=EVAL_STATUS_PROCESSING,
            )
            self.db.add(row)
        await self.db.flush()

        if settings.ENVIRONMENT == Environment.TESTING:
            return await self.execute_evaluation(row.id, role=role)

        try:
            from app.core.jobs.queue import enqueue

            job = await enqueue(
                self.db,
                task="answer_sheet_eval",
                params={"evaluation_id": str(row.id), "role": role},
                school_id=school_id,
                created_by=created_by,
            )
            row.job_id = job.id
            await self.db.flush()
            return row
        except Exception:
            logger.warning("eval_enqueue_failed_running_sync", evaluation_id=str(row.id))
            return await self.execute_evaluation(row.id, role=role)

    async def execute_evaluation(
        self, evaluation_id: uuid.UUID, *, role: str = "teacher"
    ) -> AnswerSheetEvaluation:
        result = await self.db.execute(
            select(AnswerSheetEvaluation).where(AnswerSheetEvaluation.id == evaluation_id)
        )
        row = result.scalar_one_or_none()
        if not row:
            raise EvalError("Evaluation not found")

        scope = TenantScope(self.db, row.school_id)
        exam = await scope.exam(row.exam_id)
        row.status = EVAL_STATUS_PROCESSING
        await self.db.flush()

        vision_result = None
        try:
            answers, vision_result = await self._resolve_student_answers(row, exam)
            suggestions = await self._grade_exam(
                exam=exam,
                school_id=row.school_id,
                student_answers=answers,
            )
            row.ai_suggestions = suggestions
            row.correction_summary = _build_summary(suggestions)
            row.status = EVAL_STATUS_SUGGESTED
            await self._record_eval_credits(
                school_id=row.school_id,
                created_by=row.created_by,
                role=role,
                evaluation_id=row.id,
                vision_result=vision_result,
            )
        except Exception as exc:
            logger.exception("eval_failed", evaluation_id=str(evaluation_id))
            row.status = EVAL_STATUS_FAILED
            row.error_message = "Evaluation failed. Try again or enter marks manually."
            await self.db.flush()
            raise EvalError(row.error_message) from exc

        await self.db.flush()
        return row

    async def _resolve_student_answers(
        self,
        row: AnswerSheetEvaluation,
        exam: Exam,
    ) -> tuple[dict[str, str], object | None]:
        merged = dict(row.input_answers or {})
        vision_result = None

        if row.file_id:
            file_svc = FileService(self.db)
            record = await file_svc.get_file(row.file_id, row.school_id)
            if not record:
                raise EvalError("Answer sheet file not found")
            if is_image_mime(record.content_type):
                image_bytes = Path(record.storage_path).read_bytes()
                rubrics = await fetch_rubrics_for_paper(
                    self.db, school_id=row.school_id, paper_id=exam.source_paper_id
                )
                extracted, vision_result = await extract_answers_from_image(
                    image_bytes=image_bytes,
                    mime_type=record.content_type,
                    question_schema=exam.question_schema or [],
                    rubrics=rubrics,
                )
                for qno, text in extracted.items():
                    if qno not in merged or not str(merged.get(qno, "")).strip():
                        merged[qno] = text

        return merged, vision_result

    async def _record_eval_credits(
        self,
        *,
        school_id: uuid.UUID,
        created_by: uuid.UUID,
        role: str,
        evaluation_id: uuid.UUID,
        vision_result: object | None = None,
    ) -> None:
        from app.db.models.ai_usage import AIUsage
        from app.modules.ai.gateway.base import LLMResult
        from app.modules.ai.gateway.metering import record_usage

        existing = (
            await self.db.execute(
                select(AIUsage.id).where(
                    AIUsage.school_id == school_id,
                    AIUsage.ref_type == "answer_sheet_evaluation",
                    AIUsage.ref_id == evaluation_id,
                    AIUsage.credits_charged > 0,
                ).limit(1)
            )
        ).scalar_one_or_none()
        if existing:
            return

        credits = credits_for_purpose("exam_evaluation")
        if isinstance(vision_result, LLMResult):
            await record_usage(
                self.db,
                feature="answer_sheet_eval",
                result=vision_result,
                school_id=school_id,
                created_by=created_by,
                role=role,
                purpose_tag="exam_evaluation",
                credits_charged=credits,
                ref_type="answer_sheet_evaluation",
                ref_id=evaluation_id,
                image_count=1,
            )
            return

        await assert_credits_for_charge(
            self.db,
            school_id,
            user_id=created_by,
            role=role,
            purpose_tag="exam_evaluation",
            credits=credits,
        )
        self.db.add(
            AIUsage(
                school_id=school_id,
                created_by=created_by,
                feature="answer_sheet_eval",
                provider="internal",
                model="heuristic-v1",
                tokens_in=0,
                tokens_out=0,
                cost_usd=0,
                latency_ms=0,
                role=role,
                purpose_tag="exam_evaluation",
                credits_charged=credits,
                ref_type="answer_sheet_evaluation",
                ref_id=evaluation_id,
            )
        )

    async def _grade_exam(
        self,
        *,
        exam: Exam,
        school_id: uuid.UUID,
        student_answers: dict[str, str],
    ) -> dict[str, dict]:
        rubrics = await fetch_rubrics_for_paper(
            self.db, school_id=school_id, paper_id=exam.source_paper_id
        )
        suggestions: dict[str, dict] = {}
        for q in exam.question_schema or []:
            qno = str(q["no"])
            max_marks = float(q["max_marks"])
            rubric = rubrics.get(qno, {})
            q_type = str(rubric.get("question_type") or "short")
            answer_key = str(rubric.get("answer_key") or "")
            student_answer = str(student_answers.get(qno, "")).strip()
            options = rubric.get("options")
            topic = q.get("topic") or exam.topic

            if q_type.lower() in _OBJECTIVE_TYPES or (
                q_type.lower() in ("short", "very_short") and answer_key and len(answer_key) < 40
            ):
                marks, feedback, confidence = grade_objective(
                    q_type=q_type,
                    student_answer=student_answer,
                    answer_key=answer_key,
                    max_marks=max_marks,
                    options=options,
                )
            else:
                marks, feedback, confidence = grade_subjective_heuristic(
                    student_answer=student_answer,
                    answer_key=answer_key,
                    max_marks=max_marks,
                )

            misconception_hint = None
            if marks < max_marks and rubric.get("common_wrong_answers"):
                misconception_hint = str(rubric["common_wrong_answers"][0])

            suggestions[qno] = {
                "marks_suggested": marks,
                "max_marks": max_marks,
                "feedback": feedback,
                "confidence": confidence,
                "student_answer": student_answer,
                "topic": topic,
                "misconception_hint": misconception_hint,
                "ocr_source": bool(student_answer),
            }
        return suggestions

    async def list_for_exam(
        self, school_id: uuid.UUID, exam_id: uuid.UUID
    ) -> list[AnswerSheetEvaluation]:
        await TenantScope(self.db, school_id).exam(exam_id)
        result = await self.db.execute(
            select(AnswerSheetEvaluation)
            .where(
                AnswerSheetEvaluation.school_id == school_id,
                AnswerSheetEvaluation.exam_id == exam_id,
            )
            .order_by(AnswerSheetEvaluation.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_evaluation(
        self, school_id: uuid.UUID, evaluation_id: uuid.UUID
    ) -> AnswerSheetEvaluation | None:
        result = await self.db.execute(
            select(AnswerSheetEvaluation).where(
                AnswerSheetEvaluation.id == evaluation_id,
                AnswerSheetEvaluation.school_id == school_id,
            )
        )
        return result.scalar_one_or_none()

    async def approve(
        self,
        *,
        school_id: uuid.UUID,
        evaluation_id: uuid.UUID,
        data: EvaluationApprove,
        approved_by: uuid.UUID,
    ) -> AnswerSheetEvaluation:
        row = await self.get_evaluation(school_id, evaluation_id)
        if not row:
            raise EvalError("Evaluation not found")
        if row.status != EVAL_STATUS_SUGGESTED:
            raise EvalError("Only suggested evaluations can be approved")
        if not row.ai_suggestions:
            raise EvalError("No AI suggestions to approve")

        scope = TenantScope(self.db, school_id)
        exam = await scope.exam(row.exam_id)

        question_marks: dict[str, float] = {}
        for qno, suggestion in row.ai_suggestions.items():
            override = (data.teacher_overrides or {}).get(qno) or {}
            marks = override.get("marks")
            if marks is None:
                marks = suggestion.get("marks_suggested", 0)
            max_m = float(suggestion.get("max_marks", 0))
            marks_f = round(float(marks), 2)
            if marks_f < 0 or marks_f > max_m:
                raise EvalError(f"Marks for Q{qno} outside 0..{max_m}")
            question_marks[qno] = marks_f

        row.teacher_overrides = data.teacher_overrides or None
        row.correction_summary = data.correction_summary or row.correction_summary
        row.status = EVAL_STATUS_APPROVED
        row.approved_by = approved_by
        row.approved_at = datetime.now(timezone.utc)

        exam_service = ExamService(self.db)
        feedback_lines = [
            f"Q{qno}: {(row.ai_suggestions.get(qno) or {}).get('feedback', '')}"
            for qno in sorted(question_marks, key=lambda x: int(x) if x.isdigit() else x)
        ]
        await exam_service.enter_marks(
            school_id,
            row.exam_id,
            [
                MarkEntry(
                    student_id=row.student_id,
                    question_marks=question_marks,
                    remarks=row.correction_summary,
                )
            ],
        )

        mark_row = (
            await self.db.execute(
                select(ExamMark).where(
                    ExamMark.exam_id == row.exam_id,
                    ExamMark.student_id == row.student_id,
                    ExamMark.school_id == school_id,
                )
            )
        ).scalar_one_or_none()
        if mark_row:
            mark_row.ai_graded = True
            mark_row.ai_feedback = row.correction_summary or "\n".join(feedback_lines[:10])

        await extract_from_evaluation(
            self.db, evaluation=row, exam=exam, approved_by=approved_by
        )

        await self.db.flush()
        return row

    async def list_corrections_history(
        self,
        school_id: uuid.UUID,
        *,
        class_id: uuid.UUID | None = None,
        exam_id: uuid.UUID | None = None,
        student_id: uuid.UUID | None = None,
        subject_ids: set[uuid.UUID] | None = None,
        limit: int = 100,
    ) -> list[dict]:
        query = (
            select(AnswerSheetEvaluation, Exam)
            .join(Exam, Exam.id == AnswerSheetEvaluation.exam_id)
            .where(
                AnswerSheetEvaluation.school_id == school_id,
                AnswerSheetEvaluation.status == EVAL_STATUS_APPROVED,
            )
        )
        if class_id:
            query = query.where(Exam.class_id == class_id)
        if subject_ids is not None:
            if not subject_ids:
                return []
            query = query.where(Exam.subject_id.in_(subject_ids))
        if exam_id:
            query = query.where(AnswerSheetEvaluation.exam_id == exam_id)
        if student_id:
            query = query.where(AnswerSheetEvaluation.student_id == student_id)

        rows = (
            await self.db.execute(
                query.order_by(AnswerSheetEvaluation.approved_at.desc()).limit(limit)
            )
        ).all()

        history: list[dict] = []
        for ev, exam in rows:
            suggestions = ev.ai_suggestions or {}
            overrides = ev.teacher_overrides or {}
            for qno, suggestion in suggestions.items():
                override = overrides.get(qno) or {}
                ai_marks = float(suggestion.get("marks_suggested", 0))
                teacher_marks = float(override.get("marks", ai_marks))
                history.append({
                    "evaluation_id": ev.id,
                    "exam_id": exam.id,
                    "exam_title": exam.title,
                    "student_id": ev.student_id,
                    "question_no": qno,
                    "ai_marks": ai_marks,
                    "teacher_marks": teacher_marks,
                    "max_marks": float(suggestion.get("max_marks", 0)),
                    "ai_feedback": str(suggestion.get("feedback", "")),
                    "override_reason": override.get("reason"),
                    "approved_at": ev.approved_at,
                    "topic": suggestion.get("topic"),
                })
        return history
