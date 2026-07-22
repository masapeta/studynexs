"""Academic Intelligence readiness — derived from pack status + audit events."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.curriculum_pack import PackStatus
from app.modules.curriculum.schemas.onboarding import (
    AcademicIntelligenceStatusOut,
    IntelligencePhase,
)
from app.modules.curriculum.services.pack_audit import PackAuditEventType
from app.modules.curriculum.services.pack_readiness import (
    PackReadinessSnapshot,
    approval_blockers,
    snapshot_pack_readiness,
)
from app.modules.curriculum.services.pack_service import PackError, PackService


def _event_types(events: list[dict]) -> set[str]:
    return {str(e.get("event_type") or "") for e in events}


def _rag_vector_count(events: list[dict], pack_vector_count: int | None) -> int:
    for event in reversed(events):
        if event.get("event_type") == PackAuditEventType.RAG_INDEX_SUCCEEDED.value:
            meta = event.get("metadata") or {}
            if meta.get("vector_count") is not None:
                return int(meta["vector_count"])
    return int(pack_vector_count or 0)


def compute_intelligence_status(
    *,
    pack_id: uuid.UUID,
    pack_status: PackStatus | str,
    rag_index_error: str | None,
    events: list[dict],
    readiness: PackReadinessSnapshot,
    rag_vector_count: int,
) -> AcademicIntelligenceStatusOut:
    status = pack_status.value if isinstance(pack_status, PackStatus) else str(pack_status)
    types = _event_types(events)
    approved = status == PackStatus.APPROVED.value
    has_retrievable = readiness.has_retrievable_topics
    kg_ready = PackAuditEventType.KG_SPINE_SUCCEEDED.value in types
    rag_event_ok = PackAuditEventType.RAG_INDEX_SUCCEEDED.value in types and not rag_index_error
    rag_ready = rag_event_ok and rag_vector_count > 0 and has_retrievable
    kg_failed = PackAuditEventType.KG_SPINE_FAILED.value in types
    rag_failed = (
        PackAuditEventType.RAG_INDEX_FAILED.value in types
        or bool(rag_index_error)
        or (rag_event_ok and rag_vector_count == 0)
    )
    blockers = approval_blockers(readiness)

    if not approved:
        phase = IntelligencePhase.DRAFT
        message = (
            "Draft pack — add topics with curriculum content before approval."
            if not has_retrievable
            else "Draft pack — review structure and approve when ready."
        )
        ready = False
    elif not has_retrievable:
        phase = IntelligencePhase.FAILED
        message = (
            "Approved pack has no retrievable topics — edit the pack before using AI features."
        )
        ready = False
    elif kg_ready and rag_ready:
        phase = IntelligencePhase.READY
        message = "Academic Intelligence Ready — lesson plans, papers, and tutor use this pack."
        ready = True
    elif kg_failed or rag_failed:
        phase = IntelligencePhase.FAILED
        message = "Preparation failed — retry indexing or contact support."
        ready = False
    else:
        phase = IntelligencePhase.APPROVED_PREPARING
        message = "Preparing knowledge graph and retrieval index…"
        ready = False

    if approved and kg_ready and not rag_ready and not rag_failed and has_retrievable:
        phase = IntelligencePhase.PARTIAL
        message = "Knowledge graph ready; retrieval index still preparing or failed."
        ready = False

    return AcademicIntelligenceStatusOut(
        pack_id=pack_id,
        phase=phase,
        pack_status=status,
        pack_approved=approved,
        kg_ready=kg_ready,
        rag_ready=rag_ready,
        academic_intelligence_ready=ready,
        message=message,
        rag_index_error=rag_index_error,
        retrievable_topic_count=readiness.retrievable_topic_count,
        rag_vector_count=rag_vector_count,
        can_approve=not approved and not blockers,
        approval_blockers=blockers if not approved else [],
    )


async def get_intelligence_status(
    db: AsyncSession,
    *,
    school_id: uuid.UUID,
    pack_id: uuid.UUID,
) -> AcademicIntelligenceStatusOut:
    svc = PackService(db)
    try:
        pack = await svc.get_pack(school_id, pack_id)
    except PackError as exc:
        raise ValueError(str(exc)) from exc
    events = await svc.list_pack_audit(school_id, pack_id)
    readiness = await snapshot_pack_readiness(db, school_id=school_id, pack_id=pack_id)
    vectors = _rag_vector_count(events, pack.rag_index_topic_count)
    return compute_intelligence_status(
        pack_id=pack.id,
        pack_status=pack.status,
        rag_index_error=pack.rag_index_error,
        events=events,
        readiness=readiness,
        rag_vector_count=vectors,
    )
