"""
Delete audit_logs older than AUDIT_RETENTION_DAYS.
Run via cron / Container Apps job. Usage: python scripts/purge_audit_logs.py
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

import structlog
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings
from app.db.models.audit import AuditLog

settings = get_settings()
logger = structlog.get_logger()


async def main() -> None:
    if settings.AUDIT_RETENTION_DAYS <= 0:
        logger.info("audit_purge_skipped", reason="AUDIT_RETENTION_DAYS <= 0")
        return

    cutoff = datetime.now(timezone.utc) - timedelta(days=settings.AUDIT_RETENTION_DAYS)
    engine = create_async_engine(settings.DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        result = await conn.execute(
            delete(AuditLog).where(AuditLog.created_at < cutoff)
        )
        deleted = result.rowcount

    await engine.dispose()
    logger.info("audit_purge_complete", deleted=deleted, cutoff=cutoff.isoformat())


if __name__ == "__main__":
    asyncio.run(main())
