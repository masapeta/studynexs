"""Graph query API for copilots (Batch 23)."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from httpx import AsyncClient

from app.db.models.academic import AcademicYear, Class, Subject
from app.db.models.concept_card import ConceptCard, ConceptCardStatus
from app.db.models.curriculum_pack import (
    CurriculumChapter,
    CurriculumPack,
    CurriculumTopic,
    PackStatus,
)
from app.db.models.knowledge_graph import CurriculumConcept
from app.db.models.school import School
from app.db.models.user import User, UserRole
from app.modules.knowledge_graph.services.graph_query_service import GraphQueryService
from app.modules.knowledge_graph.services.graph_service import KnowledgeGraphService
from tests.conftest import access_token_for, auth_headers


async def _seed(db):
    from datetime import date

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
    admin = User(
        school_id=school.id, mobile="+910000000001", full_name="Admin",
        role=UserRole.ADMIN, is_active=True,
    )
    db.add_all([cls, admin])
    await db.flush()
    subject = Subject(school_id=school.id, name="Maths", class_id=cls.id)
    db.add(subject)
    await db.flush()
    pack = CurriculumPack(
        school_id=school.id, class_id=cls.id, subject_id=subject.id,
        academic_year_id=ay.id, board="SSC", created_by=admin.id,
        status=PackStatus.APPROVED, approved_by=admin.id,
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
        concepts=["slope"], order_index=0,
    )
    db.add(topic)
    await db.flush()
    await KnowledgeGraphService(db).build_spine_from_pack(
        school_id=school.id, pack_id=pack.id
    )
    from sqlalchemy import select

    concept = (
        await db.execute(
            select(CurriculumConcept).where(CurriculumConcept.slug == "slope")
        )
    ).scalar_one()
    card = ConceptCard(
        school_id=school.id, pack_id=pack.id, concept_id=concept.id,
        title="Slope", explanation="Slope is rise over run for a straight line.",
        status=ConceptCardStatus.APPROVED, created_by=admin.id,
        approved_by=admin.id, approved_at=datetime.now(timezone.utc),
    )
    db.add(card)
    await db.flush()
    return {"school": school, "pack": pack, "concept": concept, "admin": admin}


@pytest.mark.asyncio
async def test_concept_context_includes_card_and_counts(db_session):
    ids = await _seed(db_session)
    ctx = await GraphQueryService(db_session).get_concept_context(
        school_id=ids["school"].id,
        pack_id=ids["pack"].id,
        concept_id=ids["concept"].id,
    )
    assert ctx.has_approved_card is True
    assert ctx.concept.slug == "slope"


@pytest.mark.asyncio
async def test_concept_context_api(
    client: AsyncClient, db_session,
):
    ids = await _seed(db_session)
    token = access_token_for(ids["admin"])
    res = await client.get(
        f"/api/v1/curriculum/packs/{ids['pack'].id}/concepts/{ids['concept'].id}/context",
        headers=auth_headers(token),
    )
    assert res.status_code == 200
    body = res.json()["data"]
    assert body["has_approved_card"] is True
    assert body["concept"]["slug"] == "slope"
