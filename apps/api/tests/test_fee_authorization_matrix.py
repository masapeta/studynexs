"""Role matrix for the fee module (audit P0-SEC-001).

GET /fees/recent listed "teacher" in require_roles, so any subject teacher could read every
family's payment history (verified live: 50 receipts, 49 households, Rs.125,000). /stats and
/roster correctly omit teacher, so it was a copy-paste slip rather than a decision.

Two rules these tests encode, both learned from the audit:

1. A 200 with an empty list is NOT an authorization pass. The original sweep missed this bug
   partly because it probed a tenant holding no fee rows. Every allow-case here therefore
   asserts on real seeded data, and the leak case asserts a family name is actually returned.
2. Enumerate EVERY role, not one representative per tier. `class_incharge` was correctly
   denied while plain `teacher` leaked — testing one "teaching role" would have missed it.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db.models.academic import AcademicYear, Class
from app.db.models.fee import (
    FeeFrequency,
    FeeReceipt,
    FeeStatus,
    FeeStructure,
    FeeType,
    PaymentMode,
    StudentFeeRecord,
)
from app.db.models.school import School
from app.db.models.student import Student
from app.db.models.user import User, UserRole
from tests.conftest import access_token_for, auth_headers

# Roles that may read school-wide finance aggregates.
FINANCE_ROLES = {UserRole.ADMIN, UserRole.SUPER_ADMIN}
# Every other role must be refused on those aggregates.
NON_FINANCE_ROLES = [
    UserRole.TEACHER,
    UserRole.CLASS_INCHARGE,
    UserRole.STUDENT,
    UserRole.PARENT,
    UserRole.OPERATIONS,
]
AGGREGATE_ENDPOINTS = [
    "/api/v1/fees/recent?limit=50",
    "/api/v1/fees/roster",
    "/api/v1/fees/stats",
]

_PAID = "2500.00"
_FAMILY = "Leaky Family Child"


@pytest_asyncio.fixture
async def user_by_role(db_session: AsyncSession, test_school: School):
    """Build one active user per role, so the matrix can cover the whole enum."""
    made: dict[UserRole, User] = {}
    for i, role in enumerate(UserRole):
        u = User(
            school_id=test_school.id,
            username=f"matrix_{role.value}",
            mobile=f"+9198000{i:05d}",
            full_name=f"Matrix {role.value}",
            role=role,
            password_hash=hash_password("Matrix@123"),
            is_active=True,
        )
        db_session.add(u)
        made[role] = u
    await db_session.flush()
    return made


@pytest_asyncio.fixture
async def seeded_payment(
    db_session: AsyncSession,
    test_school: School,
    test_class: Class,
    academic_year: AcademicYear,
) -> FeeReceipt:
    """A real paid fee + receipt.

    Without this the endpoint returns 200 with [], and an authorization bug is invisible.
    """
    student_user = User(
        school_id=test_school.id,
        username="leaky_family_student",
        mobile="+919800099999",
        full_name=_FAMILY,
        role=UserRole.STUDENT,
        password_hash=hash_password("Student@123"),
        is_active=True,
    )
    db_session.add(student_user)
    await db_session.flush()

    student = Student(
        school_id=test_school.id,
        user_id=student_user.id,
        class_id=test_class.id,
        admission_no="LEAK-001",
        roll_no="1",
    )
    db_session.add(student)

    structure = FeeStructure(
        school_id=test_school.id,
        class_id=test_class.id,
        fee_type=FeeType.TUITION,
        amount=_PAID,
        frequency=FeeFrequency.MONTHLY,
        academic_year_id=academic_year.id,
    )
    db_session.add(structure)
    await db_session.flush()

    receipt = FeeReceipt(
        school_id=test_school.id,
        receipt_number="LEAK-RCPT-0001",
        student_id=student.id,
        student_name=_FAMILY,
        class_name="Grade 1-A",
        amount_paid=_PAID,
        payment_mode=PaymentMode.CASH,
        fee_type="Tuition",
        paid_at=datetime.now(timezone.utc),
        school_name=test_school.name,
        receipt_sequence=1,
    )
    db_session.add(receipt)
    await db_session.flush()

    db_session.add(
        StudentFeeRecord(
            school_id=test_school.id,
            student_id=student.id,
            fee_structure_id=structure.id,
            amount=_PAID,
            paid_amount=_PAID,
            due_date=date(2026, 6, 10),
            status=FeeStatus.PAID,
            paid_at=datetime.now(timezone.utc),
            payment_mode=PaymentMode.CASH,
            receipt_id=receipt.id,
        )
    )
    await db_session.flush()
    return receipt


@pytest.mark.asyncio
async def test_seed_is_visible_to_admin_so_the_negative_cases_are_meaningful(
    client: AsyncClient, admin_user: User, seeded_payment: FeeReceipt
):
    """Guard the guard: prove the data exists before asserting others cannot see it."""
    r = await client.get(
        "/api/v1/fees/recent?limit=50", headers=auth_headers(access_token_for(admin_user))
    )
    assert r.status_code == 200, r.text
    names = [row["student_name"] for row in r.json()["data"]]
    assert _FAMILY in names, (
        "fixture did not surface a payment — the deny-cases below would be vacuous"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("role", NON_FINANCE_ROLES, ids=lambda r: r.value)
@pytest.mark.parametrize("path", AGGREGATE_ENDPOINTS, ids=lambda p: p.split("?")[0])
async def test_non_finance_roles_cannot_read_school_wide_fee_aggregates(
    client: AsyncClient,
    user_by_role: dict[UserRole, User],
    seeded_payment: FeeReceipt,
    role: UserRole,
    path: str,
):
    """No teaching/portal/ops role may read school-wide finance data."""
    r = await client.get(path, headers=auth_headers(access_token_for(user_by_role[role])))
    assert r.status_code == 403, (
        f"{role.value} got {r.status_code} on {path} — expected 403. Body: {r.text[:400]}"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("role", sorted(FINANCE_ROLES, key=lambda r: r.value),
                         ids=lambda r: r.value)
@pytest.mark.parametrize("path", AGGREGATE_ENDPOINTS, ids=lambda p: p.split("?")[0])
async def test_finance_roles_retain_access(
    client: AsyncClient,
    user_by_role: dict[UserRole, User],
    seeded_payment: FeeReceipt,
    role: UserRole,
    path: str,
):
    """The fix must not over-tighten: admin and principal keep their access."""
    r = await client.get(path, headers=auth_headers(access_token_for(user_by_role[role])))
    assert r.status_code == 200, (
        f"{role.value} lost access to {path} ({r.status_code}) — fix over-tightened"
    )


@pytest.mark.asyncio
async def test_teacher_cannot_see_any_family_payment_record(
    client: AsyncClient, user_by_role: dict[UserRole, User], seeded_payment: FeeReceipt
):
    """The exact audit reproduction, asserted on payload content, not just status."""
    token = access_token_for(user_by_role[UserRole.TEACHER])
    r = await client.get("/api/v1/fees/recent?limit=50", headers=auth_headers(token))
    assert r.status_code == 403, f"P0-SEC-001 regression: teacher got {r.status_code}"
    assert _FAMILY not in r.text
    assert _PAID not in r.text
    assert "LEAK-RCPT-0001" not in r.text


@pytest.mark.asyncio
async def test_teacher_cannot_read_an_unrelated_students_fee_record(
    client: AsyncClient,
    user_by_role: dict[UserRole, User],
    seeded_payment: FeeReceipt,
    db_session: AsyncSession,
):
    """Per-student fees stay object-authorized — the leak must not just move endpoints."""
    token = access_token_for(user_by_role[UserRole.TEACHER])
    r = await client.get(
        f"/api/v1/fees/student/{seeded_payment.student_id}", headers=auth_headers(token)
    )
    assert r.status_code in (403, 404), (
        f"teacher read an unrelated student's fees ({r.status_code}): {r.text[:300]}"
    )


@pytest.mark.asyncio
async def test_teacher_cannot_download_an_unrelated_receipt(
    client: AsyncClient, user_by_role: dict[UserRole, User], seeded_payment: FeeReceipt
):
    """Receipt-by-number must not become a side channel for the same data."""
    token = access_token_for(user_by_role[UserRole.TEACHER])
    r = await client.get(
        f"/api/v1/fees/receipt/{seeded_payment.receipt_number}", headers=auth_headers(token)
    )
    assert r.status_code in (403, 404), (
        f"teacher downloaded an unrelated receipt ({r.status_code})"
    )


def test_no_fee_endpoint_grants_a_teaching_role_school_wide_finance_access():
    """Static guard: catch the copy-paste slip class of bug on any future fee route.

    Complements the live probes above — a new endpoint added with the wrong role list fails
    here even if nobody remembers to add an HTTP test for it.
    """
    from pathlib import Path

    source = Path(__file__).resolve().parents[1] / "app/modules/fees/endpoints/fee.py"
    text = source.read_text(encoding="utf-8")
    offenders = [
        line.strip()
        for line in text.splitlines()
        if "require_roles(" in line
        and any(f'"{r}"' in line for r in ("teacher", "class_incharge", "student", "parent"))
    ]
    assert not offenders, (
        "fee endpoint grants a non-finance role via require_roles: "
        f"{offenders}. Per-student access belongs behind assert_can_access_student instead."
    )
