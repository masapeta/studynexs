"""DB snapshot for soak monitoring. Usage: python scripts/monitor_snapshot.py"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings

settings = get_settings()


async def main() -> None:
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async with engine.connect() as conn:
        audit = await conn.execute(
            text(
                """
                SELECT COUNT(*) AS rows,
                       pg_size_pretty(pg_total_relation_size('audit_logs')) AS size
                FROM audit_logs
                """
            )
        )
        audit_row = audit.one()

        connections = await conn.execute(
            text(
                """
                SELECT state, count(*) AS cnt
                FROM pg_stat_activity
                WHERE datname = current_database()
                GROUP BY state
                """
            )
        )
        states = {row.state or "unknown": row.cnt for row in connections}

    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "audit_logs_rows": audit_row.rows,
        "audit_logs_size": audit_row.size,
        "pg_connections": states,
    }
    print(json.dumps(payload))
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
