"""RAG hybrid search + re-ranking (Batch 24)."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from httpx import AsyncClient

from app.db.models.academic import Subject
from app.db.models.concept_card import ConceptCard, ConceptCardStatus
from app.db.models.curriculum_pack import (
    CurriculumChapter,
    CurriculumPack,
    CurriculumTopic,
    PackStatus,
)
from app.modules.ai.embeddings import EmbeddingService
from app.modules.ai.embeddings.stub_provider import StubEmbeddingProvider
from app.modules.ai.rag import HybridRetrievalOptions, HybridRetrievalService, RagService
from app.modules.ai.vectorstore.memory_store import InMemoryVectorStore
from app.modules.knowledge_graph.services.graph_service import KnowledgeGraphService
from tests.conftest import access_token_for, auth_headers


async def _seed_two_topic_pack(db, school, klass, year, creator):
    subject = Subject(school_id=school.id, class_id=klass.id, name="Maths", code="MTH")
    db.add(subject)
    await db.flush()
    pack = CurriculumPack(
        school_id=school.id,
        class_id=klass.id,
        subject_id=subject.id,
        academic_year_id=year.id,
        board="SSC",
        created_by=creator.id,
        status=PackStatus.APPROVED,
        approved_by=creator.id,
        approved_at=datetime.now(timezone.utc),
    )
    db.add(pack)
    await db.flush()
    ch = CurriculumChapter(
        school_id=school.id, pack_id=pack.id, number="1", title="Algebra", order_index=0
    )
    db.add(ch)
    await db.flush()
    db.add_all([
        CurriculumTopic(
            school_id=school.id,
            chapter_id=ch.id,
            title="Linear Equations",
            concepts=["slope", "intercept"],
            order_index=0,
        ),
        CurriculumTopic(
            school_id=school.id,
            chapter_id=ch.id,
            title="Quadratic Equations",
            concepts=["parabola", "roots"],
            order_index=1,
        ),
    ])
    await db.flush()
    await KnowledgeGraphService(db).build_spine_from_pack(
        school_id=school.id, pack_id=pack.id
    )
    return pack, ch


def _hybrid(db) -> HybridRetrievalService:
    rag = RagService(
        db,
        embedder=EmbeddingService(provider=StubEmbeddingProvider()),
        store=InMemoryVectorStore(),
    )
    return HybridRetrievalService(db, rag)


@pytest.mark.asyncio
async def test_hybrid_expands_concept_match(
    db_session, test_school, test_class, academic_year, admin_user
):
    pack, _ = await _seed_two_topic_pack(
        db_session, test_school, test_class, academic_year, admin_user
    )
    rag = RagService(
        db_session,
        embedder=EmbeddingService(provider=StubEmbeddingProvider()),
        store=InMemoryVectorStore(),
    )
    await rag.index_pack(pack)

    hybrid = _hybrid(db_session)
    hits = await hybrid.retrieve_hybrid(
        "slope intercept",
        school_id=test_school.id,
        pack_id=pack.id,
        top_k=2,
        options=HybridRetrievalOptions(rerank=True),
    )
    topics = {h.topic for h in hits}
    assert "Linear Equations" in topics
    assert len(hits) <= 2


@pytest.mark.asyncio
async def test_hybrid_rerank_boosts_approved_card(
    db_session, test_school, test_class, academic_year, admin_user
):
    pack, _ = await _seed_two_topic_pack(
        db_session, test_school, test_class, academic_year, admin_user
    )
    from sqlalchemy import select

    from app.db.models.knowledge_graph import CurriculumConcept

    concept = (
        await db_session.execute(
            select(CurriculumConcept).where(CurriculumConcept.slug == "slope")
        )
    ).scalar_one()
    db_session.add(
        ConceptCard(
            school_id=test_school.id,
            pack_id=pack.id,
            concept_id=concept.id,
            title="Slope",
            explanation="Approved slope card.",
            status=ConceptCardStatus.APPROVED,
            created_by=admin_user.id,
            approved_by=admin_user.id,
            approved_at=datetime.now(timezone.utc),
        )
    )
    await db_session.flush()

    rag = RagService(
        db_session,
        embedder=EmbeddingService(provider=StubEmbeddingProvider()),
        store=InMemoryVectorStore(),
    )
    await rag.index_pack(pack)
    hybrid = _hybrid(db_session)
    hits = await hybrid.retrieve_hybrid(
        "slope linear",
        school_id=test_school.id,
        pack_id=pack.id,
        top_k=2,
        options=HybridRetrievalOptions(rerank=True),
    )
    assert hits
    linear = next(h for h in hits if h.topic == "Linear Equations")
    assert linear.score > 0


@pytest.mark.asyncio
async def test_hybrid_rag_search_api(
    client: AsyncClient, db_session, test_school, test_class, academic_year, admin_user
):
    pack, _ = await _seed_two_topic_pack(
        db_session, test_school, test_class, academic_year, admin_user
    )
    rag = RagService(
        db_session,
        embedder=EmbeddingService(provider=StubEmbeddingProvider()),
        store=InMemoryVectorStore(),
    )
    await rag.index_pack(pack)

    token = access_token_for(admin_user)
    res = await client.get(
        f"/api/v1/curriculum/packs/{pack.id}/rag/search",
        params={"q": "slope", "top_k": 3},
        headers=auth_headers(token),
    )
    assert res.status_code == 200
    body = res.json()["data"]
    assert body["pack_id"] == str(pack.id)
    assert len(body["hits"]) >= 1
