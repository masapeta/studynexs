"""Batch 1 reconciliation P2 — append-only curriculum pack audit trail."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.academic import Subject
from app.db.models.school import School
from app.db.models.user import User
from app.modules.curriculum.schemas.pack import ChapterIn, LearningOutcomeIn, PackCreate, TopicIn
from app.modules.curriculum.services.pack_audit import PackAuditEventType
from app.modules.curriculum.services.pack_service import PackService
from tests.conftest import auth_headers, get_auth_token


async def _subject(db: AsyncSession, school: School, test_class) -> Subject:
    subject = Subject(school_id=school.id, class_id=test_class.id, name="Maths", code="MTH")
    db.add(subject)
    await db.flush()
    return subject


@pytest.mark.asyncio
async def test_lifecycle_events_recorded(
    db_session: AsyncSession,
    test_school: School,
    test_class,
    academic_year,
    admin_user: User,
):
    subject = await _subject(db_session, test_school, test_class)
    svc = PackService(db_session)

    pack = await svc.create_pack(
        test_school.id,
        PackCreate(
            class_id=test_class.id,
            subject_id=subject.id,
            academic_year_id=academic_year.id,
            board="SSC",
        ),
        admin_user.id,
    )
    chapter = await svc.add_chapter(
        test_school.id,
        pack.id,
        ChapterIn(
            number="1",
            title="Algebra",
            topics=[TopicIn(title="Linear Equations")],
        ),
        actor_id=admin_user.id,
    )
    topics = (await svc.get_topics_for_chapters([chapter.id]))[chapter.id]
    await svc.add_learning_outcome_to_topic(
        test_school.id,
        topics[0].id,
        LearningOutcomeIn(code="LO-1", description="Solve linear equations."),
        actor_id=admin_user.id,
    )
    await svc.approve_pack(test_school.id, pack.id, admin_user.id)

    events = await svc.list_pack_audit(test_school.id, pack.id)
    types = [e["event_type"] for e in events]
    assert PackAuditEventType.PACK_CREATED.value in types
    assert PackAuditEventType.CHAPTER_ADDED.value in types
    assert PackAuditEventType.LEARNING_OUTCOME_ADDED.value in types
    assert PackAuditEventType.PACK_APPROVED.value in types
    assert all(e["actor_id"] == admin_user.id for e in events)


@pytest.mark.asyncio
async def test_approval_event_traceable(
    db_session: AsyncSession,
    test_school: School,
    test_class,
    academic_year,
    admin_user: User,
):
    subject = await _subject(db_session, test_school, test_class)
    svc = PackService(db_session)
    pack = await svc.create_pack(
        test_school.id,
        PackCreate(
            class_id=test_class.id,
            subject_id=subject.id,
            academic_year_id=academic_year.id,
            board="SSC",
        ),
        admin_user.id,
    )
    await svc.add_chapter(
        test_school.id,
        pack.id,
        ChapterIn(title="Geometry"),
        actor_id=admin_user.id,
    )
    await svc.approve_pack(test_school.id, pack.id, admin_user.id)

    approved = next(
        e for e in await svc.list_pack_audit(test_school.id, pack.id)
        if e["event_type"] == PackAuditEventType.PACK_APPROVED.value
    )
    assert approved["metadata"]["version"] == 1
    assert "approved_at" in approved["metadata"]


@pytest.mark.asyncio
async def test_audit_endpoint_via_http(
    client: AsyncClient,
    admin_user: User,
    test_school: School,
    test_class,
    academic_year,
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
        json={"title": "Algebra"},
    )

    resp = await client.get(
        f"/api/v1/curriculum/packs/{pack_id}/audit",
        headers=auth_headers(token),
    )
    assert resp.status_code == 200
    types = [e["event_type"] for e in resp.json()["data"]]
    assert "pack_created" in types
    assert "chapter_added" in types


@pytest.mark.asyncio
async def test_audit_cross_tenant_protection(
    db_session: AsyncSession,
    test_school: School,
    test_class,
    academic_year,
    admin_user: User,
):
    subject = await _subject(db_session, test_school, test_class)
    other_school = School(
        name="Other",
        code="oth2",
        tenant_slug="oth2",
        board="SSC",
        contact_email="o2@t.com",
        contact_phone="+910000000098",
        is_active=True,
    )
    db_session.add(other_school)
    await db_session.flush()

    svc = PackService(db_session)
    pack = await svc.create_pack(
        test_school.id,
        PackCreate(
            class_id=test_class.id,
            subject_id=subject.id,
            academic_year_id=academic_year.id,
            board="SSC",
        ),
        admin_user.id,
    )

    from app.modules.curriculum.services.pack_service import PackError

    with pytest.raises(PackError, match="not found"):
        await svc.list_pack_audit(other_school.id, pack.id)
