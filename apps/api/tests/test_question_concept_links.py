"""Question → Concept graph links (Batch 19)."""
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select

from app.db.models.academic import AcademicYear, Class, Subject
from app.db.models.curriculum_pack import (
    CurriculumChapter,
    CurriculumPack,
    CurriculumTopic,
    PackStatus,
)
from app.db.models.knowledge_graph import CurriculumConcept, KgEdge, KgEdgeType, KgNodeType
from app.db.models.question_bank import QuestionBankItem
from app.db.models.question_paper import PaperStatus, QuestionPaper
from app.db.models.school import School
from app.db.models.user import User, UserRole
from app.modules.ai.services.question_bank_service import ingest_from_paper
from app.modules.knowledge_graph.services.graph_service import KnowledgeGraphService
from app.modules.knowledge_graph.services.question_concept_link_service import (
    QuestionConceptLinkService,
)
from tests.conftest import access_token_for, auth_headers


async def _seed_grounded_paper(db):
    school = School(
        name="T",
        code="T",
        tenant_slug="t",
        board="SSC",
        contact_email="a@t.com",
        contact_phone="+910000000000",
        is_active=True,
    )
    db.add(school)
    await db.flush()
    ay = AcademicYear(
        school_id=school.id,
        year_label="2026-2027",
        start_date=date(2026, 6, 1),
        end_date=date(2027, 5, 31),
        is_active=True,
    )
    db.add(ay)
    await db.flush()
    cls = Class(school_id=school.id, grade="10", section="A", academic_year_id=ay.id)
    teacher = User(
        school_id=school.id,
        mobile="+910000000001",
        full_name="Teacher",
        role=UserRole.TEACHER,
        is_active=True,
    )
    approver = User(
        school_id=school.id,
        mobile="+910000000002",
        full_name="Approver",
        role=UserRole.CLASS_INCHARGE,
        is_active=True,
    )
    db.add_all([cls, teacher, approver])
    await db.flush()
    cls.class_incharge_id = approver.id
    maths = Subject(school_id=school.id, name="Maths", class_id=cls.id)
    db.add(maths)
    await db.flush()

    pack = CurriculumPack(
        school_id=school.id,
        class_id=cls.id,
        subject_id=maths.id,
        academic_year_id=ay.id,
        board="SSC",
        created_by=teacher.id,
        status=PackStatus.APPROVED,
        approved_by=teacher.id,
        approved_at=datetime.now(timezone.utc),
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
    linear = CurriculumTopic(
        school_id=school.id,
        chapter_id=chapter.id,
        title="Linear Equations",
        concepts=["slope", "intercept"],
        order_index=0,
    )
    quadratic = CurriculumTopic(
        school_id=school.id,
        chapter_id=chapter.id,
        title="Quadratic Equations",
        concepts=["parabola", "roots"],
        order_index=1,
    )
    db.add_all([linear, quadratic])
    await db.flush()

    await KnowledgeGraphService(db).build_spine_from_pack(
        school_id=school.id, pack_id=pack.id
    )

    grounding_sources = [
        {
            "index": 1,
            "chapter": "Algebra",
            "topic": "Linear Equations",
            "ref_id": str(linear.id),
        },
        {
            "index": 2,
            "chapter": "Algebra",
            "topic": "Quadratic Equations",
            "ref_id": str(quadratic.id),
        },
    ]
    sections = [
        {
            "title": "Section I",
            "questions": [
                {
                    "number": "1",
                    "text": "Solve 2x + 3 = 7.",
                    "marks": 2,
                    "type": "short",
                    "answer_key": "x = 2",
                    "concepts": ["slope", "intercept"],
                    "citations": [1],
                },
                {
                    "number": "2",
                    "text": "Find roots of x^2 - 5x + 6 = 0.",
                    "marks": 2,
                    "type": "short",
                    "answer_key": "x = 2, 3",
                    "concepts": ["roots"],
                    "citations": [2],
                },
            ],
        }
    ]
    paper = QuestionPaper(
        school_id=school.id,
        class_id=cls.id,
        subject_id=maths.id,
        created_by=teacher.id,
        pack_id=pack.id,
        grounded=True,
        grounding_sources=grounding_sources,
        title="Grounded Unit Test",
        board="SSC",
        grade="10",
        subject_name="Maths",
        total_marks=Decimal("4"),
        topics=["Linear Equations", "Quadratic Equations"],
        sections=sections,
        status=PaperStatus.APPROVED,
        ai_model="stub",
    )
    db.add(paper)
    await db.flush()
    return {
        "school": school,
        "cls": cls,
        "maths": maths,
        "pack": pack,
        "linear": linear,
        "quadratic": quadratic,
        "paper": paper,
        "approver": approver,
        "teacher": teacher,
    }


@pytest.mark.asyncio
async def test_ingest_links_bank_items_to_concepts(db_session):
    ids = await _seed_grounded_paper(db_session)
    now = datetime.now(timezone.utc)

    items = await ingest_from_paper(
        db_session,
        ids["paper"],
        approved_by=ids["approver"].id,
        approved_at=now,
    )
    assert len(items) == 2

    edge_count = await db_session.scalar(
        select(func.count())
        .select_from(KgEdge)
        .where(
            KgEdge.school_id == ids["school"].id,
            KgEdge.edge_type == KgEdgeType.TESTS,
        )
    )
    assert edge_count == 3  # q1 → slope + intercept; q2 → roots

    q1_edges = list(
        (
            await db_session.execute(
                select(KgEdge).where(
                    KgEdge.from_id == items[0].id,
                    KgEdge.edge_type == KgEdgeType.TESTS,
                )
            )
        ).scalars().all()
    )
    assert len(q1_edges) == 2
    assert all(e.from_node_type == KgNodeType.QUESTION_BANK_ITEM for e in q1_edges)
    assert all(e.to_node_type == KgNodeType.CONCEPT for e in q1_edges)


@pytest.mark.asyncio
async def test_ingest_ungrounded_paper_creates_no_links(db_session):
    ids = await _seed_grounded_paper(db_session)
    paper = ids["paper"]
    paper.grounded = False
    paper.pack_id = None
    paper.grounding_sources = None
    now = datetime.now(timezone.utc)

    await ingest_from_paper(
        db_session, paper, approved_by=ids["approver"].id, approved_at=now
    )

    edge_count = await db_session.scalar(
        select(func.count())
        .select_from(KgEdge)
        .where(KgEdge.edge_type == KgEdgeType.TESTS)
    )
    assert edge_count == 0


@pytest.mark.asyncio
async def test_reingest_replaces_concept_links(db_session):
    ids = await _seed_grounded_paper(db_session)
    now = datetime.now(timezone.utc)
    paper = ids["paper"]

    first = await ingest_from_paper(
        db_session, paper, approved_by=ids["approver"].id, approved_at=now
    )
    first_ids = {item.id for item in first}

    paper.sections[0]["questions"][0]["concepts"] = ["slope"]
    await ingest_from_paper(
        db_session, paper, approved_by=ids["approver"].id, approved_at=now
    )

    orphan_edges = await db_session.scalar(
        select(func.count())
        .select_from(KgEdge)
        .where(
            KgEdge.from_id.in_(first_ids),
            KgEdge.edge_type == KgEdgeType.TESTS,
        )
    )
    assert orphan_edges == 0

    current_items = list(
        (
            await db_session.execute(
                select(QuestionBankItem).where(
                    QuestionBankItem.source_paper_id == paper.id
                )
            )
        ).scalars().all()
    )
    linker = QuestionConceptLinkService(db_session)
    q1_concepts = await linker.get_concepts_for_item(
        school_id=ids["school"].id, item_id=current_items[0].id
    )
    assert len(q1_concepts) == 1
    assert q1_concepts[0].slug == "slope"


@pytest.mark.asyncio
async def test_spine_rebuild_preserves_question_links(db_session):
    ids = await _seed_grounded_paper(db_session)
    now = datetime.now(timezone.utc)

    items = await ingest_from_paper(
        db_session,
        ids["paper"],
        approved_by=ids["approver"].id,
        approved_at=now,
    )

    kg = KnowledgeGraphService(db_session)
    await kg.build_spine_from_pack(school_id=ids["school"].id, pack_id=ids["pack"].id)

    tests_edges = await db_session.scalar(
        select(func.count())
        .select_from(KgEdge)
        .where(KgEdge.edge_type == KgEdgeType.TESTS)
    )
    assert tests_edges == 3

    linker = QuestionConceptLinkService(db_session)
    concepts = await linker.get_concepts_for_item(
        school_id=ids["school"].id, item_id=items[0].id
    )
    assert len(concepts) == 2


@pytest.mark.asyncio
async def test_api_lists_concepts_for_bank_item(client: AsyncClient, db_session):
    ids = await _seed_grounded_paper(db_session)
    now = datetime.now(timezone.utc)
    items = await ingest_from_paper(
        db_session,
        ids["paper"],
        approved_by=ids["approver"].id,
        approved_at=now,
    )
    token = access_token_for(ids["approver"])
    res = await client.get(
        f"/api/v1/ai/question-bank/items/{items[0].id}/concepts",
        headers=auth_headers(token),
    )
    assert res.status_code == 200
    body = res.json()["data"]
    assert body["item_id"] == str(items[0].id)
    slugs = {c["slug"] for c in body["concepts"]}
    assert slugs == {"slope", "intercept"}


@pytest.mark.asyncio
async def test_resolve_concepts_by_slug_without_citations(db_session):
    ids = await _seed_grounded_paper(db_session)
    linker = QuestionConceptLinkService(db_session)
    concept_ids = await linker.resolve_concept_ids(
        school_id=ids["school"].id,
        pack_id=ids["pack"].id,
        grounding_sources=None,
        question={"concepts": ["parabola", "roots"]},
    )
    assert len(concept_ids) == 2
    rows = list(
        (
            await db_session.execute(
                select(CurriculumConcept.slug).where(
                    CurriculumConcept.id.in_(concept_ids)
                )
            )
        ).scalars().all()
    )
    assert set(rows) == {"parabola", "roots"}
