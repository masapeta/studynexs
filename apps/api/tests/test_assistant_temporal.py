"""Temporal semantics — prove date ranges reach the authoritative data queries.

Seeds fee receipts and attendance across two months, then asserts the range-scoped
services return ONLY the in-range slice. This is the spec's mandatory proof that
"fee collected today / this month" filters the underlying query, not just the plan.
"""

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.attendance import Attendance, AttendanceStatus
from app.db.models.fee import FeeReceipt, PaymentMode
from app.db.models.school import School
from app.db.models.student import Student
from app.db.models.user import User
from app.modules.attendance.services.attendance_service import AttendanceService
from app.modules.fees.services.fee_service import FeeService
from app.modules.workspace.assistant.temporal import resolve_time_range


async def _student(db: AsyncSession, student_user: User) -> Student:
    from sqlalchemy import select

    return (
        await db.execute(select(Student).where(Student.user_id == student_user.id))
    ).scalar_one()


@pytest.mark.asyncio
async def test_fee_collection_range_filters_by_month(
    admin_user: User, student_user: User, test_school: School, db_session: AsyncSession
):
    student = await _student(db_session, student_user)
    # August receipt ₹10,000; September receipt ₹5,000 (tz-aware UTC).
    db_session.add_all(
        [
            FeeReceipt(
                school_id=test_school.id,
                student_id=student.id,
                receipt_number="TST-AUG",
                receipt_sequence=1,
                student_name="Test Student",
                class_name="Grade 1-A",
                amount_paid=Decimal("10000.00"),
                payment_mode=PaymentMode.CASH,
                fee_type="Tuition",
                school_name="Test School",
                paid_at=datetime(2026, 8, 15, 6, 0, tzinfo=timezone.utc),
            ),
            FeeReceipt(
                school_id=test_school.id,
                student_id=student.id,
                receipt_number="TST-SEP",
                receipt_sequence=2,
                student_name="Test Student",
                class_name="Grade 1-A",
                amount_paid=Decimal("5000.00"),
                payment_mode=PaymentMode.CASH,
                fee_type="Tuition",
                school_name="Test School",
                paid_at=datetime(2026, 9, 10, 6, 0, tzinfo=timezone.utc),
            ),
        ]
    )
    await db_session.flush()

    svc = FeeService(db_session)
    # Explicit August range (inclusive to) -> only the ₹10,000 receipt.
    aug = await resolve_time_range(
        db_session, test_school, test_school.id, {"from": "2026-08-01", "to": "2026-08-31"}
    )
    res_aug = await svc.collection_in_range(test_school.id, start=aug.start, end=aug.end)
    assert res_aug["collected"] == 10000.0
    assert res_aug["receipt_count"] == 1

    # September range -> only the ₹5,000 receipt.
    sep = await resolve_time_range(
        db_session, test_school, test_school.id, {"from": "2026-09-01", "to": "2026-09-30"}
    )
    res_sep = await svc.collection_in_range(test_school.id, start=sep.start, end=sep.end)
    assert res_sep["collected"] == 5000.0
    assert res_sep["receipt_count"] == 1

    # All-time -> both.
    allt = await resolve_time_range(db_session, test_school, test_school.id, "all_time")
    res_all = await svc.collection_in_range(test_school.id, start=allt.start, end=allt.end)
    assert res_all["collected"] == 15000.0


@pytest.mark.asyncio
async def test_student_attendance_range_filters_by_month(
    admin_user: User, student_user: User, test_school: School, db_session: AsyncSession
):
    student = await _student(db_session, student_user)
    # August: 1 present. September: present, absent, present.
    db_session.add_all(
        [
            Attendance(
                school_id=test_school.id, student_id=student.id, class_id=student.class_id,
                date=date(2026, 8, 20), status=AttendanceStatus.PRESENT, marked_by=admin_user.id,
            ),
            Attendance(
                school_id=test_school.id, student_id=student.id, class_id=student.class_id,
                date=date(2026, 9, 1), status=AttendanceStatus.PRESENT, marked_by=admin_user.id,
            ),
            Attendance(
                school_id=test_school.id, student_id=student.id, class_id=student.class_id,
                date=date(2026, 9, 2), status=AttendanceStatus.ABSENT, marked_by=admin_user.id,
            ),
            Attendance(
                school_id=test_school.id, student_id=student.id, class_id=student.class_id,
                date=date(2026, 9, 3), status=AttendanceStatus.PRESENT, marked_by=admin_user.id,
            ),
        ]
    )
    await db_session.flush()

    svc = AttendanceService(db_session)
    sep = await resolve_time_range(
        db_session, test_school, test_school.id, {"from": "2026-09-01", "to": "2026-09-30"}
    )
    res_sep = await svc.student_summary_in_range(
        test_school.id, student.id, start=sep.start_date, end=sep.end_date
    )
    # September only: 2 present of 3 recorded -> 66.7%, August's present excluded.
    assert res_sep["total"] == 3
    assert res_sep["present"] == 2
    assert res_sep["absent"] == 1
    assert res_sep["percentage"] == 66.7

    allt = await resolve_time_range(db_session, test_school, test_school.id, "all_time")
    res_all = await svc.student_summary_in_range(
        test_school.id, student.id, start=allt.start_date, end=allt.end_date
    )
    assert res_all["total"] == 4
    assert res_all["present"] == 3


@pytest.mark.asyncio
async def test_named_month_resolves_without_llm_year_guess(
    test_school: School, db_session: AsyncSession
):
    # Bare month name -> deterministic year (most recent occurrence on/before today).
    from datetime import date as _date

    rng = await resolve_time_range(db_session, test_school, test_school.id, {"month": "august"})
    today = _date.today()
    expected_year = today.year if 8 <= today.month else today.year - 1
    assert rng.start_date == _date(expected_year, 8, 1)
    assert rng.end_date == _date(expected_year, 9, 1)
    assert str(expected_year) in rng.label

    # Explicit year override is honoured.
    rng2 = await resolve_time_range(
        db_session, test_school, test_school.id, {"month": "december", "year": 2025}
    )
    assert rng2.start_date == _date(2025, 12, 1)
    assert rng2.end_date == _date(2026, 1, 1)


@pytest.mark.asyncio
async def test_academic_year_range_uses_school_boundaries(
    test_school: School, academic_year, db_session: AsyncSession
):
    rng = await resolve_time_range(
        db_session, test_school, test_school.id, "current_academic_year"
    )
    assert rng.start is not None and rng.end is not None
    # academic_year fixture: 2026-06-01 .. 2027-05-31 (end inclusive -> exclusive next day).
    assert rng.start_date == date(2026, 6, 1)
    assert rng.end_date == date(2027, 6, 1)
