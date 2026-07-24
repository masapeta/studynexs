"""Student → weak Concept graph links (Batch 22)."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from app.db.models.academic import AcademicYear, Class, Subject
from app.db.models.curriculum_pack import (
    CurriculumChapter,
    CurriculumPack,
    CurriculumTopic,
    PackStatus,
)
from app.db.models.knowledge_graph import KgEdge, KgEdgeType, KgNodeType
from app.db.models.mastery import MasteryTrend
from app.db.models.school import School
from app.db.models.student import Student
from app.db.models.user import User, UserRole
from app.modules.knowledge_graph.services.graph_service import KnowledgeGraphService
from app.modules.knowledge_graph.services.student_weak_concept_service import (
    StudentWeakConceptService,
)


async def _seed(db, *, mastery_pct=55.0, concepts: list[str] | None = None):
    school = School(
        name="T", code="T", tenant_slug="t", board="SSC",
        contact_email="a@t.com", contact_phone="+910000000000", is_active=True,
    )
    db.add(school)
    await db.flush()
    from datetime import date

    ay = AcademicYear(
        school_id=school.id, year_label="2026-2027",
        start_date=date(2026, 6, 1), end_date=date(2027, 5, 31), is_active=True,
    )
    db.add(ay)
    await db.flush()
    cls = Class(school_id=school.id, grade="10", section="A", academic_year_id=ay.id)
    teacher = User(
        school_id=school.id, mobile="+910000000001", full_name="T",
        role=UserRole.TEACHER, is_active=True,
    )
    db.add_all([cls, teacher])
    await db.flush()
    subject = Subject(school_id=school.id, name="Maths", class_id=cls.id)
    db.add(subject)
    await db.flush()
    student_user = User(
        school_id=school.id, mobile="+910000000002", full_name="S",
        role=UserRole.STUDENT, is_active=True,
    )
    db.add(student_user)
    await db.flush()
    student = Student(
        school_id=school.id, user_id=student_user.id, class_id=cls.id,
        admission_no="A1",
    )
    db.add(student)
    await db.flush()

    pack = CurriculumPack(
        school_id=school.id, class_id=cls.id, subject_id=subject.id,
        academic_year_id=ay.id, board="SSC", created_by=teacher.id,
        status=PackStatus.APPROVED, approved_by=teacher.id,
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
        school_id=school.id, chapter_id=chapter.id, title="Linear Equations",
        concepts=concepts or ["slope"], order_index=0,
    )
    db.add(topic)
    await db.flush()
    await KnowledgeGraphService(db).build_spine_from_pack(
        school_id=school.id, pack_id=pack.id
    )

    ledger = [{
        "student_id": student.id,
        "topic": "linear equations",
        "topic_display": "Linear Equations",
        "mastery_pct": mastery_pct,
        "class_avg_pct": 72.0,
        "assessments_count": 2,
        "last_assessed_on": date(2026, 7, 1),
        "trend": MasteryTrend.STABLE,
        "history": [],
    }]
    return {
        "school": school, "student": student, "pack": pack,
        "subject": subject, "cls": cls, "ay": ay, "ledger": ledger,
    }


@pytest.mark.asyncio
async def test_sync_creates_struggles_with_edges(db_session):
    ids = await _seed(db_session, mastery_pct=55.0)
    svc = StudentWeakConceptService(db_session)
    count = await svc.sync_from_ledger(
        school_id=ids["school"].id,
        class_id=ids["cls"].id,
        subject_id=ids["subject"].id,
        academic_year_id=ids["ay"].id,
        ledger_rows=ids["ledger"],
    )
    assert count == 1
    edge = (
        await db_session.execute(
            select(KgEdge).where(
                KgEdge.from_id == ids["student"].id,
                KgEdge.edge_type == KgEdgeType.STRUGGLES_WITH,
            )
        )
    ).scalar_one()
    assert edge.from_node_type == KgNodeType.STUDENT
    assert edge.to_node_type == KgNodeType.CONCEPT


@pytest.mark.asyncio
async def test_sync_skips_strong_mastery(db_session):
    ids = await _seed(db_session, mastery_pct=85.0)
    svc = StudentWeakConceptService(db_session)
    count = await svc.sync_from_ledger(
        school_id=ids["school"].id,
        class_id=ids["cls"].id,
        subject_id=ids["subject"].id,
        academic_year_id=ids["ay"].id,
        ledger_rows=ids["ledger"],
    )
    assert count == 0


@pytest.mark.asyncio
async def test_get_weak_concepts_for_student(db_session):
    ids = await _seed(db_session, mastery_pct=50.0)
    svc = StudentWeakConceptService(db_session)
    await svc.sync_from_ledger(
        school_id=ids["school"].id,
        class_id=ids["cls"].id,
        subject_id=ids["subject"].id,
        academic_year_id=ids["ay"].id,
        ledger_rows=ids["ledger"],
    )
    weak = await svc.get_weak_concepts_for_student(
        school_id=ids["school"].id,
        student_id=ids["student"].id,
        subject_id=ids["subject"].id,
    )
    assert len(weak) == 1
    assert weak[0][0].slug == "slope"


@pytest.mark.asyncio
async def test_get_weak_concepts_for_student_has_deterministic_primary(db_session):
    ids = await _seed(db_session, mastery_pct=50.0, concepts=["zeta", "alpha"])
    svc = StudentWeakConceptService(db_session)
    await svc.sync_from_ledger(
        school_id=ids["school"].id,
        class_id=ids["cls"].id,
        subject_id=ids["subject"].id,
        academic_year_id=ids["ay"].id,
        ledger_rows=ids["ledger"],
    )
    weak = await svc.get_weak_concepts_for_student(
        school_id=ids["school"].id,
        student_id=ids["student"].id,
        subject_id=ids["subject"].id,
    )

    assert [concept.slug for concept, _meta in weak] == ["zeta", "alpha"]
