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

    # Registered but no executor yet (Phases 5-7 land the others).
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


def _coerce_marks(value: Any) -> int:
    try:
        marks = int(value)
    except (TypeError, ValueError):
        return 80
    return marks if 1 <= marks <= 200 else 80


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
