"""Scheduled sweep of expired prospect demo tenants (Stage 2B)."""
from __future__ import annotations

import structlog

from app.core.database import async_session_factory
from app.core.dependencies import get_redis
from app.modules.demo.services.demo_session_service import DemoSessionService

logger = structlog.get_logger()


async def sweep_expired_prospect_tenants(ctx: dict) -> dict:
    """Arq cron entrypoint — deactivate expired demos and enqueue cleanup."""
    async with async_session_factory() as session:
        redis = await get_redis()
        service = DemoSessionService(session, redis=redis)
        swept = await service.sweep_expired(enqueue_cleanup=True)
        logger.info("demo_sweep_cron_done", count=len(swept), slugs=swept)
        return {"swept_count": len(swept), "tenant_slugs": swept}
