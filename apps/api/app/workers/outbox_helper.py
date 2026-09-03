"""
Outbox helper — convenience function to enqueue events from any module.
"""


from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.outbox import OutboxEvent


async def emit_event(
    db: AsyncSession,
    event_type: str,
    payload: dict,
    target_module: str = "notifications",
) -> OutboxEvent:
    """
    Enqueue an event in the outbox table.
    The outbox worker will pick it up and dispatch.

    Usage:
        await emit_event(db, "fee_paid", {"student_id": "...", "amount": 3500}, "notifications")
    """
    event = OutboxEvent(
        event_type=event_type,
        payload=payload,
        target_module=target_module,
    )
    db.add(event)
    await db.flush()
    return event
