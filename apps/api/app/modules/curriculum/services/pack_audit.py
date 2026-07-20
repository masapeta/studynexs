"""Curriculum pack audit — append-only lifecycle evidence (Batch 1 reconciliation).

Curriculum-specific audit records; not a generic audit framework.
No updates, deletes, or edits — events are immutable once written.
"""
from __future__ import annotations

import enum
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.curriculum_pack import CurriculumPackAuditEvent
from app.db.models.user import User


class PackAuditEventType(str, enum.Enum):
    PACK_CREATED = "pack_created"
    PACK_UPDATED = "pack_updated"
    CHAPTER_ADDED = "chapter_added"
    TOPIC_ADDED = "topic_added"
    LEARNING_OUTCOME_ADDED = "learning_outcome_added"
    LEARNING_OUTCOME_UPDATED = "learning_outcome_updated"
    PACK_APPROVED = "pack_approved"
    KG_SPINE_STARTED = "kg_spine_started"
    KG_SPINE_SUCCEEDED = "kg_spine_succeeded"
    KG_SPINE_FAILED = "kg_spine_failed"
    RAG_INDEX_STARTED = "rag_index_started"
    RAG_INDEX_SUCCEEDED = "rag_index_succeeded"
    RAG_INDEX_FAILED = "rag_index_failed"


async def record_pack_audit_event(
    db: AsyncSession,
    *,
    school_id: uuid.UUID,
    pack_id: uuid.UUID,
    actor_id: uuid.UUID,
    event_type: PackAuditEventType | str,
    metadata: dict | None = None,
) -> CurriculumPackAuditEvent:
    et = event_type.value if isinstance(event_type, PackAuditEventType) else str(event_type)
    event = CurriculumPackAuditEvent(
        school_id=school_id,
        pack_id=pack_id,
        actor_id=actor_id,
        event_type=et,
        event_metadata=metadata or {},
    )
    db.add(event)
    await db.flush()
    return event


async def list_pack_audit_events(
    db: AsyncSession,
    *,
    school_id: uuid.UUID,
    pack_id: uuid.UUID,
) -> list[dict]:
    rows = (
        await db.execute(
            select(CurriculumPackAuditEvent, User.full_name)
            .outerjoin(User, User.id == CurriculumPackAuditEvent.actor_id)
            .where(
                CurriculumPackAuditEvent.school_id == school_id,
                CurriculumPackAuditEvent.pack_id == pack_id,
            )
            .order_by(CurriculumPackAuditEvent.created_at.asc())
        )
    ).all()
    return [
        {
            "id": event.id,
            "pack_id": event.pack_id,
            "actor_id": event.actor_id,
            "actor_name": actor_name,
            "event_type": event.event_type,
            "metadata": event.event_metadata or {},
            "created_at": event.created_at,
        }
        for event, actor_name in rows
    ]
