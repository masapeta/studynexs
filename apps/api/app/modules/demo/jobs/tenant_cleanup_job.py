"""Arq handler — purge an expired prospect tenant (Stage 2B)."""
from __future__ import annotations

import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_redis
from app.core.jobs.worker import job_task
from app.modules.demo.services.cleanup_service import TenantCleanupService

logger = structlog.get_logger()


@job_task("tenant_cleanup")
async def tenant_cleanup_handler(params: dict, db: AsyncSession) -> dict:
    school_id = uuid.UUID(params["school_id"])
    exclude_job_id = uuid.UUID(params["_job_id"]) if params.get("_job_id") else None
    redis = await get_redis()
    service = TenantCleanupService(db, redis=redis)
    result = await service.purge_prospect_tenant(school_id, exclude_job_id=exclude_job_id)
    logger.info("tenant_cleanup_job_done", **result)
    return result
