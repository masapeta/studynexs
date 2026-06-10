"""
Outbox Worker — polls outbox_events and dispatches to target modules.
Runs as a background asyncio task or standalone process.

Usage:
  python -m app.workers.outbox_worker        (standalone)
  Called from lifespan in main.py             (embedded)
"""

import asyncio
import traceback

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.db.models.outbox import OutboxEvent, OutboxStatus

settings = get_settings()
logger = structlog.get_logger()

# ── Event Handlers Registry ──────────────────────────────────────────────────

HANDLERS: dict[str, callable] = {}


def register_handler(event_type: str):
    """Decorator to register an outbox event handler."""
    def decorator(func):
        HANDLERS[event_type] = func
        return func
    return decorator


# ── Built-in Handlers ────────────────────────────────────────────────────────

@register_handler("fee_paid")
async def handle_fee_paid(payload: dict, db: AsyncSession):
    """When fee is paid → create notification for parent."""
    logger.info("fee_paid_event", student_id=payload.get("student_id"))
    # In production: send SMS/push via notification service


@register_handler("attendance_marked")
async def handle_attendance_marked(payload: dict, db: AsyncSession):
    """When attendance marked absent → notify parent."""
    logger.info("attendance_absent_event", student_id=payload.get("student_id"))


@register_handler("notice_published")
async def handle_notice_published(payload: dict, db: AsyncSession):
    """When notice published → queue push notifications."""
    logger.info("notice_published_event", notice_id=payload.get("notice_id"))


@register_handler("exam_marks_entered")
async def handle_exam_marks(payload: dict, db: AsyncSession):
    """When marks entered → recompute the class×subject topic-mastery ledger."""
    import uuid as _uuid

    # Lazy import — the worker module must stay importable without the app stack.
    from app.modules.mastery.services.mastery_service import recompute_class_subject

    rows = await recompute_class_subject(
        db,
        school_id=_uuid.UUID(payload["school_id"]),
        class_id=_uuid.UUID(payload["class_id"]),
        subject_id=_uuid.UUID(payload["subject_id"]),
    )
    logger.info("exam_marks_event", exam_id=payload.get("exam_id"), mastery_rows=rows)


# ── Worker Loop ──────────────────────────────────────────────────────────────


async def process_pending_events(session: AsyncSession, batch_size: int = 20) -> int:
    """Process a batch of pending outbox events. Returns count processed."""
    result = await session.execute(
        select(OutboxEvent)
        .where(OutboxEvent.status == OutboxStatus.PENDING)
        .order_by(OutboxEvent.created_at)
        .limit(batch_size)
        .with_for_update(skip_locked=True)  # Skip events being processed by another worker
    )
    events = list(result.scalars().all())

    if not events:
        return 0

    processed = 0
    for event in events:
        event.status = OutboxStatus.PROCESSING
        await session.flush()

        handler = HANDLERS.get(event.event_type)
        if not handler:
            logger.warning("no_handler", event_type=event.event_type, event_id=str(event.id))
            event.status = OutboxStatus.DEAD_LETTER
            event.last_error = f"No handler registered for: {event.event_type}"
            await session.flush()
            continue

        try:
            await handler(event.payload, session)
            event.status = OutboxStatus.DELIVERED
            processed += 1
        except Exception as e:
            event.retry_count += 1
            event.last_error = traceback.format_exc()[-500:]

            if event.retry_count >= event.max_retries:
                event.status = OutboxStatus.DEAD_LETTER
                logger.error("event_dead_letter", event_id=str(event.id), error=str(e))
            else:
                event.status = OutboxStatus.PENDING  # Will be retried
                logger.warning("event_retry", event_id=str(event.id), retry=event.retry_count)

        await session.flush()

    await session.commit()
    return processed


async def run_worker(poll_interval: float = 2.0):
    """Main worker loop — polls every N seconds."""
    logger.info("outbox_worker_started", poll_interval=poll_interval)

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    while True:
        try:
            async with session_factory() as session:
                count = await process_pending_events(session)
                if count:
                    logger.info("outbox_batch_processed", count=count)
        except Exception as e:
            logger.error("outbox_worker_error", error=str(e))

        await asyncio.sleep(poll_interval)


# ── Standalone Entry Point ───────────────────────────────────────────────────

if __name__ == "__main__":
    asyncio.run(run_worker())
