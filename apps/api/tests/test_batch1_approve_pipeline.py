"""Batch 1 reconciliation P3 — approve pipeline (KG spine + eager RAG + audit)."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.academic import Subject
from app.db.models.curriculum_pack import (
    CurriculumChapter,
    CurriculumPack,
    CurriculumTopic,
    PackStatus,
)
from app.db.models.knowledge_graph import CurriculumConcept, KgEdge
from app.db.models.school import School
from app.db.models.user import User
from app.modules.ai.embeddings import EmbeddingService
from app.modules.ai.embeddings.stub_provider import StubEmbeddingProvider
from app.modules.ai.rag.service import RagService
from app.modules.ai.services.assessment_grounding import ground_for_pack
from app.modules.ai.vectorstore.memory_store import InMemoryVectorStore
from app.modules.curriculum.services.pack_audit import PackAuditEventType
from app.modules.curriculum.services.pack_service import PackError, PackService
from tests.conftest import auth_headers, get_auth_token


async def _subject(db: AsyncSession, school: School, test_class) -> Subject:
    subject = Subject(school_id=school.id, class_id=test_class.id, name="Maths", code="MTH")
    db.add(subject)
    await db.flush()
    return subject


def _rag(db: AsyncSession) -> RagService:
    return RagService(
        db,
        embedder=EmbeddingService(provider=StubEmbeddingProvider()),
        store=InMemoryVectorStore(),
    )


async def _draft_pack_with_topic(
    db: AsyncSession,
    *,
    school: School,
    test_class,
    academic_year,
    admin_user: User,
) -> CurriculumPack:
    subject = await _subject(db, school, test_class)
    pack = CurriculumPack(
        school_id=school.id,
        class_id=test_class.id,
        subject_id=subject.id,
        academic_year_id=academic_year.id,
        board="SSC",
        book_title="NCERT Maths",
        created_by=admin_user.id,
    )
    db.add(pack)
    await db.flush()
    chapter = CurriculumChapter(
        school_id=school.id,
        pack_id=pack.id,
        number="1",
        title="Algebra",
        order_index=0,
    )
    db.add(chapter)
    await db.flush()
    db.add(
        CurriculumTopic(
            school_id=school.id,
            chapter_id=chapter.id,
            title="Linear Equations",
            concepts=["slope", "intercept"],
            order_index=0,
        )
    )
    await db.flush()
    return pack


@pytest.mark.asyncio
async def test_approve_builds_kg_spine_and_eager_rag(
    db_session: AsyncSession,
    test_school: School,
    test_class,
    academic_year,
    admin_user: User,
):
    pack = await _draft_pack_with_topic(
        db_session,
        school=test_school,
        test_class=test_class,
        academic_year=academic_year,
        admin_user=admin_user,
    )
    rag = _rag(db_session)
    svc = PackService(db_session, rag=rag)

    approved = await svc.approve_pack(test_school.id, pack.id, admin_user.id)

    assert approved.status == PackStatus.APPROVED
    assert approved.rag_indexed_at is not None
    assert approved.rag_index_topic_count == 1
    assert approved.rag_index_error is None

    concept_count = await db_session.scalar(
        select(func.count()).select_from(CurriculumConcept).where(
            CurriculumConcept.pack_id == pack.id
        )
    )
    edge_count = await db_session.scalar(
        select(func.count()).select_from(KgEdge).where(KgEdge.pack_id == pack.id)
    )
    assert concept_count == 2
    assert edge_count >= 3

    assert await rag.count_topic_vectors(school_id=test_school.id, pack_id=pack.id) == 1
    chunks = await rag.retrieve(
        "linear equations",
        school_id=test_school.id,
        pack_id=pack.id,
        top_k=5,
    )
    assert len(chunks) == 1
    assert chunks[0].pack_id == str(pack.id)


@pytest.mark.asyncio
async def test_approve_emits_full_audit_trail(
    db_session: AsyncSession,
    test_school: School,
    test_class,
    academic_year,
    admin_user: User,
):
    pack = await _draft_pack_with_topic(
        db_session,
        school=test_school,
        test_class=test_class,
        academic_year=academic_year,
        admin_user=admin_user,
    )
    svc = PackService(db_session, rag=_rag(db_session))
    await svc.approve_pack(test_school.id, pack.id, admin_user.id)

    types = [e["event_type"] for e in await svc.list_pack_audit(test_school.id, pack.id)]
    assert PackAuditEventType.PACK_APPROVED.value in types
    assert PackAuditEventType.KG_SPINE_STARTED.value in types
    assert PackAuditEventType.KG_SPINE_SUCCEEDED.value in types
    assert PackAuditEventType.RAG_INDEX_STARTED.value in types
    assert PackAuditEventType.RAG_INDEX_SUCCEEDED.value in types


@pytest.mark.asyncio
async def test_idempotent_approval_rejects_duplicate(
    db_session: AsyncSession,
    test_school: School,
    test_class,
    academic_year,
    admin_user: User,
):
    pack = await _draft_pack_with_topic(
        db_session,
        school=test_school,
        test_class=test_class,
        academic_year=academic_year,
        admin_user=admin_user,
    )
    rag = _rag(db_session)
    svc = PackService(db_session, rag=rag)

    await svc.approve_pack(test_school.id, pack.id, admin_user.id)
    assert await rag.count_topic_vectors(school_id=test_school.id, pack_id=pack.id) == 1

    with pytest.raises(PackError, match="already approved"):
        await svc.approve_pack(test_school.id, pack.id, admin_user.id)

    events = await svc.list_pack_audit(test_school.id, pack.id)
    assert sum(1 for e in events if e["event_type"] == PackAuditEventType.PACK_APPROVED.value) == 1
    assert await rag.count_topic_vectors(school_id=test_school.id, pack_id=pack.id) == 1


@pytest.mark.asyncio
async def test_rag_failure_does_not_block_kg_or_approval(
    db_session: AsyncSession,
    test_school: School,
    test_class,
    academic_year,
    admin_user: User,
):
    pack = await _draft_pack_with_topic(
        db_session,
        school=test_school,
        test_class=test_class,
        academic_year=academic_year,
        admin_user=admin_user,
    )
    failing_rag = AsyncMock()
    failing_rag.index_pack = AsyncMock(side_effect=RuntimeError("qdrant unavailable"))
    svc = PackService(db_session, rag=failing_rag)

    approved = await svc.approve_pack(test_school.id, pack.id, admin_user.id)

    assert approved.status == PackStatus.APPROVED
    assert approved.rag_indexed_at is None
    assert approved.rag_index_error == "qdrant unavailable"

    types = [e["event_type"] for e in await svc.list_pack_audit(test_school.id, pack.id)]
    assert PackAuditEventType.KG_SPINE_SUCCEEDED.value in types
    assert PackAuditEventType.RAG_INDEX_FAILED.value in types

    concept_count = await db_session.scalar(
        select(func.count()).select_from(CurriculumConcept).where(
            CurriculumConcept.pack_id == pack.id
        )
    )
    assert concept_count == 2


@pytest.mark.asyncio
async def test_kg_failure_does_not_block_rag_or_approval(
    db_session: AsyncSession,
    test_school: School,
    test_class,
    academic_year,
    admin_user: User,
):
    pack = await _draft_pack_with_topic(
        db_session,
        school=test_school,
        test_class=test_class,
        academic_year=academic_year,
        admin_user=admin_user,
    )
    rag = _rag(db_session)
    svc = PackService(db_session, rag=rag)

    with patch(
        "app.modules.knowledge_graph.services.graph_service.KnowledgeGraphService.build_spine_from_pack",
        new_callable=AsyncMock,
        side_effect=RuntimeError("kg build failed"),
    ):
        approved = await svc.approve_pack(test_school.id, pack.id, admin_user.id)

    assert approved.status == PackStatus.APPROVED
    assert approved.rag_indexed_at is not None
    assert approved.rag_index_topic_count == 1

    types = [e["event_type"] for e in await svc.list_pack_audit(test_school.id, pack.id)]
    assert PackAuditEventType.KG_SPINE_FAILED.value in types
    assert PackAuditEventType.RAG_INDEX_SUCCEEDED.value in types


@pytest.mark.asyncio
async def test_retry_rag_index_after_failure(
    db_session: AsyncSession,
    test_school: School,
    test_class,
    academic_year,
    admin_user: User,
):
    pack = await _draft_pack_with_topic(
        db_session,
        school=test_school,
        test_class=test_class,
        academic_year=academic_year,
        admin_user=admin_user,
    )
    failing_rag = AsyncMock()
    failing_rag.index_pack = AsyncMock(side_effect=RuntimeError("temporary outage"))
    svc = PackService(db_session, rag=failing_rag)
    await svc.approve_pack(test_school.id, pack.id, admin_user.id)

    real_rag = _rag(db_session)
    svc2 = PackService(db_session, rag=real_rag)
    retried = await svc2.retry_rag_index(test_school.id, pack.id, admin_user.id)

    assert retried.rag_indexed_at is not None
    assert retried.rag_index_topic_count == 1
    assert retried.rag_index_error is None
    assert await real_rag.count_topic_vectors(school_id=test_school.id, pack_id=pack.id) == 1

    types = [e["event_type"] for e in await svc2.list_pack_audit(test_school.id, pack.id)]
    assert types.count(PackAuditEventType.RAG_INDEX_SUCCEEDED.value) == 1


@pytest.mark.asyncio
async def test_lazy_fallback_when_eager_index_failed(
    db_session: AsyncSession,
    test_school: School,
    test_class,
    academic_year,
    admin_user: User,
):
    pack = await _draft_pack_with_topic(
        db_session,
        school=test_school,
        test_class=test_class,
        academic_year=academic_year,
        admin_user=admin_user,
    )
    failing_rag = AsyncMock()
    failing_rag.index_pack = AsyncMock(side_effect=RuntimeError("eager failed"))
    svc = PackService(db_session, rag=failing_rag)
    approved = await svc.approve_pack(test_school.id, pack.id, admin_user.id)
    assert approved.rag_index_error is not None

    store = InMemoryVectorStore()
    ctx = await ground_for_pack(
        db_session,
        pack=approved,
        topics=["Linear Equations"],
        embedder=EmbeddingService(provider=StubEmbeddingProvider()),
        store=store,
    )
    assert not ctx.is_empty
    assert "Linear Equations" in ctx.context_text


@pytest.mark.asyncio
async def test_approve_cross_tenant_isolation_unchanged(
    db_session: AsyncSession,
    test_school: School,
    test_class,
    academic_year,
    admin_user: User,
):
    pack = await _draft_pack_with_topic(
        db_session,
        school=test_school,
        test_class=test_class,
        academic_year=academic_year,
        admin_user=admin_user,
    )
    other = School(
        name="Other",
        code="oth3",
        tenant_slug="oth3",
        board="SSC",
        contact_email="o3@t.com",
        contact_phone="+910000000097",
        is_active=True,
    )
    db_session.add(other)
    await db_session.flush()

    svc = PackService(db_session, rag=_rag(db_session))
    await svc.approve_pack(test_school.id, pack.id, admin_user.id)

    with pytest.raises(PackError, match="not found"):
        await svc.approve_pack(other.id, pack.id, admin_user.id)


@pytest.mark.asyncio
async def test_approve_via_http_exposes_rag_index_status(
    client: AsyncClient,
    admin_user: User,
    test_school: School,
    test_class,
    academic_year,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
):
    _store = InMemoryVectorStore()

    def _test_rag_factory(db: AsyncSession, **_kw) -> RagService:
        return RagService(
            db,
            embedder=EmbeddingService(provider=StubEmbeddingProvider()),
            store=_store,
        )

    monkeypatch.setattr(
        "app.modules.ai.rag.service.RagService",
        _test_rag_factory,
    )

    subject = await _subject(db_session, test_school, test_class)
    token = await get_auth_token(client, "test_admin", "Admin@123")

    resp = await client.post(
        "/api/v1/curriculum/packs",
        headers=auth_headers(token),
        json={
            "class_id": str(test_class.id),
            "subject_id": str(subject.id),
            "academic_year_id": str(academic_year.id),
            "board": "SSC",
            "book_title": "NCERT Maths",
        },
    )
    pack_id = resp.json()["data"]["id"]

    await client.post(
        f"/api/v1/curriculum/packs/{pack_id}/chapters",
        headers=auth_headers(token),
        json={
            "number": "1",
            "title": "Algebra",
            "topics": [{"title": "Linear Equations", "concepts": ["slope"]}],
        },
    )

    resp = await client.post(
        f"/api/v1/curriculum/packs/{pack_id}/approve",
        headers=auth_headers(token),
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["status"] == "approved"
    assert data["rag_indexed_at"] is not None
    assert data["rag_index_topic_count"] == 1
    assert data["rag_index_error"] is None

    rag = _test_rag_factory(db_session)
    chunks = await rag.retrieve(
        "equations",
        school_id=test_school.id,
        pack_id=uuid.UUID(pack_id),
        top_k=5,
    )
    assert len(chunks) == 1
