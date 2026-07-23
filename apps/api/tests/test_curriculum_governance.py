"""Tests — teacher-owned curriculum draft editing and approval governance."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db.models.academic import Class, Subject, TeacherSubjectMapping
from app.db.models.school import School
from app.db.models.user import User, UserRole
from tests.conftest import access_token_for, auth_headers, get_auth_token


async def _subject(db: AsyncSession, school: School, test_class: Class) -> Subject:
    subject = Subject(school_id=school.id, class_id=test_class.id, name="Maths", code="MTH")
    db.add(subject)
    await db.flush()
    return subject


async def _map_teacher(
    db: AsyncSession,
    school: School,
    teacher: User,
    test_class: Class,
    subject: Subject,
) -> None:
    db.add(
        TeacherSubjectMapping(
            school_id=school.id,
            teacher_id=teacher.id,
            class_id=test_class.id,
            subject_id=subject.id,
            is_primary=True,
        )
    )
    await db.flush()


async def _incharge_user(
    db: AsyncSession, school: School, incharge_class: Class, *, username: str = "gov_incharge"
) -> User:
    user = User(
        school_id=school.id,
        username=username,
        mobile="+919876543288",
        full_name="Class Incharge",
        role=UserRole.CLASS_INCHARGE,
        password_hash=hash_password("Incharge@123"),
        is_active=True,
    )
    db.add(user)
    await db.flush()
    incharge_class.class_incharge_id = user.id
    await db.flush()
    return user


async def _create_draft_with_chapter(
    client: AsyncClient,
    token: str,
    test_class: Class,
    subject: Subject,
    academic_year,
) -> str:
    resp = await client.post(
        "/api/v1/curriculum/packs",
        headers=auth_headers(token),
        json={
            "class_id": str(test_class.id),
            "subject_id": str(subject.id),
            "academic_year_id": str(academic_year.id),
            "board": "SSC",
            "book_title": "Governance Maths",
        },
    )
    assert resp.status_code == 201, resp.text
    pack_id = resp.json()["data"]["id"]
    ch = await client.post(
        f"/api/v1/curriculum/packs/{pack_id}/chapters",
        headers=auth_headers(token),
        json={"number": "1", "title": "Algebra", "topics": [{"title": "Linear Equations"}]},
    )
    assert ch.status_code == 201, ch.text
    return pack_id


@pytest.mark.asyncio
async def test_teacher_can_create_draft_for_mapped_class_subject(
    client: AsyncClient,
    teacher_user: User,
    test_school: School,
    test_class: Class,
    academic_year,
    db_session: AsyncSession,
):
    subject = await _subject(db_session, test_school, test_class)
    await _map_teacher(db_session, test_school, teacher_user, test_class, subject)
    token = await get_auth_token(client, "test_teacher", "Teacher@123")

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
    assert resp.status_code == 201, resp.text
    assert resp.json()["data"]["created_by"] == str(teacher_user.id)


@pytest.mark.asyncio
async def test_teacher_cannot_edit_unmapped_class_subject(
    client: AsyncClient,
    teacher_user: User,
    test_school: School,
    test_class: Class,
    academic_year,
    db_session: AsyncSession,
):
    subject = await _subject(db_session, test_school, test_class)
    other_class = Class(
        school_id=test_school.id,
        grade="Grade 9",
        section="Z",
        academic_year_id=academic_year.id,
    )
    db_session.add(other_class)
    await db_session.flush()
    other_subject = Subject(
        school_id=test_school.id, class_id=other_class.id, name="Science", code="SCI"
    )
    db_session.add(other_subject)
    await db_session.flush()
    await _map_teacher(db_session, test_school, teacher_user, test_class, subject)
    token = await get_auth_token(client, "test_teacher", "Teacher@123")

    resp = await client.post(
        "/api/v1/curriculum/packs",
        headers=auth_headers(token),
        json={
            "class_id": str(other_class.id),
            "subject_id": str(other_subject.id),
            "academic_year_id": str(academic_year.id),
            "board": "SSC",
        },
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_teacher_cannot_create_draft_for_unmapped_subject_in_assigned_class(
    client: AsyncClient,
    teacher_user: User,
    test_school: School,
    test_class: Class,
    academic_year,
    db_session: AsyncSession,
):
    mapped_subject = await _subject(db_session, test_school, test_class)
    other_subject = Subject(
        school_id=test_school.id,
        class_id=test_class.id,
        name="Science",
        code="SCI",
    )
    db_session.add(other_subject)
    await db_session.flush()
    await _map_teacher(db_session, test_school, teacher_user, test_class, mapped_subject)
    token = await get_auth_token(client, "test_teacher", "Teacher@123")

    resp = await client.post(
        "/api/v1/curriculum/packs",
        headers=auth_headers(token),
        json={
            "class_id": str(test_class.id),
            "subject_id": str(other_subject.id),
            "academic_year_id": str(academic_year.id),
            "board": "SSC",
        },
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_teacher_can_edit_mapped_draft(
    client: AsyncClient,
    teacher_user: User,
    test_school: School,
    test_class: Class,
    academic_year,
    db_session: AsyncSession,
):
    subject = await _subject(db_session, test_school, test_class)
    await _map_teacher(db_session, test_school, teacher_user, test_class, subject)
    token = await get_auth_token(client, "test_teacher", "Teacher@123")
    pack_id = await _create_draft_with_chapter(
        client, token, test_class, subject, academic_year
    )
    detail = await client.get(
        f"/api/v1/curriculum/packs/{pack_id}", headers=auth_headers(token)
    )
    topic_id = detail.json()["data"]["chapters"][0]["topics"][0]["id"]

    updated = await client.put(
        f"/api/v1/curriculum/topics/{topic_id}",
        headers=auth_headers(token),
        json={"title": "Linear Equations and Graphs", "concepts": ["slope"]},
    )
    assert updated.status_code == 200, updated.text


@pytest.mark.asyncio
async def test_teacher_cannot_approve_own_draft(
    client: AsyncClient,
    teacher_user: User,
    test_school: School,
    test_class: Class,
    academic_year,
    db_session: AsyncSession,
):
    subject = await _subject(db_session, test_school, test_class)
    await _map_teacher(db_session, test_school, teacher_user, test_class, subject)
    token = await get_auth_token(client, "test_teacher", "Teacher@123")
    pack_id = await _create_draft_with_chapter(
        client, token, test_class, subject, academic_year
    )

    resp = await client.post(
        f"/api/v1/curriculum/packs/{pack_id}/approve",
        headers=auth_headers(token),
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_incharge_cannot_approve_own_authored_pack(
    client: AsyncClient,
    test_school: School,
    test_class: Class,
    academic_year,
    db_session: AsyncSession,
):
    subject = await _subject(db_session, test_school, test_class)
    incharge = await _incharge_user(db_session, test_school, test_class)
    token = access_token_for(incharge)
    pack_id = await _create_draft_with_chapter(
        client, token, test_class, subject, academic_year
    )

    resp = await client.post(
        f"/api/v1/curriculum/packs/{pack_id}/approve",
        headers=auth_headers(token),
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_incharge_can_approve_another_authors_pack(
    client: AsyncClient,
    teacher_user: User,
    test_school: School,
    test_class: Class,
    academic_year,
    db_session: AsyncSession,
):
    subject = await _subject(db_session, test_school, test_class)
    await _map_teacher(db_session, test_school, teacher_user, test_class, subject)
    await _incharge_user(db_session, test_school, test_class, username="gov_incharge_b")
    teacher_token = await get_auth_token(client, "test_teacher", "Teacher@123")
    incharge_token = await get_auth_token(client, "gov_incharge_b", "Incharge@123")
    pack_id = await _create_draft_with_chapter(
        client, teacher_token, test_class, subject, academic_year
    )

    resp = await client.post(
        f"/api/v1/curriculum/packs/{pack_id}/approve",
        headers=auth_headers(incharge_token),
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["status"] == "approved"


@pytest.mark.asyncio
async def test_incharge_cannot_approve_different_class_pack(
    client: AsyncClient,
    admin_user: User,
    test_school: School,
    test_class: Class,
    academic_year,
    db_session: AsyncSession,
):
    incharge = await _incharge_user(db_session, test_school, test_class, username="gov_incharge_c")
    other_class = Class(
        school_id=test_school.id,
        grade="Grade 9",
        section="Y",
        academic_year_id=academic_year.id,
    )
    db_session.add(other_class)
    await db_session.flush()
    other_subject = Subject(
        school_id=test_school.id,
        class_id=other_class.id,
        name="Science",
        code="SCI",
    )
    db_session.add(other_subject)
    await db_session.flush()

    admin_token = access_token_for(admin_user)
    pack_id = await _create_draft_with_chapter(
        client, admin_token, other_class, other_subject, academic_year
    )
    incharge_token = access_token_for(incharge)
    resp = await client.post(
        f"/api/v1/curriculum/packs/{pack_id}/approve",
        headers=auth_headers(incharge_token),
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_permissions_curriculum_governance_flags(
    client: AsyncClient,
    teacher_user: User,
    admin_user: User,
    test_school: School,
    test_class: Class,
    db_session: AsyncSession,
):
    await _incharge_user(db_session, test_school, test_class, username="gov_perm_incharge")
    teacher_token = await get_auth_token(client, "test_teacher", "Teacher@123")
    incharge_token = await get_auth_token(client, "gov_perm_incharge", "Incharge@123")
    admin_token = access_token_for(admin_user)

    teacher_perms = (
        await client.get("/api/v1/users/me/permissions", headers=auth_headers(teacher_token))
    ).json()["data"]
    assert teacher_perms["can_manage_curriculum"] is False
    assert teacher_perms["can_edit_curriculum_draft"] is False
    assert teacher_perms["can_approve_curriculum"] is False

    subject = await _subject(db_session, test_school, test_class)
    await _map_teacher(db_session, test_school, teacher_user, test_class, subject)
    teacher_mapped = (
        await client.get("/api/v1/users/me/permissions", headers=auth_headers(teacher_token))
    ).json()["data"]
    assert teacher_mapped["can_edit_curriculum_draft"] is True
    assert teacher_mapped["can_approve_curriculum"] is False
    assert teacher_mapped["teaching_assignments"] == [
        {"class_id": str(test_class.id), "subject_id": str(subject.id)}
    ]

    incharge_perms = (
        await client.get("/api/v1/users/me/permissions", headers=auth_headers(incharge_token))
    ).json()["data"]
    assert incharge_perms["can_edit_curriculum_draft"] is True
    assert incharge_perms["can_approve_curriculum"] is True

    admin_perms = (
        await client.get("/api/v1/users/me/permissions", headers=auth_headers(admin_token))
    ).json()["data"]
    assert admin_perms["can_edit_curriculum_draft"] is True
    assert admin_perms["can_approve_curriculum"] is True
