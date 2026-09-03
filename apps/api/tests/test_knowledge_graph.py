"""Knowledge Graph — curriculum spine build and query (Batch 17)."""
from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.academic import AcademicYear, Class, Subject
from app.db.models.curriculum_pack import (
    CurriculumChapter,
    CurriculumPack,
    CurriculumTopic,
    PackStatus,
)
from app.db.models.knowledge_graph import CurriculumConcept, KgEdge, KgEdgeType, KgNodeType
from app.db.models.school import School
from app.db.models.user import User
from app.modules.curriculum.services.pack_service import PackError
from app.modules.knowledge_graph.services.graph_service import (
    KnowledgeGraphService,
    concept_slug,
)
from tests.conftest import auth_headers, get_auth_token


def test_concept_slug_normalizes_labels():
    assert concept_slug("Linear Equations") == "linear-equations"
    assert concept_slug("  Factorisation!  ") == "factorisation"


async def _subject(db: AsyncSession, school: School, test_class: Class) -> Subject:
    subject = Subject(school_id=school.id, class_id=test_class.id, name="Maths", code="MTH")
    db.add(subject)
    await db.flush()
    return subject


async def _seed_draft_pack(
    db: AsyncSession,
    *,
    school: School,
    test_class: Class,
    year: AcademicYear,
    admin: User,
) -> tuple[CurriculumPack, CurriculumChapter, CurriculumTopic]:
    subject = await _subject(db, school, test_class)
    pack = CurriculumPack(
        school_id=school.id,
        class_id=test_class.id,
        subject_id=subject.id,
        academic_year_id=year.id,
        board="SSC",
        created_by=admin.id,
        status=PackStatus.DRAFT,
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
    topic = CurriculumTopic(
        school_id=school.id,
        chapter_id=chapter.id,
        title="Linear Equations",
        order_index=0,
        concepts=["slope", "intercept"],
    )
    db.add(topic)
    await db.flush()
    return pack, chapter, topic


@pytest.mark.asyncio
async def test_build_spine_on_approve(
    db_session: AsyncSession,
    test_school: School,
    test_class: Class,
    academic_year: AcademicYear,
    admin_user: User,
):
    pack, chapter, topic = await _seed_draft_pack(
        db_session,
        school=test_school,
        test_class=test_class,
        year=academic_year,
        admin=admin_user,
    )
    pack.status = PackStatus.APPROVED
    await db_session.flush()

    svc = KnowledgeGraphService(db_session)
    result = await svc.build_spine_from_pack(school_id=test_school.id, pack_id=pack.id)

    assert result.concepts_created == 2
    assert result.edges_created >= 4  # pack→subject, pack→chapter, chapter→topic, 2× topic→concept

    concepts = (
        await db_session.execute(
            select(CurriculumConcept).where(CurriculumConcept.pack_id == pack.id)
        )
    ).scalars().all()
    assert len(concepts) == 2
    slugs = {c.slug for c in concepts}
    assert slugs == {"slope", "intercept"}

    edges = (
        await db_session.execute(
            select(KgEdge).where(KgEdge.pack_id == pack.id, KgEdge.school_id == test_school.id)
        )
    ).scalars().all()
    assert any(
        e.edge_type == KgEdgeType.CONTAINS
        and e.from_node_type == KgNodeType.TOPIC
        and e.from_id == topic.id
        for e in edges
    )


@pytest.mark.asyncio
async def test_spine_idempotent_rebuild(
    db_session: AsyncSession,
    test_school: School,
    test_class: Class,
    academic_year: AcademicYear,
    admin_user: User,
):
    pack, _, _ = await _seed_draft_pack(
        db_session,
        school=test_school,
        test_class=test_class,
        year=academic_year,
        admin=admin_user,
    )
    pack.status = PackStatus.APPROVED
    await db_session.flush()

    svc = KnowledgeGraphService(db_session)
    await svc.build_spine_from_pack(school_id=test_school.id, pack_id=pack.id)
    await svc.build_spine_from_pack(school_id=test_school.id, pack_id=pack.id)

    concept_count = await db_session.scalar(
        select(func.count()).select_from(CurriculumConcept).where(
            CurriculumConcept.pack_id == pack.id
        )
    )
    edge_count = await db_session.scalar(
        select(func.count()).select_from(KgEdge).where(KgEdge.pack_id == pack.id)
    )
    assert concept_count == 2
    assert edge_count >= 4


@pytest.mark.asyncio
async def test_spine_tenant_isolation(
    db_session: AsyncSession,
    test_school: School,
    test_class: Class,
    academic_year: AcademicYear,
    admin_user: User,
):
    pack, _, _ = await _seed_draft_pack(
        db_session,
        school=test_school,
        test_class=test_class,
        year=academic_year,
        admin=admin_user,
    )
    pack.status = PackStatus.APPROVED
    await db_session.flush()
    await KnowledgeGraphService(db_session).build_spine_from_pack(
        school_id=test_school.id, pack_id=pack.id
    )

    other = School(
        name="Other",
        code="O2",
        tenant_slug="o2",
        board="CBSE",
        contact_email="o@o.com",
        contact_phone="+910000000002",
        is_active=True,
    )
    db_session.add(other)
    await db_session.flush()

    svc = KnowledgeGraphService(db_session)
    with pytest.raises(PackError):
        await svc.get_spine(school_id=other.id, pack_id=pack.id)


@pytest.mark.asyncio
async def test_approve_pack_builds_graph_via_http(
    client: AsyncClient,
    admin_user: User,
    test_school: School,
    test_class: Class,
    academic_year: AcademicYear,
    db_session: AsyncSession,
):
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
        },
    )
    pack_id = resp.json()["data"]["id"]

    await client.post(
        f"/api/v1/curriculum/packs/{pack_id}/chapters",
        headers=auth_headers(token),
        json={
            "number": "1",
            "title": "Algebra",
            "topics": [{"title": "Quadratics", "concepts": ["factorisation", "formula"]}],
        },
    )

    resp = await client.post(
        f"/api/v1/curriculum/packs/{pack_id}/approve", headers=auth_headers(token)
    )
    assert resp.status_code == 200

    resp = await client.get(
        f"/api/v1/curriculum/packs/{pack_id}/graph", headers=auth_headers(token)
    )
    assert resp.status_code == 200
    spine = resp.json()["data"]
    assert spine["concept_count"] == 2
    assert spine["edge_count"] >= 4
    assert spine["chapters"][0]["topics"][0]["concepts"][0]["slug"] == "factorisation"


@pytest.mark.asyncio
async def test_backfill_approved_pack(
    db_session: AsyncSession,
    test_school: School,
    test_class: Class,
    academic_year: AcademicYear,
    admin_user: User,
):
    pack, _, _ = await _seed_draft_pack(
        db_session,
        school=test_school,
        test_class=test_class,
        year=academic_year,
        admin=admin_user,
    )
    pack.status = PackStatus.APPROVED
    await db_session.flush()

    built = await KnowledgeGraphService(db_session).backfill_approved_packs(
        school_id=test_school.id
    )
    assert built == 1

    concept_count = await db_session.scalar(
        select(func.count()).select_from(CurriculumConcept).where(
            CurriculumConcept.pack_id == pack.id
        )
    )
    assert concept_count == 2
