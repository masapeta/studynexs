"""ConceptCard — draft → approve workflow and tutor grounding (Batch 18)."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.academic import AcademicYear, Class, Subject
from app.db.models.concept_card import ConceptCardStatus
from app.db.models.curriculum_pack import (
    CurriculumChapter,
    CurriculumPack,
    CurriculumTopic,
    PackStatus,
)
from app.db.models.school import School
from app.db.models.user import User, UserRole
from app.modules.curriculum.services.concept_card_service import (
    ConceptCardError,
    ConceptCardService,
)
from app.modules.curriculum.schemas.concept_card import ConceptCardCreate
from app.modules.knowledge_graph.services.graph_service import KnowledgeGraphService
from app.modules.tutor.services.tutor_service import get_lesson
from tests.conftest import auth_headers, get_auth_token


async def _seed_approved_with_concept(
    db: AsyncSession,
    *,
    school: School,
    test_class: Class,
    year: AcademicYear,
    admin: User,
) -> tuple[CurriculumPack, str]:
    subject = Subject(school_id=school.id, class_id=test_class.id, name="Maths", code="MTH")
    db.add(subject)
    await db.flush()
    pack = CurriculumPack(
        school_id=school.id,
        class_id=test_class.id,
        subject_id=subject.id,
        academic_year_id=year.id,
        board="SSC",
        created_by=admin.id,
        status=PackStatus.APPROVED,
        approved_by=admin.id,
        approved_at=datetime.now(timezone.utc),
    )
    db.add(pack)
    await db.flush()
    chapter = CurriculumChapter(
        school_id=school.id, pack_id=pack.id, number="1", title="Algebra", order_index=0
    )
    db.add(chapter)
    await db.flush()
    topic = CurriculumTopic(
        school_id=school.id,
        chapter_id=chapter.id,
        title="Linear Equations",
        order_index=0,
        concepts=["slope"],
    )
    db.add(topic)
    await db.flush()
    await KnowledgeGraphService(db).build_spine_from_pack(
        school_id=school.id, pack_id=pack.id
    )
    return pack, "slope"


@pytest.mark.asyncio
async def test_create_and_approve_concept_card(
    db_session: AsyncSession,
    test_school: School,
    test_class: Class,
    academic_year: AcademicYear,
    admin_user: User,
):
    pack, slug = await _seed_approved_with_concept(
        db_session,
        school=test_school,
        test_class=test_class,
        year=academic_year,
        admin=admin_user,
    )
    from app.db.models.knowledge_graph import CurriculumConcept
    from sqlalchemy import select

    concept = (
        await db_session.execute(
            select(CurriculumConcept).where(
                CurriculumConcept.pack_id == pack.id, CurriculumConcept.slug == slug
            )
        )
    ).scalar_one()

    svc = ConceptCardService(db_session)
    card = await svc.create_card(
        school_id=test_school.id,
        concept_id=concept.id,
        data=ConceptCardCreate(
            title="Understanding slope",
            explanation="Slope measures how steep a line is. Rise over run.",
            examples=["Find slope between (0,0) and (2,4) → 2"],
            hints=["Count vertical change first"],
        ),
        created_by=admin_user.id,
    )
    assert card.status == ConceptCardStatus.DRAFT

    approved = await svc.approve_card(
        school_id=test_school.id, card_id=card.id, approved_by=admin_user.id
    )
    assert approved.status == ConceptCardStatus.APPROVED
    assert approved.approved_at is not None


@pytest.mark.asyncio
async def test_approved_card_is_immutable(
    db_session: AsyncSession,
    test_school: School,
    test_class: Class,
    academic_year: AcademicYear,
    admin_user: User,
):
    pack, slug = await _seed_approved_with_concept(
        db_session,
        school=test_school,
        test_class=test_class,
        year=academic_year,
        admin=admin_user,
    )
    from app.db.models.knowledge_graph import CurriculumConcept
    from sqlalchemy import select

    concept = (
        await db_session.execute(
            select(CurriculumConcept).where(CurriculumConcept.slug == slug)
        )
    ).scalar_one()
    svc = ConceptCardService(db_session)
    card = await svc.create_card(
        school_id=test_school.id,
        concept_id=concept.id,
        data=ConceptCardCreate(
            title="Slope basics",
            explanation="Slope is rise divided by run for a straight line.",
        ),
        created_by=admin_user.id,
    )
    await svc.approve_card(
        school_id=test_school.id, card_id=card.id, approved_by=admin_user.id
    )

    from app.modules.curriculum.schemas.concept_card import ConceptCardUpdate

    with pytest.raises(ConceptCardError, match="immutable"):
        await svc.update_card(
            school_id=test_school.id,
            card_id=card.id,
            data=ConceptCardUpdate(title="Changed"),
        )


@pytest.mark.asyncio
async def test_tutor_uses_approved_concept_card(
    db_session: AsyncSession,
    test_school: School,
    test_class: Class,
    academic_year: AcademicYear,
    admin_user: User,
    student_user: User,
):
    from app.db.models.student import Student
    from sqlalchemy import select

    pack, slug = await _seed_approved_with_concept(
        db_session,
        school=test_school,
        test_class=test_class,
        year=academic_year,
        admin=admin_user,
    )
    from app.db.models.knowledge_graph import CurriculumConcept

    concept = (
        await db_session.execute(
            select(CurriculumConcept).where(CurriculumConcept.slug == slug)
        )
    ).scalar_one()

    student = (
        await db_session.execute(
            select(Student).where(Student.user_id == student_user.id)
        )
    ).scalar_one()

    svc = ConceptCardService(db_session)
    card = await svc.create_card(
        school_id=test_school.id,
        concept_id=concept.id,
        data=ConceptCardCreate(
            title="Slope explained",
            explanation="Slope tells us how much y changes when x increases by one.",
        ),
        created_by=admin_user.id,
    )
    await svc.approve_card(
        school_id=test_school.id, card_id=card.id, approved_by=admin_user.id
    )

    lesson = await get_lesson(
        db_session, school_id=test_school.id, student_id=student.id, lesson_key=slug
    )
    assert lesson is not None
    assert lesson.trigger == "concept_card"
    assert "Slope" in lesson.steps[0].narration or "slope" in lesson.steps[0].narration.lower()


@pytest.mark.asyncio
async def test_concept_card_api_lifecycle(
    client: AsyncClient,
    admin_user: User,
    test_school: School,
    test_class: Class,
    academic_year: AcademicYear,
    db_session: AsyncSession,
):
    pack, slug = await _seed_approved_with_concept(
        db_session,
        school=test_school,
        test_class=test_class,
        year=academic_year,
        admin=admin_user,
    )
    from app.db.models.knowledge_graph import CurriculumConcept
    from sqlalchemy import select

    concept = (
        await db_session.execute(
            select(CurriculumConcept).where(CurriculumConcept.pack_id == pack.id)
        )
    ).scalar_one()

    token = await get_auth_token(client, "test_admin", "Admin@123")

    resp = await client.post(
        f"/api/v1/curriculum/concepts/{concept.id}/cards",
        headers=auth_headers(token),
        json={
            "title": "Slope card",
            "explanation": "Slope is the rate of change of a line on a graph.",
            "examples": ["Between (1,2) and (3,6) slope is 2"],
        },
    )
    assert resp.status_code == 201, resp.text
    card_id = resp.json()["data"]["id"]

    resp = await client.get(
        f"/api/v1/curriculum/packs/{pack.id}/concept-cards",
        headers=auth_headers(token),
    )
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 1

    resp = await client.post(
        f"/api/v1/curriculum/concept-cards/{card_id}/approve",
        headers=auth_headers(token),
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "approved"
