"""Content Review Queue — HITL gap-filling for tutor content (Batch 20)."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.academic import AcademicYear, Class, Subject
from app.db.models.concept_card import ConceptCardStatus
from app.db.models.content_review import (
    ContentReviewItem,
    ContentReviewItemType,
    ContentReviewSource,
    ContentReviewStatus,
)
from app.db.models.curriculum_pack import (
    CurriculumChapter,
    CurriculumPack,
    CurriculumTopic,
    PackStatus,
)
from app.db.models.school import School
from app.db.models.user import User
from app.modules.curriculum.services.content_review_service import ContentReviewService
from app.modules.knowledge_graph.services.graph_service import KnowledgeGraphService
from app.modules.tutor.services.tutor_service import get_lesson
from tests.conftest import auth_headers, get_auth_token


async def _seed_pack_with_concept(
    db: AsyncSession,
    *,
    school: School,
    test_class: Class,
    year: AcademicYear,
    admin: User,
    suffix: str = "",
) -> tuple[CurriculumPack, str]:
    subject = Subject(
        school_id=school.id,
        class_id=test_class.id,
        name=f"Maths{suffix}",
        code=f"MTH{suffix}",
    )
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
async def test_enqueue_concept_gap_by_slug_handles_duplicate_pack_slugs(
    db_session: AsyncSession,
    test_school: School,
    test_class: Class,
    academic_year: AcademicYear,
    admin_user: User,
):
    """Tutor gap enqueue must not 500 when multiple approved packs share a slug."""

    from app.db.models.knowledge_graph import CurriculumConcept

    await _seed_pack_with_concept(
        db_session,
        school=test_school,
        test_class=test_class,
        year=academic_year,
        admin=admin_user,
        suffix="1",
    )
    await _seed_pack_with_concept(
        db_session,
        school=test_school,
        test_class=test_class,
        year=academic_year,
        admin=admin_user,
        suffix="2",
    )
    concepts = (
        await db_session.execute(
            select(CurriculumConcept).where(
                CurriculumConcept.school_id == test_school.id,
                CurriculumConcept.slug == "slope",
            )
        )
    ).scalars().all()
    assert len(concepts) == 2

    item = await ContentReviewService(db_session).enqueue_concept_gap_by_slug(
        school_id=test_school.id,
        slug="slope",
        created_by=admin_user.id,
        source=ContentReviewSource.TUTOR_GAP,
    )

    assert item is not None
    assert item.concept_id in {concept.id for concept in concepts}


@pytest.mark.asyncio
async def test_enqueue_concept_gap_is_idempotent(
    db_session: AsyncSession,
    test_school: School,
    test_class: Class,
    academic_year: AcademicYear,
    admin_user: User,
):
    from app.db.models.knowledge_graph import CurriculumConcept

    pack, slug = await _seed_pack_with_concept(
        db_session,
        school=test_school,
        test_class=test_class,
        year=academic_year,
        admin=admin_user,
    )
    concept = (
        await db_session.execute(
            select(CurriculumConcept).where(CurriculumConcept.slug == slug)
        )
    ).scalar_one()

    svc = ContentReviewService(db_session)
    first = await svc.enqueue_concept_gap(
        school_id=test_school.id,
        concept_id=concept.id,
        created_by=admin_user.id,
        source=ContentReviewSource.TEACHER,
    )
    second = await svc.enqueue_concept_gap(
        school_id=test_school.id,
        concept_id=concept.id,
        created_by=admin_user.id,
        source=ContentReviewSource.TEACHER,
    )
    assert first is not None
    assert second is not None
    assert first.id == second.id

    count = await db_session.scalar(
        select(func.count())
        .select_from(ContentReviewItem)
        .where(
            ContentReviewItem.concept_id == concept.id,
            ContentReviewItem.status == ContentReviewStatus.PENDING,
        )
    )
    assert count == 1


@pytest.mark.asyncio
async def test_approve_gap_promotes_concept_card(
    db_session: AsyncSession,
    test_school: School,
    test_class: Class,
    academic_year: AcademicYear,
    admin_user: User,
):
    from app.db.models.concept_card import ConceptCard
    from app.db.models.knowledge_graph import CurriculumConcept

    pack, slug = await _seed_pack_with_concept(
        db_session,
        school=test_school,
        test_class=test_class,
        year=academic_year,
        admin=admin_user,
    )
    concept = (
        await db_session.execute(
            select(CurriculumConcept).where(CurriculumConcept.slug == slug)
        )
    ).scalar_one()

    svc = ContentReviewService(db_session)
    item = await svc.enqueue_concept_gap(
        school_id=test_school.id,
        concept_id=concept.id,
        created_by=admin_user.id,
        source=ContentReviewSource.TUTOR_GAP,
    )
    assert item is not None

    item.draft_payload = {
        "title": "Understanding slope",
        "explanation": "Slope measures steepness: rise divided by run on a straight line.",
        "examples": ["Between (0,0) and (2,4) the slope is 2."],
        "hints": ["Count vertical change first"],
        "visual_kind": "generic",
    }
    await db_session.flush()

    approved = await svc.approve_item(
        school_id=test_school.id,
        item_id=item.id,
        reviewed_by=admin_user.id,
    )
    assert approved.status == ContentReviewStatus.APPROVED
    assert approved.result_card_id is not None

    card = (
        await db_session.execute(
            select(ConceptCard).where(ConceptCard.id == approved.result_card_id)
        )
    ).scalar_one()
    assert card.status == ConceptCardStatus.APPROVED


@pytest.mark.asyncio
async def test_tutor_get_lesson_enqueues_gap(
    db_session: AsyncSession,
    test_school: School,
    test_class: Class,
    academic_year: AcademicYear,
    admin_user: User,
    student_user: User,
):
    from app.db.models.student import Student

    await _seed_pack_with_concept(
        db_session,
        school=test_school,
        test_class=test_class,
        year=academic_year,
        admin=admin_user,
    )
    student = (
        await db_session.execute(
            select(Student).where(Student.user_id == student_user.id)
        )
    ).scalar_one()

    await get_lesson(
        db_session,
        school_id=test_school.id,
        student_id=student.id,
        lesson_key="slope",
    )

    pending = await db_session.scalar(
        select(func.count())
        .select_from(ContentReviewItem)
        .where(
            ContentReviewItem.item_type == ContentReviewItemType.CONCEPT_CARD_GAP,
            ContentReviewItem.source == ContentReviewSource.TUTOR_GAP,
            ContentReviewItem.status == ContentReviewStatus.PENDING,
        )
    )
    assert pending == 1


@pytest.mark.asyncio
async def test_reject_review_item(
    db_session: AsyncSession,
    test_school: School,
    test_class: Class,
    academic_year: AcademicYear,
    admin_user: User,
):
    from app.db.models.knowledge_graph import CurriculumConcept

    pack, slug = await _seed_pack_with_concept(
        db_session,
        school=test_school,
        test_class=test_class,
        year=academic_year,
        admin=admin_user,
    )
    concept = (
        await db_session.execute(
            select(CurriculumConcept).where(CurriculumConcept.slug == slug)
        )
    ).scalar_one()

    svc = ContentReviewService(db_session)
    item = await svc.enqueue_concept_gap(
        school_id=test_school.id,
        concept_id=concept.id,
        created_by=admin_user.id,
        source=ContentReviewSource.TEACHER,
    )
    assert item is not None

    rejected = await svc.reject_item(
        school_id=test_school.id,
        item_id=item.id,
        reviewed_by=admin_user.id,
        reason="Not needed this term",
    )
    assert rejected.status == ContentReviewStatus.REJECTED
    assert rejected.rejection_reason == "Not needed this term"


@pytest.mark.asyncio
async def test_content_review_api_lifecycle(
    client: AsyncClient,
    db_session: AsyncSession,
    test_school: School,
    test_class: Class,
    academic_year: AcademicYear,
    admin_user: User,
):
    from app.db.models.knowledge_graph import CurriculumConcept

    pack, slug = await _seed_pack_with_concept(
        db_session,
        school=test_school,
        test_class=test_class,
        year=academic_year,
        admin=admin_user,
    )
    concept = (
        await db_session.execute(
            select(CurriculumConcept).where(CurriculumConcept.pack_id == pack.id)
        )
    ).scalar_one()

    token = await get_auth_token(client, "test_admin", "Admin@123")

    resp = await client.post(
        f"/api/v1/curriculum/concepts/{concept.id}/content-review",
        headers=auth_headers(token),
        json={
            "title": "Slope basics",
            "explanation": "Slope is the rate of change along a straight line on a graph.",
        },
    )
    assert resp.status_code == 201, resp.text
    item_id = resp.json()["data"]["id"]

    resp = await client.get(
        f"/api/v1/curriculum/content-review/queue?pack_id={pack.id}",
        headers=auth_headers(token),
    )
    assert resp.status_code == 200
    body = resp.json()["data"]
    assert body["pending_count"] >= 1
    assert any(i["id"] == item_id for i in body["items"])

    resp = await client.post(
        f"/api/v1/curriculum/content-review/items/{item_id}/approve",
        headers=auth_headers(token),
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["status"] == "approved"
    assert resp.json()["data"]["result_card_id"] is not None
