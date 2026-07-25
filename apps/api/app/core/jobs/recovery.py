"""Operational recovery helpers for background jobs.

These helpers are intentionally operator-facing: normal product requests should
not silently mutate or replay stale work.  H6 made stale queue state visible; H5
adds a narrow, auditable recovery path for answer-sheet evaluation jobs.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.answer_sheet_evaluation import (
    EVAL_STATUS_APPROVED,
    EVAL_STATUS_FAILED,
    EVAL_STATUS_SUGGESTED,
    AnswerSheetEvaluation,
)
from app.db.models.job import Job, JobStatus

logger = structlog.get_logger()

_TERMINAL_SUCCESS_EVAL_STATUSES = {EVAL_STATUS_SUGGESTED, EVAL_STATUS_APPROVED}
_RECOVERABLE_JOB_STATUSES = {JobStatus.QUEUED, JobStatus.RUNNING}


@dataclass(frozen=True)
class StaleEvaluationJobRecoveryItem:
    job_id: uuid.UUID
    school_id: uuid.UUID | None
    job_status: str
    evaluation_id: uuid.UUID | None
    evaluation_status: str | None
    action: str
    applied: bool
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "job_id": str(self.job_id),
            "school_id": str(self.school_id) if self.school_id else None,
            "job_status": self.job_status,
            "evaluation_id": str(self.evaluation_id) if self.evaluation_id else None,
            "evaluation_status": self.evaluation_status,
            "action": self.action,
            "applied": self.applied,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class StaleEvaluationJobRecoveryResult:
    dry_run: bool
    older_than_minutes: int
    scanned: int
    reconciled_done: int
    reconciled_failed: int
    needs_manual_review: int
    items: list[StaleEvaluationJobRecoveryItem]

    def as_dict(self) -> dict[str, Any]:
        return {
            "dry_run": self.dry_run,
            "older_than_minutes": self.older_than_minutes,
            "scanned": self.scanned,
            "reconciled_done": self.reconciled_done,
            "reconciled_failed": self.reconciled_failed,
            "needs_manual_review": self.needs_manual_review,
            "items": [item.as_dict() for item in self.items],
        }


def _coerce_evaluation_id(params: dict | None) -> uuid.UUID | None:
    raw = (params or {}).get("evaluation_id")
    if raw is None:
        return None
    try:
        return uuid.UUID(str(raw))
    except (TypeError, ValueError):
        return None


async def recover_stale_answer_sheet_eval_jobs(
    db: AsyncSession,
    *,
    older_than_minutes: int = 30,
    school_id: uuid.UUID | None = None,
    apply: bool = False,
) -> StaleEvaluationJobRecoveryResult:
    """Classify or reconcile stale answer-sheet evaluation jobs.

    Safe automatic reconciliation is limited to jobs whose linked
    ``AnswerSheetEvaluation`` is already terminal. This prevents duplicate AI
    execution while letting operators repair stale job rows after a worker or
    queue outage.

    - ``suggested`` / ``approved`` evaluations reconcile the job to ``done``.
    - ``failed`` evaluations reconcile the job to ``failed``.
    - missing, malformed, or still-processing evaluations are reported for
      manual review and left unchanged.
    """

    if older_than_minutes < 1:
        raise ValueError("older_than_minutes must be >= 1")

    cutoff = datetime.now(timezone.utc) - timedelta(minutes=older_than_minutes)
    query = (
        select(Job)
        .where(
            Job.type == "answer_sheet_eval",
            Job.status.in_(tuple(_RECOVERABLE_JOB_STATUSES)),
            Job.updated_at <= cutoff,
        )
        .order_by(Job.updated_at.asc(), Job.created_at.asc(), Job.id.asc())
    )
    if school_id is not None:
        query = query.where(Job.school_id == school_id)
    if apply:
        query = query.with_for_update(skip_locked=True)

    jobs = list((await db.execute(query)).scalars().all())
    items: list[StaleEvaluationJobRecoveryItem] = []
    reconciled_done = 0
    reconciled_failed = 0
    needs_manual_review = 0

    for job in jobs:
        original_job_status = (
            job.status.value if isinstance(job.status, JobStatus) else str(job.status)
        )
        evaluation_id = _coerce_evaluation_id(job.params)
        evaluation = None
        if evaluation_id is not None:
            eval_query = select(AnswerSheetEvaluation).where(
                AnswerSheetEvaluation.id == evaluation_id
            )
            if job.school_id is not None:
                eval_query = eval_query.where(AnswerSheetEvaluation.school_id == job.school_id)
            if apply:
                eval_query = eval_query.with_for_update()
            evaluation = (await db.execute(eval_query)).scalar_one_or_none()

        action = "manual_review"
        reason = "Linked evaluation is missing, malformed, or still processing."

        if evaluation is None:
            needs_manual_review += 1
            reason = (
                "Job params do not contain a valid evaluation_id."
                if evaluation_id is None
                else "Linked evaluation was not found in the same tenant."
            )
        elif evaluation.status in _TERMINAL_SUCCESS_EVAL_STATUSES:
            action = "mark_job_done"
            reason = "Linked evaluation already reached a successful terminal status."
            reconciled_done += 1
            if apply:
                job.status = JobStatus.DONE
                job.result = {
                    "recovered": True,
                    "reason": reason,
                    "evaluation_id": str(evaluation.id),
                    "evaluation_status": evaluation.status,
                }
                job.error = None
                job.updated_at = datetime.now(timezone.utc)
        elif evaluation.status == EVAL_STATUS_FAILED:
            action = "mark_job_failed"
            reason = "Linked evaluation already failed."
            reconciled_failed += 1
            if apply:
                job.status = JobStatus.FAILED
                job.error = "Recovered stale job: linked evaluation already failed."
                job.result = {
                    "recovered": True,
                    "reason": reason,
                    "evaluation_id": str(evaluation.id),
                    "evaluation_status": evaluation.status,
                }
                job.updated_at = datetime.now(timezone.utc)
        else:
            needs_manual_review += 1
            reason = f"Linked evaluation is not terminal: {evaluation.status}."

        items.append(
            StaleEvaluationJobRecoveryItem(
                job_id=job.id,
                school_id=job.school_id,
                job_status=original_job_status,
                evaluation_id=evaluation_id,
                evaluation_status=evaluation.status if evaluation else None,
                action=action,
                applied=apply and action in {"mark_job_done", "mark_job_failed"},
                reason=reason,
            )
        )

    if apply:
        await db.flush()
        logger.info(
            "stale_answer_sheet_eval_jobs_recovered",
            older_than_minutes=older_than_minutes,
            school_id=str(school_id) if school_id else None,
            scanned=len(jobs),
            reconciled_done=reconciled_done,
            reconciled_failed=reconciled_failed,
            needs_manual_review=needs_manual_review,
        )

    return StaleEvaluationJobRecoveryResult(
        dry_run=not apply,
        older_than_minutes=older_than_minutes,
        scanned=len(jobs),
        reconciled_done=reconciled_done,
        reconciled_failed=reconciled_failed,
        needs_manual_review=needs_manual_review,
        items=items,
    )
