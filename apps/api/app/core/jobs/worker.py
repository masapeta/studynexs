"""Arq worker — runs background jobs and drives each Job row's lifecycle.

Run (requires arq installed + Redis reachable):
    arq app.core.jobs.worker.WorkerSettings
or:
    python -m app.core.jobs.worker

Handlers register themselves via the `@job_task("name")` decorator; the name must
match the `task` passed to `queue.enqueue(...)`.
"""

from __future__ import annotations

import time
import uuid
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.core.jobs.queue import get_redis_settings
from app.core.platform_metrics import platform_metrics
from app.db.models.job import Job, JobStatus

logger = structlog.get_logger()

# Handlers receive (params, db_session) and return a JSON-serialisable result dict.
JobHandler = Callable[[dict, AsyncSession], Awaitable[dict]]
JOB_HANDLERS: dict[str, JobHandler] = {}


def job_task(name: str):
    """Register an async handler for a job type."""

    def decorator(fn: JobHandler) -> JobHandler:
        JOB_HANDLERS[name] = fn
        return fn

    return decorator


async def run_job(ctx, job_id: str):
    """Generic Arq entrypoint: load the Job, dispatch to its handler, persist result."""
    start = time.perf_counter()
    async with async_session_factory() as session:
        result = await session.execute(select(Job).where(Job.id == uuid.UUID(job_id)))
        job = result.scalar_one_or_none()
        if job is None:
            # The enqueueing request's transaction may not have committed yet (enqueue flushes;
            # the request commits later). arq.Retry re-queues with a short defer — a PLAIN
            # exception is NOT retried by arq and would fail the job permanently. Bounded by
            # WorkerSettings.max_tries, so a genuinely missing job still fails after a few tries.
            from arq import Retry

            logger.info("job_not_found_yet_retrying", job_id=job_id)
            platform_metrics.record_job_event(task="unknown", status="retry_not_found")
            raise Retry(defer=2)

        handler = JOB_HANDLERS.get(job.type)
        if handler is None:
            job.status = JobStatus.FAILED
            job.error = f"No handler registered for job type: {job.type}"
            await session.commit()
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            platform_metrics.record_job_event(
                task=job.type,
                status=JobStatus.FAILED.value,
                duration_ms=duration_ms,
            )
            logger.warning(
                "job_no_handler",
                job_id=job_id,
                task=job.type,
                school_id=str(job.school_id) if job.school_id else None,
                duration_ms=duration_ms,
            )
            return

        job.status = JobStatus.RUNNING
        await session.commit()
        platform_metrics.record_job_event(task=job.type, status=JobStatus.RUNNING.value)
        logger.info(
            "job_started",
            job_id=job_id,
            task=job.type,
            school_id=str(job.school_id) if job.school_id else None,
            created_by=str(job.created_by) if job.created_by else None,
        )

        try:
            params = dict(job.params or {})
            params["_job_id"] = str(job.id)
            output = await handler(params, session)
            job.status = JobStatus.DONE
            job.result = output or {}
        except Exception as exc:  # noqa: BLE001 — record any failure on the row
            job.status = JobStatus.FAILED
            job.error = str(exc)[:2000]
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            platform_metrics.record_job_event(
                task=job.type,
                status=JobStatus.FAILED.value,
                duration_ms=duration_ms,
            )
            logger.exception(
                "job_failed",
                job_id=job_id,
                task=job.type,
                school_id=str(job.school_id) if job.school_id else None,
                duration_ms=duration_ms,
            )
        finally:
            job.updated_at = datetime.now(timezone.utc)
            if job.status == JobStatus.DONE:
                duration_ms = round((time.perf_counter() - start) * 1000, 2)
                platform_metrics.record_job_event(
                    task=job.type,
                    status=JobStatus.DONE.value,
                    duration_ms=duration_ms,
                )
                logger.info(
                    "job_done",
                    job_id=job_id,
                    task=job.type,
                    school_id=str(job.school_id) if job.school_id else None,
                    duration_ms=duration_ms,
                )
            await session.commit()


async def register_job_handlers(ctx: dict | None = None) -> None:
    """Import job modules so their ``@job_task`` decorators populate JOB_HANDLERS.

    This runs on worker startup for BOTH launch paths — ``arq app.core.jobs.worker.WorkerSettings``
    (the documented command) and ``python -m app.core.jobs.worker``. The documented command
    imports this module by dotted path, so the ``if __name__ == "__main__"`` block never runs;
    without this hook JOB_HANDLERS would be empty and every job would dead-end as
    "No handler registered". New job modules must be imported here.
    """
    import app.modules.demo.jobs.tenant_cleanup_job  # noqa: F401
    import app.modules.examinations.jobs.answer_sheet_eval_job  # noqa: F401

    logger.info("job_handlers_registered", handlers=sorted(JOB_HANDLERS))


async def sweep_expired_prospect_tenants(ctx: dict) -> dict:
    from app.modules.demo.jobs.demo_sweep_cron import sweep_expired_prospect_tenants as _sweep

    return await _sweep(ctx)


def _demo_sweep_cron():
    from arq.cron import cron

    from app.core.config import get_settings

    cfg = get_settings()
    return cron(
        sweep_expired_prospect_tenants,
        minute=set(cfg.DEMO_SWEEP_CRON_MINUTES),
        run_at_startup=True,
    )


class WorkerSettings:
    """Arq worker settings — all jobs flow through the single `run_job` entrypoint."""

    functions = [run_job, sweep_expired_prospect_tenants]
    cron_jobs = [_demo_sweep_cron()]
    redis_settings = get_redis_settings()
    on_startup = register_job_handlers
    max_tries = 5  # bounds the job-not-found-yet Retry loop (see run_job)


if __name__ == "__main__":
    from arq import run_worker

    run_worker(WorkerSettings)  # type: ignore[arg-type]
