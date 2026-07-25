"""Async job queue (Arq) — Redis settings + enqueue helper.

`arq` is imported lazily inside functions so the FastAPI app stays importable
without arq installed (e.g. in CI/tests before `pip install -e .[dev]`).
"""
from __future__ import annotations

import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.platform_metrics import platform_metrics
from app.db.models.job import Job, JobStatus

settings = get_settings()
logger = structlog.get_logger()


def get_redis_settings():
    """Build Arq RedisSettings from the configured REDIS_URL."""
    from arq.connections import RedisSettings

    return RedisSettings.from_dsn(settings.REDIS_URL)


_pool = None


async def get_arq_pool():
    """Lazy-init a shared Arq Redis pool used for enqueuing jobs."""
    global _pool
    if _pool is None:
        from arq import create_pool

        _pool = await create_pool(get_redis_settings())
    return _pool


async def enqueue(
    db: AsyncSession,
    *,
    task: str,
    params: dict,
    school_id: uuid.UUID | None = None,
    created_by: uuid.UUID | None = None,
) -> Job:
    """Create a Job row (status=queued) and enqueue it for the Arq worker.

    The worker's single `run_job` entrypoint loads the row by id and dispatches to
    the handler registered under `task` (see `worker.JOB_HANDLERS`), driving the row
    through running → done/failed. Returns the Job so the caller can return its id.
    """
    job = Job(
        type=task,
        params=params,
        school_id=school_id,
        created_by=created_by,
        status=JobStatus.QUEUED,
    )
    db.add(job)
    await db.flush()

    pool = await get_arq_pool()
    # Dispatch through the generic entrypoint; job.type selects the handler.
    await pool.enqueue_job("run_job", str(job.id))
    platform_metrics.record_job_event(task=task, status=JobStatus.QUEUED.value)
    logger.info(
        "job_enqueued",
        job_id=str(job.id),
        task=task,
        school_id=str(school_id) if school_id else None,
        created_by=str(created_by) if created_by else None,
    )
    return job
