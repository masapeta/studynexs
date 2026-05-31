"""Arq worker — runs background jobs and drives each Job row's lifecycle.

Run (requires arq installed + Redis reachable):
    arq app.core.jobs.worker.WorkerSettings
or:
    python -m app.core.jobs.worker

Handlers register themselves via the `@job_task("name")` decorator; the name must
match the `task` passed to `queue.enqueue(...)`.
"""
from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.core.jobs.queue import get_redis_settings
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
    async with async_session_factory() as session:
        result = await session.execute(select(Job).where(Job.id == uuid.UUID(job_id)))
        job = result.scalar_one_or_none()
        if job is None:
            # The enqueueing request may not have committed yet — raise so Arq retries.
            raise RuntimeError(f"Job {job_id} not found yet")

        handler = JOB_HANDLERS.get(job.type)
        if handler is None:
            job.status = JobStatus.FAILED
            job.error = f"No handler registered for job type: {job.type}"
            await session.commit()
            logger.warning("job_no_handler", job_id=job_id, task=job.type)
            return

        job.status = JobStatus.RUNNING
        await session.commit()

        try:
            output = await handler(job.params, session)
            job.status = JobStatus.DONE
            job.result = output or {}
        except Exception as exc:  # noqa: BLE001 — record any failure on the row
            job.status = JobStatus.FAILED
            job.error = str(exc)[:2000]
            logger.exception("job_failed", job_id=job_id, task=job.type)
        finally:
            job.updated_at = datetime.now(timezone.utc)
            await session.commit()


class WorkerSettings:
    """Arq worker settings — all jobs flow through the single `run_job` entrypoint."""

    functions = [run_job]
    redis_settings = get_redis_settings()


if __name__ == "__main__":
    from arq import run_worker

    run_worker(WorkerSettings)  # type: ignore[arg-type]
