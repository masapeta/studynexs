"""Scheduled stuck-job sweep — detect and REPORT background jobs that are stuck.

A job still ``queued`` past ``JOB_QUEUED_STUCK_SECONDS`` (worker down / backlogged) or still
``running`` past ``JOB_RUNNING_STUCK_SECONDS`` (worker likely crashed mid-job) is flagged via a
structured log + the existing platform job metric. This is **report-only**: it never mutates,
cancels or retries a job — surfacing the condition for operators is the whole job. It reuses the
existing ``Job`` state + timestamps and ``platform_metrics``; it adds no monitoring framework.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import structlog
from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import async_session_factory
from app.core.platform_metrics import platform_metrics
from app.db.models.job import Job, JobStatus

logger = structlog.get_logger()


async def sweep_stuck_jobs(ctx: dict) -> dict:
    """Arq cron entrypoint — flag jobs stuck in QUEUED/RUNNING beyond the configured thresholds."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    queued_cutoff = now - timedelta(seconds=settings.JOB_QUEUED_STUCK_SECONDS)
    running_cutoff = now - timedelta(seconds=settings.JOB_RUNNING_STUCK_SECONDS)

    async with async_session_factory() as session:
        # QUEUED is measured from creation (never started); RUNNING from last update (when the
        # worker flipped it to RUNNING). Both bounded by a reasonable LIMIT so a large backlog
        # can't make the sweep itself expensive.
        queued = (
            await session.execute(
                select(Job)
                .where(Job.status == JobStatus.QUEUED, Job.created_at < queued_cutoff)
                .order_by(Job.created_at)
                .limit(100)
            )
        ).scalars().all()
        running = (
            await session.execute(
                select(Job)
                .where(Job.status == JobStatus.RUNNING, Job.updated_at < running_cutoff)
                .order_by(Job.updated_at)
                .limit(100)
            )
        ).scalars().all()

    for job in queued:
        age = round((now - _aware(job.created_at)).total_seconds())
        logger.warning(
            "job_stuck",
            job_id=str(job.id),
            task=job.type,
            status=JobStatus.QUEUED.value,
            age_seconds=age,
            school_id=str(job.school_id) if job.school_id else None,
        )
        platform_metrics.record_job_event(task=job.type, status="stuck_queued")
    for job in running:
        age = round((now - _aware(job.updated_at)).total_seconds())
        logger.warning(
            "job_stuck",
            job_id=str(job.id),
            task=job.type,
            status=JobStatus.RUNNING.value,
            age_seconds=age,
            school_id=str(job.school_id) if job.school_id else None,
        )
        platform_metrics.record_job_event(task=job.type, status="stuck_running")

    total = len(queued) + len(running)
    logger.info("job_stuck_sweep_done", stuck_queued=len(queued), stuck_running=len(running))
    return {"stuck_queued": len(queued), "stuck_running": len(running), "stuck_total": total}


def _aware(dt: datetime) -> datetime:
    """Treat a naive timestamp as UTC so the age arithmetic never raises."""
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)
