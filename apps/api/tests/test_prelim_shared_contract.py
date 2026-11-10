"""Preliminary fixes + shared-contract guards (P2 Rev 2: P1, Q5, Q7, Q8)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.security import hash_password
from app.db.models.academic import Class, Subject, TeacherSubjectMapping
from app.db.models.school import School
from app.db.models.user import User, UserRole
from app.modules.workspace.assistant.role_access import restricted_domain_for, role_denied_block
from tests.conftest import access_token_for, auth_headers

# ── P1: engineering dashboard is internal-tier only (server-side) ───────────


def _prod_settings(**overrides) -> dict:
    base = dict(
        ENVIRONMENT="production",
        DEBUG=False,
        JWT_SECRET_KEY="x" * 40,
        WEBHOOK_SECRET="real-webhook-secret",
        ALLOWED_ORIGINS=["https://app.studynexs.com"],
        COOKIE_SECURE=True,
        REDIS_URL="redis://prod-redis:6379/0",
        AI_DEFAULT_PROVIDER="ollama",
        AADHAAR_ENCRYPTION_KEYS=["k"],
    )
    base.update(overrides)
    return base


def test_production_requires_explicit_deployment_tier():
    with pytest.raises(ValueError, match="DEPLOYMENT_TIER must be set"):
        Settings(**_prod_settings(DEPLOYMENT_TIER=""))
    with pytest.raises(ValueError, match="is not one of"):
        Settings(**_prod_settings(DEPLOYMENT_TIER="qa"))
    ok = Settings(**_prod_settings(DEPLOYMENT_TIER="production"))
    assert ok.deployment_tier == "production"
    assert ok.is_internal_tier is False


@pytest.mark.parametrize("tier", ["staging", "demo", "production", " Staging "])
def test_production_accepts_non_internal_tiers(tier):
    ok = Settings(**_prod_settings(DEPLOYMENT_TIER=tier))
    assert ok.deployment_tier == tier.strip().lower()
    assert ok.is_internal_tier is False


@pytest.mark.parametrize("tier", ["development", "internal", "INTERNAL", " development "])
def test_production_rejects_internal_tiers(tier):
    with pytest.raises(ValueError, match="not allowed in production"):
        Settings(**_prod_settings(DEPLOYMENT_TIER=tier))


@pytest.mark.parametrize("tier", ["", "   "])
def test_production_rejects_empty_tier(tier):
    with pytest.raises(ValueError, match="DEPLOYMENT_TIER must be set"):
        Settings(**_prod_settings(DEPLOYMENT_TIER=tier))


def test_production_rejects_missing_tier(monkeypatch):
    monkeypatch.delenv("DEPLOYMENT_TIER", raising=False)
    with pytest.raises(ValueError, match="DEPLOYMENT_TIER must be set"):
        Settings(_env_file=None, **_prod_settings())


def test_internal_tier_resolution():
    assert Settings(ENVIRONMENT="development", DEPLOYMENT_TIER="").is_internal_tier is True
    assert Settings(ENVIRONMENT="development", DEPLOYMENT_TIER="internal").is_internal_tier is True
    for tier in ("staging", "demo", "production"):
        assert Settings(ENVIRONMENT="development", DEPLOYMENT_TIER=tier).is_internal_tier is False


@pytest.mark.parametrize("tier", ["development", "internal"])
def test_development_environment_keeps_internal_tiers(tier):
    s = Settings(ENVIRONMENT="development", DEPLOYMENT_TIER=tier)
    assert s.deployment_tier == tier
    assert s.is_internal_tier is True


@pytest.mark.asyncio
async def test_engineering_status_refused_on_non_internal_tier(
    client: AsyncClient, admin_user: User, monkeypatch
):
    token = access_token_for(admin_user)
    settings = get_settings()
    monkeypatch.setattr(settings, "DEPLOYMENT_TIER", "production")
    resp = await client.get("/api/v1/platform/engineering-status", headers=auth_headers(token))
    assert resp.status_code == 404


@pytest.mark.asyncio
@pytest.mark.parametrize("tier", ["development", "internal"])
async def test_engineering_status_served_on_internal_tier(
    client: AsyncClient, admin_user: User, monkeypatch, tier
):
    token = access_token_for(admin_user)
    monkeypatch.setattr(get_settings(), "DEPLOYMENT_TIER", tier)
    resp = await client.get("/api/v1/platform/engineering-status", headers=auth_headers(token))
    assert resp.status_code == 200


# ── Q5: timetable teacher selection is class + subject scoped ───────────────


async def _class_subject(db: AsyncSession, school: School, cls: Class, name: str) -> Subject:
    subject = Subject(school_id=school.id, class_id=cls.id, name=name)
    db.add(subject)
    await db.flush()
    return subject


async def _teacher(db: AsyncSession, school: School, username: str, mobile: str) -> User:
    user = User(
        school_id=school.id,
        username=username,
        mobile=mobile,
        full_name=username.title(),
        role=UserRole.TEACHER,
        password_hash=hash_password("Teacher@123"),
        is_active=True,
    )
    db.add(user)
    await db.flush()
    return user


@pytest.mark.asyncio
async def test_timetable_teacher_list_and_save_validate_mapping(
    client: AsyncClient,
    db_session: AsyncSession,
    test_school: School,
    test_class: Class,
    admin_user: User,
):
    maths = await _class_subject(db_session, test_school, test_class, "Mathematics")
    science = await _class_subject(db_session, test_school, test_class, "Science")
    mapped = await _teacher(db_session, test_school, "maths_t", "+919000000101")
    unmapped = await _teacher(db_session, test_school, "other_t", "+919000000102")
    db_session.add(
        TeacherSubjectMapping(
            school_id=test_school.id,
            teacher_id=mapped.id,
            class_id=test_class.id,
            subject_id=maths.id,
        )
    )
    await db_session.flush()
    headers = auth_headers(access_token_for(admin_user))

    listed = await client.get(
        f"/api/v1/timetable/class/{test_class.id}/teachers?subject_id={maths.id}", headers=headers
    )
    assert listed.status_code == 200
    assert [t["teacher_id"] for t in listed.json()["data"]] == [str(mapped.id)]
    none_for_science = await client.get(
        f"/api/v1/timetable/class/{test_class.id}/teachers?subject_id={science.id}",
        headers=headers,
    )
    assert none_for_science.json()["data"] == []

    slot = {
        "class_id": str(test_class.id),
        "subject_id": str(maths.id),
        "day_of_week": "monday",
        "period_number": 1,
        "start_time": "09:00",
        "end_time": "09:45",
    }
    bad = await client.post("/api/v1/timetable", headers=headers, json={**slot, "teacher_id": str(unmapped.id)})
    assert bad.status_code == 400
    assert "not assigned" in bad.json()["detail"]
    wrong_subject = await client.post(
        "/api/v1/timetable",
        headers=headers,
        json={**slot, "subject_id": str(science.id), "teacher_id": str(mapped.id)},
    )
    assert wrong_subject.status_code == 400
    good = await client.post("/api/v1/timetable", headers=headers, json={**slot, "teacher_id": str(mapped.id)})
    assert good.status_code == 201


@pytest.mark.asyncio
async def test_timetable_teacher_list_scope_teacher_role_incharge(
    client: AsyncClient,
    db_session: AsyncSession,
    test_school: School,
    test_class: Class,
    academic_year,
    teacher_user: User,
):
    """P2: a TEACHER-role user who is incharge of a class may manage that class only."""
    test_class.class_incharge_id = teacher_user.id
    other = Class(
        school_id=test_school.id, grade="Grade 2", section="B", academic_year_id=academic_year.id
    )
    db_session.add(other)
    await db_session.flush()
    headers = auth_headers(access_token_for(teacher_user))

    own = await client.get(f"/api/v1/timetable/class/{test_class.id}/teachers", headers=headers)
    assert own.status_code == 200
    foreign = await client.get(f"/api/v1/timetable/class/{other.id}/teachers", headers=headers)
    assert foreign.status_code == 403
    # The general user directory stays role-gated (no broadening for TEACHER role).
    users = await client.get("/api/v1/users?role=teacher", headers=headers)
    assert users.status_code == 403


@pytest.mark.asyncio
async def test_timetable_teacher_list_denied_for_portal_roles(
    client: AsyncClient, test_class: Class, student_user: User, parent_user: User
):
    for user in (student_user, parent_user):
        resp = await client.get(
            f"/api/v1/timetable/class/{test_class.id}/teachers",
            headers=auth_headers(access_token_for(user)),
        )
        assert resp.status_code == 403


# ── Q8: role-denied assistant answers ────────────────────────────────────────


def test_role_denied_domain_detection():
    fees = restricted_domain_for("How much fee is pending?", "teacher")
    assert fees is not None and fees.key == "fees"
    assert restricted_domain_for("How much fee is pending?", "super_admin") is None
    assert restricted_domain_for("How much fee is pending?", "parent") is None
    assert restricted_domain_for("Which topics am I weak in?", "student") is None
    block = role_denied_block(fees, "teacher")
    assert block["kind"] == "not_found"
    assert "Subject Teacher" in block["message"]
    assert "isn't available for your role" in block["title"]


# ── Q7: tutor daily plan never emits an unresolvable lesson key ─────────────


def test_resolvable_lesson_key():
    import uuid

    from app.modules.tutor.schemas.copilot import WeakConceptStudyOut
    from app.modules.tutor.services.student_copilot_service import _resolvable_lesson_key

    def concept(slug: str, card: bool) -> WeakConceptStudyOut:
        return WeakConceptStudyOut(
            concept_id=uuid.uuid4(),
            slug=slug,
            title=slug,
            pack_id=uuid.uuid4(),
            has_approved_card=card,
        )

    assert _resolvable_lesson_key(concept("standard-form", False)) is None
    assert _resolvable_lesson_key(concept("standard-form", True)) == "standard-form"
    assert _resolvable_lesson_key(concept("fractions", False)) == "fractions"


@pytest.mark.asyncio
async def test_content_review_items_not_created_by_student_reads(
    client: AsyncClient, db_session: AsyncSession, student_user: User
):
    from app.db.models.content_review import ContentReviewItem
    from app.db.models.student import Student

    student = (
        await db_session.execute(select(Student).where(Student.user_id == student_user.id))
    ).scalar_one()
    headers = auth_headers(access_token_for(student_user))
    before = len((await db_session.execute(select(ContentReviewItem.id))).all())
    for path in ("daily-plan", "recommendations", "lessons/standard-form", "lessons/slope"):
        await client.get(f"/api/v1/tutor/students/{student.id}/{path}", headers=headers)
    after = len((await db_session.execute(select(ContentReviewItem.id))).all())
    assert after == before
