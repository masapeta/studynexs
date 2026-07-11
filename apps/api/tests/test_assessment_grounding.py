"""Grounded Assessment Intelligence — question-paper generation grounded in an APPROVED
CurriculumPack via the shared RAG platform.

Proves the Batch-12 contract without cost or live services (stub embedder + in-memory vector
store + a monkeypatched LLM):
- a grounded paper carries pack provenance + citation sources, and every question keeps its
  Bloom / difficulty / learning-outcome / citation metadata;
- generation REFUSES (no LLM call) when curriculum grounding is expected but unavailable — an
  empty pack, an unapproved pack, or a pack that does not belong to the class/subject;
- tenant + pack isolation of retrieval holds;
- the ungrounded free-text path is unchanged (backward compatible).
"""
import json
from datetime import date, datetime, timezone

import pytest

from app.db.models.academic import AcademicYear, Class, Subject
from app.db.models.curriculum_pack import (
    CurriculumChapter,
    CurriculumPack,
    CurriculumTopic,
    PackStatus,
)
from app.db.models.question_paper import PaperStatus
from app.db.models.school import School
from app.db.models.user import User, UserRole
from app.modules.ai.embeddings import EmbeddingService
from app.modules.ai.embeddings.stub_provider import StubEmbeddingProvider
from app.modules.ai.gateway import LLMResult
from app.modules.ai.gateway.output_guard import sanitize_paper_sections
from app.modules.ai.services.assessment_grounding import ground_for_evaluation, ground_for_pack
from app.modules.ai.services.question_paper_service import generate_paper
from app.modules.ai.vectorstore.memory_store import InMemoryVectorStore

_QP_SERVICE_LLM = "app.modules.ai.services.question_paper_service.generate_llm"


def _stub_embedder() -> EmbeddingService:
    return EmbeddingService(provider=StubEmbeddingProvider())


async def _seed(db, *, pack_status=PackStatus.APPROVED, with_topics=True, second_subject=False):
    school = School(
        name="T", code="T", tenant_slug="t", board="SSC",
        contact_email="a@t.com", contact_phone="+910000000000", is_active=True,
    )
    db.add(school)
    await db.flush()
    ay = AcademicYear(
        school_id=school.id, year_label="2026-2027",
        start_date=date(2026, 6, 1), end_date=date(2027, 5, 31), is_active=True,
    )
    db.add(ay)
    await db.flush()
    cls = Class(school_id=school.id, grade="10", section="A", academic_year_id=ay.id)
    teacher = User(
        school_id=school.id, mobile="+910000000001", full_name="Teacher",
        role=UserRole.TEACHER, is_active=True,
    )
    db.add_all([cls, teacher])
    await db.flush()
    maths = Subject(school_id=school.id, name="Maths", class_id=cls.id)
    db.add(maths)
    await db.flush()
    science = None
    if second_subject:
        science = Subject(school_id=school.id, name="Science", class_id=cls.id)
        db.add(science)
        await db.flush()

    pack = CurriculumPack(
        school_id=school.id, class_id=cls.id, subject_id=maths.id,
        academic_year_id=ay.id, board="SSC", created_by=teacher.id,
        status=pack_status,
        approved_by=teacher.id if pack_status == PackStatus.APPROVED else None,
        approved_at=datetime.now(timezone.utc) if pack_status == PackStatus.APPROVED else None,
    )
    db.add(pack)
    await db.flush()
    if with_topics:
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
    return {
        "school": school, "cls": cls, "teacher": teacher,
        "maths": maths, "science": science, "pack": pack,
    }


_GROUNDED_PAPER = {
    "title": "Maths — 10",
    "general_instructions": ["Answer all questions."],
    "sections": [
        {
            "title": "Section I",
            "instructions": "2 marks each.",
            "questions": [
                {
                    "number": "1", "text": "Solve 2x + 3 = 7.", "marks": 2, "type": "short",
                    "answer_key": "x = 2", "bloom": "Apply", "difficulty": "easy",
                    "learning_outcome": "Solve a linear equation in one variable.",
                    "concepts": ["slope", "intercept"], "citations": [1],
                },
                {
                    "number": "2", "text": "Find the roots of x^2 - 5x + 6 = 0.", "marks": 2,
                    "type": "short", "answer_key": "x = 2, 3", "bloom": "Analyze",
                    "difficulty": "medium", "learning_outcome": "Find roots of a quadratic.",
                    "concepts": ["parabola", "roots"], "citations": [2],
                },
            ],
        }
    ],
}


def _fake_llm(payload: dict, flag: dict):
    async def _gen(*_args, **_kwargs):
        flag["called"] = True
        return LLMResult(
            text=json.dumps(payload), provider="stub", model="stub-model",
            tokens_in=10, tokens_out=20, latency_ms=1,
        )
    return _gen


@pytest.mark.asyncio
async def test_grounded_generation_cites_curriculum_and_maps_metadata(db_session, monkeypatch):
    ids = await _seed(db_session)
    flag = {"called": False}
    monkeypatch.setattr(_QP_SERVICE_LLM, _fake_llm(_GROUNDED_PAPER, flag))

    paper = await generate_paper(
        db_session,
        school_id=ids["school"].id,
        created_by=ids["teacher"].id,
        class_id=ids["cls"].id,
        subject_id=ids["maths"].id,
        topics=["Linear Equations", "Quadratic Equations"],
        total_marks=80,
        duration_minutes=180,
        difficulty="balanced",
        credits_charged=0,  # isolate grounding from credit machinery (tested elsewhere)
        pack_id=ids["pack"].id,
        embedder=_stub_embedder(),
        store=InMemoryVectorStore(),
    )

    assert flag["called"] is True
    assert paper.grounded is True
    assert paper.pack_id == ids["pack"].id
    assert paper.board == "SSC"
    assert paper.status == PaperStatus.DRAFT  # HITL — teacher approves, AI never publishes

    # Citation sources are stored, numbered, and traceable to the curriculum.
    assert paper.grounding_sources
    assert {s["index"] for s in paper.grounding_sources} == {1, 2}
    assert all(s["chapter"] == "Algebra" for s in paper.grounding_sources)
    assert {s["topic"] for s in paper.grounding_sources} == {
        "Linear Equations", "Quadratic Equations"
    }

    # Per-question Assessment-Intelligence metadata survives sanitation + persistence.
    q1 = paper.sections[0]["questions"][0]
    assert q1["bloom"] == "Apply"
    assert q1["difficulty"] == "easy"
    assert q1["learning_outcome"].startswith("Solve")
    assert q1["citations"] == [1]
    assert q1["concepts"] == ["slope", "intercept"]


@pytest.mark.asyncio
async def test_generation_refuses_when_pack_has_no_curriculum(db_session, monkeypatch):
    """Grounding expected but the pack is empty → refuse; never fall back to ungrounded LLM."""
    ids = await _seed(db_session, with_topics=False)
    flag = {"called": False}
    monkeypatch.setattr(_QP_SERVICE_LLM, _fake_llm(_GROUNDED_PAPER, flag))

    with pytest.raises(ValueError, match="no chapters/topics"):
        await generate_paper(
            db_session,
            school_id=ids["school"].id,
            created_by=ids["teacher"].id,
            class_id=ids["cls"].id,
            subject_id=ids["maths"].id,
            topics=[],
            total_marks=80,
            duration_minutes=180,
            difficulty="balanced",
            credits_charged=0,
            pack_id=ids["pack"].id,
            embedder=_stub_embedder(),
            store=InMemoryVectorStore(),
        )
    assert flag["called"] is False  # the LLM must not run without grounding


@pytest.mark.asyncio
async def test_grounding_requires_approved_pack(db_session, monkeypatch):
    ids = await _seed(db_session, pack_status=PackStatus.DRAFT)
    flag = {"called": False}
    monkeypatch.setattr(_QP_SERVICE_LLM, _fake_llm(_GROUNDED_PAPER, flag))

    with pytest.raises(ValueError, match="[Aa]pprove"):
        await generate_paper(
            db_session,
            school_id=ids["school"].id,
            created_by=ids["teacher"].id,
            class_id=ids["cls"].id,
            subject_id=ids["maths"].id,
            topics=["Linear Equations"],
            total_marks=80,
            duration_minutes=180,
            difficulty="balanced",
            credits_charged=0,
            pack_id=ids["pack"].id,
            embedder=_stub_embedder(),
        )
    assert flag["called"] is False


@pytest.mark.asyncio
async def test_grounding_rejects_pack_from_wrong_subject(db_session, monkeypatch):
    """Pack isolation: a Maths pack cannot ground a Science paper for the same class."""
    ids = await _seed(db_session, second_subject=True)
    flag = {"called": False}
    monkeypatch.setattr(_QP_SERVICE_LLM, _fake_llm(_GROUNDED_PAPER, flag))

    with pytest.raises(ValueError, match="does not match"):
        await generate_paper(
            db_session,
            school_id=ids["school"].id,
            created_by=ids["teacher"].id,
            class_id=ids["cls"].id,
            subject_id=ids["science"].id,   # different subject than the pack
            topics=["Linear Equations"],
            total_marks=80,
            duration_minutes=180,
            difficulty="balanced",
            credits_charged=0,
            pack_id=ids["pack"].id,
            embedder=_stub_embedder(),
        )
    assert flag["called"] is False


@pytest.mark.asyncio
async def test_ungrounded_generation_is_unchanged(db_session, monkeypatch):
    """No pack_id → the original free-text path; grounded flag off, no sources."""
    ids = await _seed(db_session)
    flag = {"called": False}
    plain = {
        "title": "Maths — 10",
        "general_instructions": ["Answer all."],
        "sections": [{
            "title": "Section A", "instructions": "",
            "questions": [{"number": "1", "text": "What is 2+2?", "marks": 2,
                           "type": "short", "answer_key": "4"}],
        }],
    }
    monkeypatch.setattr(_QP_SERVICE_LLM, _fake_llm(plain, flag))

    paper = await generate_paper(
        db_session,
        school_id=ids["school"].id,
        created_by=ids["teacher"].id,
        class_id=ids["cls"].id,
        subject_id=ids["maths"].id,
        topics=["Algebra"],
        total_marks=80,
        duration_minutes=180,
        difficulty="balanced",
        credits_charged=0,
    )
    assert flag["called"] is True
    assert paper.grounded is False
    assert paper.pack_id is None
    assert paper.grounding_sources is None


@pytest.mark.asyncio
async def test_ground_for_pack_builds_numbered_cited_context(db_session):
    ids = await _seed(db_session)
    ctx = await ground_for_pack(
        db_session,
        pack=ids["pack"],
        topics=["Linear Equations", "Quadratic Equations"],
        embedder=_stub_embedder(),
        store=InMemoryVectorStore(),
    )
    assert not ctx.is_empty
    assert ctx.chunk_count == 2
    assert "[1]" in ctx.context_text and "[2]" in ctx.context_text
    assert "source:" in ctx.context_text
    # sources indices align 1..n with the context block numbering
    assert [s["index"] for s in ctx.sources] == [1, 2]


def test_sanitize_preserves_and_coerces_question_metadata():
    """Output guard keeps grounding metadata and coerces citations to positive ints."""
    raw = [{
        "title": "S1",
        "questions": [{
            "number": "1", "text": "Q?", "marks": 2, "type": "short",
            "bloom": "Understand", "difficulty": "EASY",
            "learning_outcome": "Understand concept.",
            "concepts": ["a", "b", ""],
            "citations": [1, "2", "junk", 0, -3, 4],
        }],
    }]
    out = sanitize_paper_sections(raw)
    q = out[0]["questions"][0]
    assert q["bloom"] == "Understand"
    assert q["difficulty"] == "easy"           # normalized to lower-case
    assert q["learning_outcome"] == "Understand concept."
    assert q["concepts"] == ["a", "b"]         # empties dropped
    assert q["citations"] == [1, 2, 4]         # non-ints and <1 dropped


@pytest.mark.asyncio
async def test_ground_for_evaluation_returns_context_for_approved_pack(db_session):
    ids = await _seed(db_session)
    ctx = await ground_for_evaluation(
        db_session,
        school_id=ids["school"].id,
        pack_id=ids["pack"].id,
        topics=["Linear Equations"],
        embedder=_stub_embedder(),
        store=InMemoryVectorStore(),
    )
    assert not ctx.is_empty
    assert ctx.chunk_count >= 1


@pytest.mark.asyncio
async def test_ground_for_evaluation_empty_when_no_pack(db_session):
    ids = await _seed(db_session)
    ctx = await ground_for_evaluation(
        db_session,
        school_id=ids["school"].id,
        pack_id=None,
        topics=["Science"],
    )
    assert ctx.is_empty


@pytest.mark.asyncio
async def test_ground_for_evaluation_empty_for_draft_pack(db_session):
    ids = await _seed(db_session, pack_status=PackStatus.DRAFT)
    ctx = await ground_for_evaluation(
        db_session,
        school_id=ids["school"].id,
        pack_id=ids["pack"].id,
        topics=["Linear Equations"],
    )
    assert ctx.is_empty
