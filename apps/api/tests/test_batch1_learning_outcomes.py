"""Batch 1 reconciliation P2 — Learning Outcome CRUD and approval enforcement."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.academic import Subject
from app.db.models.curriculum_pack import PackStatus
from app.db.models.school import School
from app.db.models.user import User
from app.modules.curriculum.schemas.pack import (
    ChapterIn,
    LearningOutcomeIn,
    LearningOutcomeUpdate,
    PackCreate,
    TopicIn,
)
from app.modules.curriculum.services.pack_service import PackError, PackService
from tests.conftest import auth_headers, get_auth_token


async def _subject(db: AsyncSession, school: School, test_class) -> Subject:
    subject = Subject(school_id=school.id, class_id=test_class.id, name="Maths", code="MTH")
    db.add(subject)
    await db.flush()
    return subject


@pytest.mark.asyncio
async def test_create_and_edit_learning_outcomes_on_draft_pack(
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
            book_title="Maths",
        ),
        admin_user.id,
    )
    chapter = await svc.add_chapter(
        test_school.id,
        pack.id,
        ChapterIn(
            number="1",
            title="Algebra",
            topics=[
                TopicIn(
                    title="Linear Equations",
                    concepts=["slope"],
                    learning_outcomes=[
                        LearningOutcomeIn(
                            code="LO-1.1",
                            description="Solve linear equations in one variable.",
                        )
                    ],
                )
            ],
            learning_outcomes=[
                LearningOutcomeIn(
                    code="LO-CH-1",
                    description="Understand algebraic expressions at chapter level.",
                )
            ],
        ),
        actor_id=admin_user.id,
    )
    topics = (await svc.get_topics_for_chapters([chapter.id]))[chapter.id]
    topic_id = topics[0].id

    extra = await svc.add_learning_outcome_to_topic(
        test_school.id,
        topic_id,
        LearningOutcomeIn(description="Graph a linear equation on the coordinate plane."),
        actor_id=admin_user.id,
    )
    updated = await svc.update_learning_outcome(
        test_school.id,
        extra.id,
        LearningOutcomeUpdate(code="LO-1.2", description="Plot linear equations accurately."),
        actor_id=admin_user.id,
    )

    assert updated.code == "LO-1.2"
    topic_outcomes = await svc.get_outcomes_for_topics([topic_id])
    chapter_outcomes = await svc.get_outcomes_for_chapters([chapter.id])
    assert len(topic_outcomes[topic_id]) == 2
    assert len(chapter_outcomes[chapter.id]) == 1
    assert topics[0].concepts == ["slope"]


@pytest.mark.asyncio
async def test_learning_outcomes_persist_in_pack_detail(
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
        json={
            "number": "2",
            "title": "Geometry",
            "topics": [
                {
                    "title": "Triangles",
                    "concepts": ["pythagoras"],
                    "learning_outcomes": [
                        {
                            "code": "LO-G-1",
                            "description": "Apply Pythagoras theorem to right triangles.",
                        }
                    ],
                }
            ],
        },
    )

    resp = await client.get(f"/api/v1/curriculum/packs/{pack_id}", headers=auth_headers(token))
    assert resp.status_code == 200
    chapter = resp.json()["data"]["chapters"][0]
    assert chapter["topics"][0]["concepts"] == ["pythagoras"]
    assert chapter["topics"][0]["learning_outcomes"][0]["code"] == "LO-G-1"


@pytest.mark.asyncio
async def test_cannot_edit_outcomes_on_approved_pack(
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
            title="Stats",
            topics=[
                TopicIn(
                    title="Mean",
                    learning_outcomes=[
                        LearningOutcomeIn(description="Calculate arithmetic mean of a dataset.")
                    ],
                )
            ],
        ),
        actor_id=admin_user.id,
    )
    topics = (await svc.get_topics_for_chapters([chapter.id]))[chapter.id]
    outcome_id = (await svc.get_outcomes_for_topics([topics[0].id]))[topics[0].id][0].id
    approved = await svc.approve_pack(test_school.id, pack.id, admin_user.id)
    assert approved.status == PackStatus.APPROVED

    with pytest.raises(PackError, match="immutable"):
        await svc.update_learning_outcome(
            test_school.id,
            outcome_id,
            LearningOutcomeUpdate(description="Changed after approve."),
            actor_id=admin_user.id,
        )


@pytest.mark.asyncio
async def test_learning_outcome_endpoints_via_http(
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
    resp = await client.post(
        f"/api/v1/curriculum/packs/{pack_id}/chapters",
        headers=auth_headers(token),
        json={"title": "Numbers", "topics": [{"title": "Fractions", "concepts": ["numerator"]}]},
    )
    chapter_id = resp.json()["data"]["id"]
    topic_id = resp.json()["data"]["topics"][0]["id"]

    resp = await client.post(
        f"/api/v1/curriculum/topics/{topic_id}/learning-outcomes",
        headers=auth_headers(token),
        json={"code": "LO-F-1", "description": "Add and subtract unlike fractions."},
    )
    assert resp.status_code == 201
    outcome_id = resp.json()["data"]["id"]

    resp = await client.put(
        f"/api/v1/curriculum/learning-outcomes/{outcome_id}",
        headers=auth_headers(token),
        json={"description": "Add subtract multiply unlike fractions."},
    )
    assert resp.status_code == 200
    assert "multiply" in resp.json()["data"]["description"]

    resp = await client.post(
        f"/api/v1/curriculum/chapters/{chapter_id}/learning-outcomes",
        headers=auth_headers(token),
        json={"description": "Use fractions in real-life word problems."},
    )
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_learning_outcome_cross_tenant_protection(
    db_session: AsyncSession,
    test_school: School,
    test_class,
    academic_year,
    admin_user: User,
):
    subject = await _subject(db_session, test_school, test_class)
    other_school = School(
        name="Other",
        code="oth",
        tenant_slug="oth",
        board="SSC",
        contact_email="o@t.com",
        contact_phone="+910000000099",
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
    chapter = await svc.add_chapter(
        test_school.id,
        pack.id,
        ChapterIn(title="Algebra", topics=[TopicIn(title="Linear")]),
        actor_id=admin_user.id,
    )
    topics = (await svc.get_topics_for_chapters([chapter.id]))[chapter.id]

    with pytest.raises(PackError, match="not found"):
        await svc.add_learning_outcome_to_topic(
            other_school.id,
            topics[0].id,
            LearningOutcomeIn(description="Cross-tenant LO."),
            actor_id=admin_user.id,
        )
