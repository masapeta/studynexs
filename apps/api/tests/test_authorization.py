"""Tests — object-level authorization and tenant-scoped resources."""

from datetime import date, datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db.models.academic import Class
from app.db.models.fee import FeeReceipt, FeeStructure, PaymentMode, StudentFeeRecord
from app.db.models.file import FileCategory, UploadedFile
from app.db.models.school import School
from app.db.models.student import Student
from app.db.models.user import User, UserRole
from tests.conftest import auth_headers, get_auth_token


async def _make_student(
    db: AsyncSession, school: School, test_class: Class,
    *, admission_no: str, username: str, mobile: str,
) -> Student:
    """Create an unrelated student (User + Student) for negative authz cases."""
    user = User(
        school_id=school.id, username=username, mobile=mobile,
        full_name="Other Student", role=UserRole.STUDENT,
        password_hash=hash_password("Other@123"), is_active=True,
    )
    db.add(user)
    await db.flush()
    student = Student(
        school_id=school.id, user_id=user.id, class_id=test_class.id,
        admission_no=admission_no, roll_no="9",
    )
    db.add(student)
    await db.flush()
    return student


async def _student_of(db: AsyncSession, student_user: User) -> Student:
    return (
        await db.execute(select(Student).where(Student.user_id == student_user.id))
    ).scalar_one()


@pytest.mark.asyncio
async def test_file_download_wrong_school_returns_404(
    client: AsyncClient,
    admin_user: User,
    db_session: AsyncSession,
):
    other_school = School(
        name="Other School",
        code="OTH",
        tenant_slug="other",
        board="CBSE",
        contact_email="o@test.com",
        contact_phone="+911111111111",
        is_active=True,
    )
    db_session.add(other_school)
    await db_session.flush()

    foreign_file = UploadedFile(
        school_id=other_school.id,
        filename="secret.pdf",
        original_name="secret.pdf",
        content_type="application/pdf",
        size_bytes=10,
        category=FileCategory.DOCUMENT,
        storage_path="/tmp/unused",
        url="/api/v1/files/00000000-0000-0000-0000-000000000001",
        uploaded_by=admin_user.id,
    )
    db_session.add(foreign_file)
    await db_session.flush()

    token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.get(
        f"/api/v1/files/{foreign_file.id}",
        headers=auth_headers(token),
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_student_cannot_pay_fees(
    client: AsyncClient,
    admin_user: User,
    student_user: User,
    fee_setup: FeeStructure,
    db_session: AsyncSession,
):
    res = await db_session.execute(
        select(Student).where(Student.user_id == student_user.id)
    )
    student = res.scalar_one()

    fee_record = StudentFeeRecord(
        school_id=admin_user.school_id,
        student_id=student.id,
        fee_structure_id=fee_setup.id,
        amount=fee_setup.amount,
        due_date=date(2026, 7, 5),
    )
    db_session.add(fee_record)
    await db_session.flush()

    token = await get_auth_token(client, "test_student", "Student@123")
    resp = await client.post(
        "/api/v1/fees/pay",
        headers=auth_headers(token),
        json={
            "fee_record_id": str(fee_record.id),
            "amount": 1000.0,
            "payment_mode": "cash",
        },
    )
    assert resp.status_code == 403


# ── Academic roster / profile / parents ────────────────────────────────────────

@pytest.mark.asyncio
async def test_student_roster_is_staff_only(
    client: AsyncClient, admin_user: User, student_user: User, parent_user: User
):
    """Roster listing is staff-only; parents/students cannot enumerate the school."""
    for username, password in (("test_student", "Student@123"), ("test_parent", "Parent@123")):
        token = await get_auth_token(client, username, password)
        resp = await client.get("/api/v1/academic/students", headers=auth_headers(token))
        assert resp.status_code == 403, f"{username} should be denied the roster"

    admin_token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.get("/api/v1/academic/students", headers=auth_headers(admin_token))
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_student_profile_object_level_access(
    client: AsyncClient,
    admin_user: User,
    student_user: User,
    parent_user: User,
    test_school: School,
    test_class: Class,
    db_session: AsyncSession,
):
    child = await _student_of(db_session, student_user)
    other = await _make_student(
        db_session, test_school, test_class,
        admission_no="ADM999", username="other_student", mobile="+919000000999",
    )

    parent_token = await get_auth_token(client, "test_parent", "Parent@123")
    student_token = await get_auth_token(client, "test_student", "Student@123")
    admin_token = await get_auth_token(client, "test_admin", "Admin@123")

    # Parent of the child + the student themselves + staff may read the profile.
    for token in (parent_token, student_token, admin_token):
        resp = await client.get(
            f"/api/v1/academic/students/{child.id}/profile", headers=auth_headers(token)
        )
        assert resp.status_code == 200

    # Parent and student must NOT read an unrelated student's profile.
    for token in (parent_token, student_token):
        resp = await client.get(
            f"/api/v1/academic/students/{other.id}/profile", headers=auth_headers(token)
        )
        assert resp.status_code == 403


@pytest.mark.asyncio
async def test_student_parents_object_level_access(
    client: AsyncClient,
    admin_user: User,
    student_user: User,
    parent_user: User,
    test_school: School,
    test_class: Class,
    db_session: AsyncSession,
):
    child = await _student_of(db_session, student_user)
    other = await _make_student(
        db_session, test_school, test_class,
        admission_no="ADM998", username="other_student2", mobile="+919000000998",
    )

    parent_token = await get_auth_token(client, "test_parent", "Parent@123")

    resp = await client.get(
        f"/api/v1/academic/students/{child.id}/parents", headers=auth_headers(parent_token)
    )
    assert resp.status_code == 200

    resp = await client.get(
        f"/api/v1/academic/students/{other.id}/parents", headers=auth_headers(parent_token)
    )
    assert resp.status_code == 403


# ── Receipt download ────────────────────────────────────────────────────────────

async def _make_receipt(
    db: AsyncSession, school: School, student: Student, number: str, seq: int
) -> FeeReceipt:
    receipt = FeeReceipt(
        school_id=school.id,
        receipt_number=number,
        student_id=student.id,
        student_name="Snapshot Name",
        class_name="Grade 1-A",
        amount_paid=1000,
        payment_mode=PaymentMode.CASH,
        fee_type="Tuition",
        paid_at=datetime.now(timezone.utc),
        school_name=school.name,
        receipt_sequence=seq,
    )
    db.add(receipt)
    await db.flush()
    return receipt


@pytest.mark.asyncio
async def test_receipt_download_object_level_access(
    client: AsyncClient,
    student_user: User,
    parent_user: User,
    test_school: School,
    test_class: Class,
    db_session: AsyncSession,
):
    child = await _student_of(db_session, student_user)
    other = await _make_student(
        db_session, test_school, test_class,
        admission_no="ADM997", username="other_student3", mobile="+919000000997",
    )
    own_receipt = await _make_receipt(db_session, test_school, child, "TST-2026-00001", 1)
    other_receipt = await _make_receipt(db_session, test_school, other, "TST-2026-00002", 2)

    parent_token = await get_auth_token(client, "test_parent", "Parent@123")

    resp = await client.get(
        f"/api/v1/fees/receipt/{own_receipt.receipt_number}", headers=auth_headers(parent_token)
    )
    assert resp.status_code == 200

    resp = await client.get(
        f"/api/v1/fees/receipt/{other_receipt.receipt_number}", headers=auth_headers(parent_token)
    )
    assert resp.status_code == 403


# ── File download ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_file_download_owner_and_staff_only(
    client: AsyncClient, admin_user: User, student_user: User, parent_user: User
):
    """Non-staff may download only their own uploads; staff may download any school file."""
    parent_token = await get_auth_token(client, "test_parent", "Parent@123")
    up = await client.post(
        "/api/v1/files/upload",
        headers=auth_headers(parent_token),
        files={"file": ("note.pdf", b"%PDF-1.0\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[]/Count 0>>endobj\nxref\n0 3\ntrailer<</Root 1 0 R>>\n%%EOF", "application/pdf")},
        data={"category": "document"},
    )
    assert up.status_code == 201, up.text
    file_id = up.json()["data"]["id"]

    # Uploader (parent) can download their own file.
    own = await client.get(f"/api/v1/files/{file_id}", headers=auth_headers(parent_token))
    assert own.status_code == 200

    # A different non-staff user (student) cannot.
    student_token = await get_auth_token(client, "test_student", "Student@123")
    other = await client.get(f"/api/v1/files/{file_id}", headers=auth_headers(student_token))
    assert other.status_code == 403

    # Staff (admin) can download any file in the school.
    admin_token = await get_auth_token(client, "test_admin", "Admin@123")
    staff = await client.get(f"/api/v1/files/{file_id}", headers=auth_headers(admin_token))
    assert staff.status_code == 200


# ── School-ops rosters (transport / residential) ────────────────────────────────

@pytest.mark.asyncio
async def test_ops_rosters_are_staff_only(
    client: AsyncClient, admin_user: User, student_user: User, parent_user: User
):
    """Transport routes/riders and residential blocks/residents expose driver/warden
    contacts and child rosters — readable by admin/operations only."""
    admin_token = await get_auth_token(client, "test_admin", "Admin@123")

    route = await client.post(
        "/api/v1/ops/transport/routes",
        headers=auth_headers(admin_token),
        json={"route_name": "Route 1", "driver_name": "Driver", "driver_contact": "+919000000001"},
    )
    assert route.status_code == 201, route.text
    route_id = route.json()["data"]["id"]

    block = await client.post(
        "/api/v1/ops/residential/blocks",
        headers=auth_headers(admin_token),
        json={"block_name": "Block A", "warden_name": "Warden", "warden_contact": "+919000000002"},
    )
    assert block.status_code == 201, block.text
    block_id = block.json()["data"]["id"]

    protected = [
        "/api/v1/ops/transport/routes",
        f"/api/v1/ops/transport/routes/{route_id}/students",
        "/api/v1/ops/residential/blocks",
        f"/api/v1/ops/residential/blocks/{block_id}/residents",
    ]

    for username, password in (("test_student", "Student@123"), ("test_parent", "Parent@123")):
        token = await get_auth_token(client, username, password)
        for path in protected:
            resp = await client.get(path, headers=auth_headers(token))
            assert resp.status_code == 403, f"{username} should be denied {path}"

    for path in protected:
        resp = await client.get(path, headers=auth_headers(admin_token))
        assert resp.status_code == 200, f"admin should read {path}"


# ── Timetable ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_teacher_timetable_staff_only(
    client: AsyncClient, teacher_user: User, student_user: User, test_class: Class
):
    """Students must not enumerate where staff are during the day; class timetable stays open."""
    student_token = await get_auth_token(client, "test_student", "Student@123")
    resp = await client.get(
        f"/api/v1/timetable/teacher/{teacher_user.id}", headers=auth_headers(student_token)
    )
    assert resp.status_code == 403

    teacher_token = await get_auth_token(client, "test_teacher", "Teacher@123")
    resp = await client.get(
        f"/api/v1/timetable/teacher/{teacher_user.id}", headers=auth_headers(teacher_token)
    )
    assert resp.status_code == 200

    resp = await client.get(
        f"/api/v1/timetable/class/{test_class.id}", headers=auth_headers(student_token)
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_teacher_roster_access_is_class_scoped(
    client: AsyncClient,
    admin_user: User,
    teacher_user: User,
    student_user: User,
    test_class: Class,
    db_session: AsyncSession,
):
    """Roster access is scope-gated: an unassigned teacher cannot enumerate the whole
    school, but an incharge can list their own class; admins still see everything."""
    teacher_token = await get_auth_token(client, "test_teacher", "Teacher@123")

    # Teacher with no managed class and no class filter → must scope to a class first.
    resp = await client.get("/api/v1/academic/students", headers=auth_headers(teacher_token))
    assert resp.status_code == 403

    # Make the teacher the incharge of test_class → may list that class's students.
    test_class.class_incharge_id = teacher_user.id
    await db_session.flush()
    resp = await client.get(
        f"/api/v1/academic/students?class_id={test_class.id}",
        headers=auth_headers(teacher_token),
    )
    assert resp.status_code == 200

    # Admin still sees the full roster with no class filter.
    admin_token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.get("/api/v1/academic/students", headers=auth_headers(admin_token))
    assert resp.status_code == 200
