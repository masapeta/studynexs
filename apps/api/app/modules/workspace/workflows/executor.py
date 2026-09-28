"""Deterministic workflow executor — the single controlled workflow-resolution path.

Phase 4 wires Question Paper in as the FIRST workflow consumer. This module is the ONLY place
that maps a planner-chosen `workflow_id` to its execution. It reuses the existing governed QP
machinery end to end — resolvers, staff-scope authorization, the monthly AI credit cap, the QP
generation service, and the approved CurriculumPack lookup — and returns a UI-independent
structured result. It rewrites none of that logic.

Boundary discipline:
* Authorization is the EXISTING `get_staff_scope` + `assert_qp_generate`; JEV/Gemma selecting the
  workflow grants nothing.
* Generation is the EXISTING `question_paper_service.generate_paper`; grounding/blueprint/
  validation/answer-key are untouched.
* The QP DOMAIN lifecycle (`PaperStatus`) stays authoritative; we only report the orchestration
  `WorkflowState` alongside it (wraps, does not own).
* Approval is NOT performed here — the paper is returned as a DRAFT awaiting the existing
  server-side approval endpoints (human-in-the-loop).
"""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser
from app.modules.workspace.workflows.lifecycle import WorkflowState
from app.modules.workspace.workflows.registry import get_workflow

logger = structlog.get_logger()


class WorkflowError(Exception):
    """A recoverable workflow failure carrying a safe, user-facing message."""

    def __init__(self, message: str, *, state: WorkflowState = WorkflowState.FAILED) -> None:
        super().__init__(message)
        self.message = message
        self.state = state


async def run_workflow(
    db: AsyncSession,
    current_user: CurrentUser,
    *,
    workflow_id: str | None,
    params: dict[str, Any] | None,
) -> dict[str, Any]:
    """Resolve and execute a workflow by id. Returns a UI-independent structured block.

    The ONE dispatch point for workflows. Unknown/unregistered ids degrade to a guide block so a
    misroute never crashes the turn.
    """
    definition = get_workflow(workflow_id)
    if definition is None:
        logger.info("workflow_unknown", workflow_id=workflow_id)
        return {
            "kind": "guide",
            "title": "Not available",
            "message": "That workflow isn't available yet.",
        }

    if definition.workflow_id == "question_paper":
        return await _run_question_paper(db, current_user, params or {})
    if definition.workflow_id == "evaluate_answer_sheet":
        return await _run_evaluation(db, current_user, params or {})
    if definition.workflow_id == "lesson_plan":
        return await _run_lesson_plan(db, current_user, params or {})

    # Registered but no executor yet (Phase 7 lands the others).
    return {
        "kind": "guide",
        "title": definition.name,
        "message": f"The {definition.name} workflow isn't wired up yet.",
    }


async def _run_question_paper(
    db: AsyncSession, current_user: CurrentUser, params: dict[str, Any]
) -> dict[str, Any]:
    """Execute the Question Paper workflow over the EXISTING QP pipeline.

    CREATED -> RUNNING -> (generation) -> WAITING_FOR_APPROVAL, returning a DRAFT paper for the
    existing approval flow. Missing class/subject -> a clarify block (WAITING_FOR_INPUT), never a
    crash.
    """
    from app.core.staff_permissions import assert_qp_generate, get_staff_scope
    from app.modules.ai.services.question_paper_service import generate_paper
    from app.modules.ai.services.usage_caps import enforce_monthly_ai_cap
    from app.modules.workspace.assistant.resolver import resolve_class, resolve_subject

    school_id = uuid.UUID(current_user.school_id)

    class_label = (params.get("class_label") or params.get("class") or "").strip()
    subject_name = (params.get("subject") or "").strip()
    if not class_label or not subject_name:
        missing = "class" if not class_label else "subject"
        return {
            "kind": "clarify",
            "title": "Which class and subject?",
            "message": (
                f"Tell me the {missing} for the question paper — e.g. "
                "'a Science paper for Class 8'."
            ),
        }

    # Resolve class -> class_id (deterministic; reuses the assistant resolver).
    class_res = await resolve_class(db, school_id, class_label)
    if len(class_res.candidates) != 1:
        return _clarify_entity("class", class_label, class_res.candidates)
    class_id = class_res.candidates[0].id

    # Resolve subject within that class -> subject_id.
    subject_res = await resolve_subject(db, school_id, subject_name, class_id=class_id)
    if len(subject_res.candidates) != 1:
        return _clarify_entity("subject", subject_name, subject_res.candidates)
    subject_id = subject_res.candidates[0].id

    # Authorization — the EXISTING staff-scope gate. Workflow selection grants nothing.
    scope = await get_staff_scope(db, current_user)
    assert_qp_generate(scope, class_id, subject_id)

    # Approved CurriculumPack for grounding (chat can't pass a pack_id; find the newest APPROVED).
    pack_id = await _approved_pack_id(db, school_id, class_id, subject_id)
    if pack_id is None:
        return {
            "kind": "guide",
            "title": "Curriculum pack needed",
            "message": (
                f"No approved curriculum pack exists for {class_res.candidates[0].label} "
                f"{subject_res.candidates[0].label}. Approve a pack first, then I can generate "
                "a grounded paper."
            ),
        }

    total_marks = _coerce_marks(params.get("total_marks"))
    topics = [str(t) for t in (params.get("topics") or []) if str(t).strip()]

    # Credit cap — the EXISTING monthly enforcement (row-locked ledger).
    credits = await enforce_monthly_ai_cap(
        db,
        school_id,
        user_id=uuid.UUID(current_user.id),
        role=current_user.role,
        feature="question_paper",
        purpose_tag="qp_full",
    )

    try:
        paper = await generate_paper(
            db,
            school_id=school_id,
            created_by=uuid.UUID(current_user.id),
            class_id=class_id,
            subject_id=subject_id,
            topics=topics,
            total_marks=total_marks,
            duration_minutes=180,
            difficulty="balanced",
            role=current_user.role,
            purpose_tag="qp_full",
            credits_charged=credits,
            pack_id=pack_id,
        )
    except ValueError as exc:
        raise WorkflowError(str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 — surface a safe message; details are logged upstream
        logger.warning("workflow_qp_generate_failed", error=str(exc))
        raise WorkflowError("Question paper generation failed. Please try again.") from exc

    return _qp_result_block(
        paper,
        class_label=class_res.candidates[0].label,
        subject_label=subject_res.candidates[0].label,
    )


async def _approved_pack_id(
    db: AsyncSession, school_id: uuid.UUID, class_id: uuid.UUID, subject_id: uuid.UUID
) -> uuid.UUID | None:
    from app.db.models.curriculum_pack import PackStatus
    from app.modules.curriculum.services.pack_service import PackService

    packs = await PackService(db).list_packs(
        school_id, class_id=class_id, subject_id=subject_id
    )
    for pack in packs:  # newest-first
        if pack.status == PackStatus.APPROVED:
            return pack.id
    return None


async def _run_evaluation(
    db: AsyncSession, current_user: CurrentUser, params: dict[str, Any]
) -> dict[str, Any]:
    """Execute the Answer Sheet Evaluation workflow over the EXISTING async pipeline.

    Wraps `AnswerSheetEvalService.create_and_evaluate` (unchanged): it authorizes, checks AI
    credits, and enqueues an Arq job (runs sync only under TESTING). The generic WorkflowState is
    DERIVED from the authoritative domain status — QUEUED/RUNNING while the job runs,
    WAITING_FOR_APPROVAL once AI marks are suggested (teacher HITL), COMPLETED on approval, FAILED
    on error. We do NOT report COMPLETED merely because the job was submitted.

    Needs an exam + a student + an answer source (a file already uploaded, or transcribed answers).
    A chat turn typically supplies exam + student references; the answer sheet itself is uploaded
    through the existing UI, so when no answer source is present we return an honest next-step
    rather than fabricating one.
    """
    from app.core.staff_permissions import (
        assert_exam_eval_access,
        assert_exams_access,
        get_staff_scope,
    )
    from app.core.tenant_scope import TenantScope
    from app.modules.examinations.services.answer_sheet_eval_service import (
        AnswerSheetEvalService,
        EvalError,
    )
    from app.modules.workspace.assistant.resolver import resolve_student

    school_id = uuid.UUID(current_user.school_id)

    exam_id = _coerce_uuid(params.get("exam_id"))
    if exam_id is None:
        return {
            "kind": "clarify",
            "title": "Which exam?",
            "message": (
                "Tell me which exam to evaluate — open the exam and start the evaluation, or "
                "name the exam so I can look it up."
            ),
        }

    # Authorization — the EXISTING exam/eval gates. Workflow selection grants nothing.
    scope = await get_staff_scope(db, current_user)
    assert_exams_access(scope)
    try:
        exam = await TenantScope(db, school_id).exam(exam_id)
    except Exception:  # noqa: BLE001 — a missing/foreign exam is a clarify, not a crash
        return {
            "kind": "clarify",
            "title": "Exam not found",
            "message": "I couldn't find that exam for your school. Please check and try again.",
        }
    assert_exam_eval_access(scope, exam)

    student_token = (params.get("student") or "").strip()
    if not student_token:
        return {
            "kind": "clarify",
            "title": "Which student?",
            "message": "Which student's answer sheet should I evaluate?",
        }
    student_res = await resolve_student(db, school_id, student_token)
    if len(student_res.candidates) != 1:
        return _clarify_entity("student", student_token, student_res.candidates)
    student_id = student_res.candidates[0].id

    file_id = _coerce_uuid(params.get("file_id"))
    raw_answers = params.get("student_answers")
    student_answers = raw_answers if isinstance(raw_answers, dict) else None
    if not file_id and not student_answers:
        return {
            "kind": "guide",
            "title": "Upload the answer sheet",
            "message": (
                f"To evaluate {student_res.candidates[0].label} for {exam.title}, upload the "
                "answer sheet on the exam's evaluation screen — then I can start the evaluation."
            ),
            "suggestions": [
                {"label": "Open exam evaluation", "href": f"/dashboard/teaching/exams/{exam.id}"},
            ],
        }

    from app.db.models.school import School

    school = await db.get(School, school_id)

    service = AnswerSheetEvalService(db)
    try:
        row = await service.create_and_evaluate(
            school_id=school_id,
            exam_id=exam.id,
            student_id=student_id,
            created_by=uuid.UUID(current_user.id),
            role=current_user.role,
            school=school,
            file_id=file_id,
            student_answers=student_answers,
        )
    except EvalError as exc:
        raise WorkflowError(str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 — safe message; details logged upstream
        logger.warning("workflow_eval_failed", error=str(exc))
        raise WorkflowError("Answer sheet evaluation failed. Please try again.") from exc

    return _eval_result_block(
        row, exam_title=exam.title, student_label=student_res.candidates[0].label
    )


async def _run_lesson_plan(
    db: AsyncSession, current_user: CurrentUser, params: dict[str, Any]
) -> dict[str, Any]:
    """Execute the Lesson Plan workflow over the EXISTING lesson-plan pipeline (sync + approval).

    Wraps `LessonPlanService.generate` unchanged: it authorizes via the existing staff-scope gate
    and produces a DRAFT lesson plan (grounded in an approved pack when one exists, else a
    template). CREATED -> RUNNING -> WAITING_FOR_APPROVAL; the LessonPlan domain lifecycle
    (DRAFT -> APPROVED) stays authoritative.
    """
    from app.core.staff_permissions import assert_qp_generate, get_staff_scope
    from app.modules.curriculum.services.lesson_plan_service import LessonPlanService
    from app.modules.workspace.assistant.resolver import resolve_class, resolve_subject

    school_id = uuid.UUID(current_user.school_id)

    class_label = (params.get("class_label") or params.get("class") or "").strip()
    subject_name = (params.get("subject") or "").strip()
    if not class_label or not subject_name:
        missing = "class" if not class_label else "subject"
        return {
            "kind": "clarify",
            "title": "Which class and subject?",
            "message": (
                f"Tell me the {missing} for the lesson plan — e.g. "
                "'a lesson plan for Class 8 Science'."
            ),
        }

    class_res = await resolve_class(db, school_id, class_label)
    if len(class_res.candidates) != 1:
        return _clarify_entity("class", class_label, class_res.candidates)
    class_id = class_res.candidates[0].id

    subject_res = await resolve_subject(db, school_id, subject_name, class_id=class_id)
    if len(subject_res.candidates) != 1:
        return _clarify_entity("subject", subject_name, subject_res.candidates)
    subject_id = subject_res.candidates[0].id

    # Authorization — the EXISTING staff-scope gate (same one QP uses), enforced BEFORE generation
    # so a 403 propagates as-is and is never masked by the broad failure handler below.
    scope = await get_staff_scope(db, current_user)
    assert_qp_generate(scope, class_id, subject_id)

    topic = (params.get("topic") or "").strip() or None
    chapter = (params.get("chapter") or "").strip() or None
    # Ground on an approved pack when available; the service also works ungrounded (template).
    pack_id = await _approved_pack_id(db, school_id, class_id, subject_id)

    service = LessonPlanService(db)
    try:
        plan = await service.generate(
            school_id,
            scope,
            class_id=class_id,
            subject_id=subject_id,
            topic=topic,
            chapter=chapter,
            pack_id=pack_id,
        )
    except ValueError as exc:
        raise WorkflowError(str(exc)) from exc
    except HTTPException:
        raise  # authorization / governance errors must propagate unchanged
    except Exception as exc:  # noqa: BLE001 — safe message; details logged upstream
        logger.warning("workflow_lesson_plan_failed", error=str(exc))
        raise WorkflowError("Lesson plan generation failed. Please try again.") from exc

    return _lesson_plan_result_block(
        plan,
        class_label=class_res.candidates[0].label,
        subject_label=subject_res.candidates[0].label,
    )


def _coerce_marks(value: Any) -> int:
    try:
        marks = int(value)
    except (TypeError, ValueError):
        return 80
    return marks if 1 <= marks <= 200 else 80


def _coerce_uuid(value: Any) -> uuid.UUID | None:
    if isinstance(value, uuid.UUID):
        return value
    if isinstance(value, str) and value.strip():
        try:
            return uuid.UUID(value.strip())
        except ValueError:
            return None
    return None


def _clarify_entity(kind: str, query: str, candidates: list[Any]) -> dict[str, Any]:
    if not candidates:
        msg = f"I couldn't find a {kind} matching '{query}'."
    else:
        names = ", ".join(c.label for c in candidates[:5])
        msg = f"Which {kind} did you mean? {names}"
    return {"kind": "clarify", "title": f"Which {kind}?", "message": msg}


def _qp_result_block(paper: Any, *, class_label: str, subject_label: str) -> dict[str, Any]:
    """UI-independent workflow result for a generated draft awaiting approval."""
    question_count = sum(len(getattr(s, "questions", []) or []) for s in (paper.sections or []))
    return {
        "kind": "workflow",
        "workflow_id": "question_paper",
        "title": f"Question Paper — {class_label} {subject_label}",
        "workflow_state": WorkflowState.WAITING_FOR_APPROVAL.value,
        "paper_status": paper.status.value if hasattr(paper.status, "value") else str(paper.status),
        "summary": {
            "paper_id": str(paper.id),
            "class": class_label,
            "subject": subject_label,
            "total_marks": float(paper.total_marks),
            "question_count": question_count,
            "grounded": bool(getattr(paper, "grounded", False)),
        },
        # Available actions invoke the EXISTING authorized server-side endpoints (HITL).
        "actions": [
            {"label": "Review", "href": f"/dashboard/question-papers/{paper.id}"},
            {
                "label": "Submit for approval",
                "endpoint": f"/api/v1/ai/question-papers/{paper.id}/submit",
            },
            {"label": "Approve", "endpoint": f"/api/v1/ai/question-papers/{paper.id}/approve"},
        ],
        "message": (
            f"Drafted a {float(paper.total_marks):.0f}-mark {subject_label} paper for "
            f"{class_label} ({question_count} questions). Review and approve it to finalise."
        ),
    }


# Map the authoritative domain eval status -> the generic orchestration state. The domain status
# stays the source of truth (wraps, does not own); this derivation is display/telemetry only.
_EVAL_STATUS_TO_WORKFLOW = {
    "pending": WorkflowState.QUEUED,
    "processing": WorkflowState.RUNNING,
    "suggested": WorkflowState.WAITING_FOR_APPROVAL,  # AI done, awaiting teacher HITL
    "approved": WorkflowState.COMPLETED,
    "failed": WorkflowState.FAILED,
}


def _eval_result_block(row: Any, *, exam_title: str, student_label: str) -> dict[str, Any]:
    """UI-independent workflow result for an (async) answer-sheet evaluation."""
    status = row.status.value if hasattr(row.status, "value") else str(row.status)
    wf_state = _EVAL_STATUS_TO_WORKFLOW.get(status, WorkflowState.RUNNING).value
    running = wf_state in (WorkflowState.QUEUED.value, WorkflowState.RUNNING.value)
    if wf_state == WorkflowState.FAILED.value:
        message = f"Evaluation failed for {student_label}. {row.error_message or ''}".strip()
    elif running:
        message = (
            f"Evaluating {student_label}'s answer sheet for {exam_title}. I'll have suggested "
            "marks shortly — check the evaluation screen to review and approve."
        )
    else:
        message = (
            f"AI marks are ready for {student_label} ({exam_title}). Review and approve them to "
            "finalise."
        )
    return {
        "kind": "workflow",
        "workflow_id": "evaluate_answer_sheet",
        "title": f"Answer Sheet Evaluation — {student_label}",
        "workflow_state": wf_state,
        "eval_status": status,  # authoritative domain status
        "summary": {
            "evaluation_id": str(row.id),
            "exam": exam_title,
            "student": student_label,
            "job_id": str(row.job_id) if row.job_id else None,
        },
        "actions": [
            {"label": "Review evaluation", "href": f"/dashboard/teaching/exams/{row.exam_id}"},
            {
                "label": "Approve marks",
                "endpoint": f"/api/v1/exams/evaluations/{row.id}/approve",
            },
        ],
        "message": message,
    }


def _lesson_plan_result_block(
    plan: Any, *, class_label: str, subject_label: str
) -> dict[str, Any]:
    """UI-independent workflow result for a generated lesson-plan draft awaiting approval."""
    return {
        "kind": "workflow",
        "workflow_id": "lesson_plan",
        "title": f"Lesson Plan — {class_label} {subject_label}",
        "workflow_state": WorkflowState.WAITING_FOR_APPROVAL.value,
        "plan_status": plan.status.value if hasattr(plan.status, "value") else str(plan.status),
        "summary": {
            "lesson_plan_id": str(plan.id),
            "class": class_label,
            "subject": subject_label,
            "topic": plan.topic,
            "chapter": plan.chapter,
            "segments": len(plan.segments or []),
            "grounded": bool(getattr(plan, "grounded", False)),
        },
        # Actions invoke the EXISTING authorized server-side endpoints (HITL).
        "actions": [
            {"label": "Review", "href": f"/dashboard/lesson-plans/{plan.id}"},
            {"label": "Approve", "endpoint": f"/api/v1/lesson-plans/{plan.id}/approve"},
        ],
        "message": (
            f"Drafted a lesson plan for {class_label} {subject_label}"
            f"{f' on {plan.topic}' if plan.topic else ''}. Review and approve it to finalise."
        ),
    }
