"""Batch 1 reconciliation P2 — curriculum grounding facade over Hybrid RAG."""

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from app.db.models.academic import AcademicYear, Class, Subject
from app.db.models.curriculum_pack import (
    CurriculumChapter,
    CurriculumPack,
    CurriculumTopic,
    PackStatus,
)
from app.db.models.school import School
from app.db.models.user import User, UserRole
from app.modules.ai.embeddings import EmbeddingService
from app.modules.ai.embeddings.stub_provider import StubEmbeddingProvider
from app.modules.ai.vectorstore.memory_store import InMemoryVectorStore
from app.modules.curriculum.services.curriculum_grounding import ground_approved_pack
from app.modules.curriculum.services.pack_service import PackError, PackService


def _stub_embedder() -> EmbeddingService:
    return EmbeddingService(provider=StubEmbeddingProvider())


async def _seed_approved_pack(db, *, school_code: str = "t"):
    school = School(
        name=f"School {school_code}",
        code=school_code,
        tenant_slug=school_code,
        board="SSC",
        contact_email=f"{school_code}@t.com",
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
        mobile=f"+910000000{school_code[-1]}01",
        full_name="Teacher",
        role=UserRole.TEACHER,
        is_active=True,
    )
    db.add_all([cls, teacher])
    await db.flush()
    maths = Subject(school_id=school.id, name="Maths", class_id=cls.id)
    db.add(maths)
    await db.flush()

    pack = CurriculumPack(
        school_id=school.id,
        class_id=cls.id,
        subject_id=maths.id,
        academic_year_id=ay.id,
        board="SSC",
        book_title="Maths Textbook",
        created_by=teacher.id,
        status=PackStatus.APPROVED,
        version=2,
        approved_by=teacher.id,
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
    return {
        "school": school,
        "cls": cls,
        "teacher": teacher,
        "maths": maths,
        "pack": pack,
    }


@pytest.mark.asyncio
async def test_ground_approved_pack_returns_provenance(db_session):
    ids = await _seed_approved_pack(db_session)
    grounding = await ground_approved_pack(
        db_session,
        school_id=ids["school"].id,
        pack_id=ids["pack"].id,
        class_id=ids["cls"].id,
        subject_id=ids["maths"].id,
        topics=["Linear Equations"],
        embedder=_stub_embedder(),
        store=InMemoryVectorStore(),
    )
    assert grounding.pack_id == ids["pack"].id
    assert grounding.pack_status == PackStatus.APPROVED.value
    assert grounding.pack_version == 2
    assert grounding.board == "SSC"
    assert grounding.chunk_count >= 1
    meta = grounding.as_metadata()
    assert meta["pack_id"] == str(ids["pack"].id)
    assert all(s["pack_id"] == str(ids["pack"].id) for s in grounding.sources)


@pytest.mark.asyncio
async def test_ground_approved_pack_is_tenant_scoped(db_session):
    ids_a = await _seed_approved_pack(db_session, school_code="a")
    ids_b = await _seed_approved_pack(db_session, school_code="b")

    with pytest.raises(ValueError, match="not found|Pack"):
        await ground_approved_pack(
            db_session,
            school_id=ids_b["school"].id,
            pack_id=ids_a["pack"].id,
        )

    with pytest.raises(PackError):
        await PackService(db_session).get_pack(ids_b["school"].id, ids_a["pack"].id)


@pytest.mark.asyncio
async def test_ground_approved_pack_rejects_draft_pack(db_session, test_school, test_class, academic_year, admin_user):
    from app.modules.curriculum.schemas.pack import ChapterIn, PackCreate, TopicIn
    from app.modules.curriculum.services.pack_service import PackService

    subject = Subject(school_id=test_school.id, class_id=test_class.id, name="Maths", code="M")
    db_session.add(subject)
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
    await svc.add_chapter(
        test_school.id,
        pack.id,
        ChapterIn(title="Algebra", topics=[TopicIn(title="Linear")]),
        actor_id=admin_user.id,
    )

    with pytest.raises(ValueError, match="Approve"):
        await ground_approved_pack(
            db_session,
            school_id=test_school.id,
            pack_id=pack.id,
            embedder=_stub_embedder(),
            store=InMemoryVectorStore(),
        )


@pytest.mark.asyncio
async def test_grounding_preview_endpoint(
    client,
    admin_user,
    test_school,
    test_class,
    academic_year,
    db_session,
):
    from app.modules.curriculum.schemas.pack import ChapterIn, PackCreate, TopicIn
    from app.modules.curriculum.services.pack_service import PackService
    from tests.conftest import auth_headers, get_auth_token

    subject = Subject(school_id=test_school.id, class_id=test_class.id, name="Maths", code="M2")
    db_session.add(subject)
    await db_session.flush()

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
    await svc.add_chapter(
        test_school.id,
        pack.id,
        ChapterIn(title="Algebra", topics=[TopicIn(title="Linear Equations", concepts=["slope"])]),
        actor_id=admin_user.id,
    )
    await svc.approve_pack(test_school.id, pack.id, admin_user.id)

    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.get(
        f"/api/v1/curriculum/packs/{pack.id}/grounding",
        headers=auth_headers(token),
        params={"topics": ["Linear Equations"]},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["pack_status"] == "approved"
    assert data["source_count"] >= 1
