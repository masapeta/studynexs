"""RAG curriculum grounding — index a pack's topics, retrieve tenant+pack-scoped with citations.

Uses the deterministic stub embedder + in-memory store, so it validates the pipeline
(chunk → embed → index → scoped retrieve → cited context) without cost. Semantic ranking
quality is covered by the live-OpenAI embedding test; here we prove wiring and isolation.
"""

import pytest

from app.db.models.academic import Subject
from app.db.models.curriculum_pack import CurriculumChapter, CurriculumPack, CurriculumTopic
from app.modules.ai.embeddings import EmbeddingService
from app.modules.ai.embeddings.stub_provider import StubEmbeddingProvider
from app.modules.ai.rag import RagService
from app.modules.ai.vectorstore.memory_store import InMemoryVectorStore


async def _seed_pack(db, school, klass, year, creator):
    subject = Subject(school_id=school.id, class_id=klass.id, name="Maths", code="MTH")
    db.add(subject)
    await db.flush()
    pack = CurriculumPack(
        school_id=school.id, class_id=klass.id, subject_id=subject.id,
        academic_year_id=year.id, board="SSC", created_by=creator.id,
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
            school_id=school.id, chapter_id=ch.id, title="Linear Equations",
            concepts=["slope", "intercept"], order_index=0,
        ),
        CurriculumTopic(
            school_id=school.id, chapter_id=ch.id, title="Quadratic Equations",
            concepts=["parabola", "roots"], order_index=1,
        ),
    ])
    await db.flush()
    return pack


def _rag(db) -> RagService:
    return RagService(
        db, embedder=EmbeddingService(provider=StubEmbeddingProvider()), store=InMemoryVectorStore()
    )


@pytest.mark.asyncio
async def test_index_retrieve_and_cited_context(
    db_session, test_school, test_class, academic_year, admin_user
):
    pack = await _seed_pack(db_session, test_school, test_class, academic_year, admin_user)
    rag = _rag(db_session)

    indexed = await rag.index_pack(pack)
    assert indexed == 2  # both topics embedded + indexed

    chunks = await rag.retrieve(
        "equations", school_id=test_school.id, pack_id=pack.id, top_k=5
    )
    assert len(chunks) == 2
    assert all(c.pack_id == str(pack.id) for c in chunks)
    topics = {c.topic for c in chunks}
    assert topics == {"Linear Equations", "Quadratic Equations"}

    context = rag.build_context(chunks)
    assert "source:" in context  # citations present
    assert "Algebra" in context  # chapter cited
    assert "[1]" in context and "[2]" in context  # numbered for reference


@pytest.mark.asyncio
async def test_retrieval_is_tenant_scoped(
    db_session, test_school, test_class, academic_year, admin_user
):
    pack = await _seed_pack(db_session, test_school, test_class, academic_year, admin_user)
    rag = _rag(db_session)
    await rag.index_pack(pack)

    # A different school must retrieve nothing from this pack's vectors.
    other = await rag.retrieve(
        "equations", school_id="00000000-0000-0000-0000-000000000000", pack_id=pack.id
    )
    assert other == []


@pytest.mark.asyncio
async def test_retrieval_is_pack_scoped(
    db_session, test_school, test_class, academic_year, admin_user
):
    pack = await _seed_pack(db_session, test_school, test_class, academic_year, admin_user)
    rag = _rag(db_session)
    await rag.index_pack(pack)

    # Same school, wrong pack → nothing (grounding never bleeds across packs).
    other = await rag.retrieve(
        "equations", school_id=test_school.id, pack_id="00000000-0000-0000-0000-000000000000"
    )
    assert other == []
