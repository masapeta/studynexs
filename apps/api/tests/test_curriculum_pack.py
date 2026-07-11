"""Tests — curriculum packs: build draft, approve to immutable, versioning, isolation."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.academic import AcademicYear, Class, Subject
from app.db.models.school import School
from app.db.models.user import User
from tests.conftest import access_token_for, auth_headers, get_auth_token


async def _subject(db: AsyncSession, school: School, test_class: Class) -> Subject:
    subject = Subject(school_id=school.id, class_id=test_class.id, name="Maths", code="MTH")
    db.add(subject)
    await db.flush()
    return subject


async def _new_pack(
    client: AsyncClient, token: str, test_class: Class, subject: Subject, year: AcademicYear
):
    return await client.post(
        "/api/v1/curriculum/packs",
        headers=auth_headers(token),
        json={
            "class_id": str(test_class.id),
            "subject_id": str(subject.id),
            "academic_year_id": str(year.id),
            "board": "SSC",
            "book_title": "NCERT Maths",
        },
    )


@pytest.mark.asyncio
async def test_pack_build_approve_immutable_and_version(
    client: AsyncClient,
    admin_user: User,
    test_school: School,
    test_class: Class,
    academic_year: AcademicYear,
    db_session: AsyncSession,
):
    subject = await _subject(db_session, test_school, test_class)
    token = await get_auth_token(client, "test_admin", "Admin@123")

    # Create draft pack v1.
    resp = await _new_pack(client, token, test_class, subject, academic_year)
    assert resp.status_code == 201, resp.text
    pack = resp.json()["data"]
    assert pack["status"] == "draft"
    assert pack["version"] == 1
    pack_id = pack["id"]

    # Cannot approve an empty pack.
    resp = await client.post(
        f"/api/v1/curriculum/packs/{pack_id}/approve", headers=auth_headers(token)
    )
    assert resp.status_code == 400

    # Add a chapter with a topic.
    resp = await client.post(
        f"/api/v1/curriculum/packs/{pack_id}/chapters",
        headers=auth_headers(token),
        json={
            "number": "1",
            "title": "Algebra",
            "topics": [{"title": "Linear Equations", "concepts": ["slope"]}],
        },
    )
    assert resp.status_code == 201, resp.text

    # Detail reflects the tree.
    resp = await client.get(f"/api/v1/curriculum/packs/{pack_id}", headers=auth_headers(token))
    assert resp.status_code == 200
    detail = resp.json()["data"]
    assert len(detail["chapters"]) == 1
    assert detail["chapters"][0]["topics"][0]["title"] == "Linear Equations"

    # Approve -> immutable.
    resp = await client.post(
        f"/api/v1/curriculum/packs/{pack_id}/approve", headers=auth_headers(token)
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "approved"

    # Editing an approved pack is rejected.
    resp = await client.post(
        f"/api/v1/curriculum/packs/{pack_id}/chapters",
        headers=auth_headers(token),
        json={"title": "Geometry"},
    )
    assert resp.status_code == 409

    # A new pack for the same scope gets version 2.
    resp = await _new_pack(client, token, test_class, subject, academic_year)
    assert resp.status_code == 201
    assert resp.json()["data"]["version"] == 2


@pytest.mark.asyncio
async def test_pack_tenant_isolation(
    client: AsyncClient,
    admin_user: User,
    test_school: School,
    test_class: Class,
    academic_year: AcademicYear,
    db_session: AsyncSession,
):
    subject = await _subject(db_session, test_school, test_class)
    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await _new_pack(client, token, test_class, subject, academic_year)
    pack_id = resp.json()["data"]["id"]

    # A different school's admin cannot read it.
    from app.core.security import hash_password
    from app.db.models.user import UserRole

    other = School(
        name="Other School",
        code="OTHP",
        tenant_slug="otherp",
        board="CBSE",
        contact_email="o@p.com",
        contact_phone="+911111100000",
        is_active=True,
    )
    db_session.add(other)
    await db_session.flush()
    other_admin = User(
        school_id=other.id,
        username="other_admin",
        mobile="+911111100001",
        full_name="Other Admin",
        role=UserRole.ADMIN,
        password_hash=hash_password("Admin@123"),
        is_active=True,
    )
    db_session.add(other_admin)
    await db_session.flush()

    # Issue the other school's token directly — the shared client sends X-Tenant-Slug=test,
    # so a cross-tenant /auth/login would (correctly) fail; here we only need a valid token
    # scoped to the other school to prove the pack is not readable across tenants.
    other_token = access_token_for(other_admin, tenant_slug="otherp")
    resp = await client.get(
        f"/api/v1/curriculum/packs/{pack_id}", headers=auth_headers(other_token)
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_pack_build_requires_staff(
    client: AsyncClient,
    admin_user: User,
    student_user: User,
    test_school: School,
    test_class: Class,
    academic_year: AcademicYear,
    db_session: AsyncSession,
):
    subject = await _subject(db_session, test_school, test_class)
    token = await get_auth_token(client, "test_student", "Student@123")
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
    assert resp.status_code == 403
