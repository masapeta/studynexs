"""Composable multi-capability planning (Phase 4).

Tests the PLAN (parse + bounds) and EXECUTION (join-by-canonical-id, filters, batching)
against controlled fixtures — no special-purpose combination capability exists.
"""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.attendance import Attendance, AttendanceStatus
from app.db.models.fee import FeeStructure, StudentFeeRecord
from app.db.models.school import School
from app.db.models.student import Student
from app.db.models.user import User
from app.modules.workspace.assistant.composition import (
    CompositionError,
    execute_plan,
    parse_plan,
)


class _FakeUser:
    """Minimal CurrentUser stand-in for the executor (school_id + role)."""

    def __init__(self, school_id, role="super_admin"):
        self.school_id = str(school_id)
        self.role = role
        self.id = str(school_id)


async def _noop_range(_school_id, _token):
    from app.modules.workspace.assistant.temporal import DateRange

    return DateRange(None, None, "all time")


# ── Plan parsing / bounds ─────────────────────────────────────────────────────


def test_parse_plan_requires_single_source():
    with pytest.raises(CompositionError):
        parse_plan({"operations": [{"id": "a", "capability": "enrich_fees"}]})
    with pytest.raises(CompositionError):
        parse_plan(
            {"operations": [
                {"id": "a", "capability": "classes_overview"},
                {"id": "b", "capability": "class_students", "params": {"class_label": "1A"}},
            ]}
        )


def test_parse_plan_rejects_unknown_capability_and_bad_dep():
    with pytest.raises(CompositionError):
        parse_plan({"operations": [{"id": "a", "capability": "get_everything"}]})
    with pytest.raises(CompositionError):
        parse_plan(
            {"operations": [
                {"id": "a", "capability": "classes_overview"},
                {"id": "b", "capability": "enrich_fees", "depends_on": ["missing"]},
            ]}
        )


def test_parse_plan_enforces_max_operations():
    ops = [{"id": "s", "capability": "classes_overview"}]
    ops += [{"id": f"e{i}", "capability": "filter", "depends_on": ["s"]} for i in range(10)]
    with pytest.raises(CompositionError):
        parse_plan({"operations": ops})


# ── Execution: cross-domain students (attendance + fees + filters + join) ─────


@pytest.mark.asyncio
async def test_compose_students_low_attendance_high_fees(
    admin_user: User,
    test_school: School,
    test_class,
    fee_setup: FeeStructure,
    db_session: AsyncSession,
):
    # Two students in the same class.
    from app.core.security import hash_password
    from app.db.models.student import Student as S
    from app.db.models.user import UserRole

    async def make_student(username, adm, mobile):
        u = User(
            school_id=test_school.id, username=username, mobile=mobile,
            full_name=username.title(), role=UserRole.STUDENT,
            password_hash=hash_password("Student@123"), is_active=True,
        )
        db_session.add(u)
        await db_session.flush()
        s = S(
            school_id=test_school.id, user_id=u.id, class_id=test_class.id,
            admission_no=adm, roll_no=adm[-1],
        )
        db_session.add(s)
        await db_session.flush()
        return s

    s_low = await make_student("low_high", "C001", "+919000000001")   # low att, high due
    s_ok = await make_student("high_low", "C002", "+919000000002")    # high att, low due

    # Attendance: s_low 1/4 = 25%; s_ok 4/4 = 100%.
    db_session.add_all([
        Attendance(school_id=test_school.id, student_id=s_low.id, class_id=test_class.id,
                   date=date(2026, 9, d), status=st, marked_by=admin_user.id)
        for d, st in [(1, AttendanceStatus.PRESENT), (2, AttendanceStatus.ABSENT),
                      (3, AttendanceStatus.ABSENT), (4, AttendanceStatus.ABSENT)]
    ])
    db_session.add_all([
        Attendance(school_id=test_school.id, student_id=s_ok.id, class_id=test_class.id,
                   date=date(2026, 9, d), status=AttendanceStatus.PRESENT, marked_by=admin_user.id)
        for d in (1, 2, 3, 4)
    ])
    # Fees: s_low owes 20000; s_ok owes 0.
    db_session.add(StudentFeeRecord(
        school_id=test_school.id, student_id=s_low.id, fee_structure_id=fee_setup.id,
        amount=Decimal("20000.00"), paid_amount=Decimal("0.00"), due_date=date(2026, 9, 5),
    ))
    db_session.add(StudentFeeRecord(
        school_id=test_school.id, student_id=s_ok.id, fee_structure_id=fee_setup.id,
        amount=Decimal("5000.00"), paid_amount=Decimal("5000.00"), due_date=date(2026, 9, 5),
    ))
    await db_session.flush()

    plan = parse_plan({
        "operations": [
            {"id": "s", "capability": "class_students", "params": {"class_label": "Grade 1 A"}},
            {"id": "a", "capability": "enrich_attendance", "depends_on": ["s"]},
            {"id": "f", "capability": "enrich_fees", "depends_on": ["a"]},
            {"id": "flt", "capability": "filter", "depends_on": ["f"], "filters": [
                {"field": "attendance_pct", "op": "<", "value": 75},
                {"field": "fee_due", "op": ">", "value": 10000},
            ]},
        ],
        "output": {"columns": ["admission_no", "attendance_pct", "fee_due"]},
    })
    result = await execute_plan(db_session, _FakeUser(test_school.id), plan, resolve_range=_noop_range)

    # Only s_low satisfies BOTH conditions — join by student_id, filters authoritative.
    assert len(result.rows) == 1
    row = result.rows[0]
    assert row["admission_no"] == "C001"
    assert row["attendance_pct"] == 25.0
    assert row["fee_due"] == 20000.0
    # Trace shows 4 operations with decreasing row counts (bounded, observable).
    assert [o["capability"] for o in result.trace_ops] == [
        "class_students", "enrich_attendance", "enrich_fees", "filter"
    ]


@pytest.mark.asyncio
async def test_compose_classes_overview_with_teacher_and_sort(
    admin_user: User, test_school: School, test_class, db_session: AsyncSession
):
    # classes_overview should yield the class with a student count; sort/limit applied.
    from app.core.security import hash_password
    from app.db.models.user import UserRole

    u = User(
        school_id=test_school.id, username="stud_x", mobile="+919000000003",
        full_name="Stud X", role=UserRole.STUDENT,
        password_hash=hash_password("Student@123"), is_active=True,
    )
    db_session.add(u)
    await db_session.flush()
    db_session.add(Student(
        school_id=test_school.id, user_id=u.id, class_id=test_class.id, admission_no="D001",
    ))
    await db_session.flush()

    plan = parse_plan({
        "operations": [{"id": "c", "capability": "classes_overview"}],
        "output": {
            "columns": ["class_label", "student_count", "attendance_pct", "class_teacher"],
            "sort_field": "student_count", "sort_desc": True, "limit": 5,
        },
    })
    result = await execute_plan(db_session, _FakeUser(test_school.id), plan, resolve_range=_noop_range)
    assert result.rows
    top = result.rows[0]
    assert top["class_label"] == "Grade 1 A"
    assert top["student_count"] >= 1
    assert "class_teacher" in top


@pytest.mark.asyncio
async def test_compose_class_not_found_is_honest(
    test_school: School, db_session: AsyncSession
):
    plan = parse_plan({
        "operations": [
            {"id": "s", "capability": "class_students", "params": {"class_label": "99Z"}},
        ]
    })
    with pytest.raises(CompositionError):
        await execute_plan(db_session, _FakeUser(test_school.id), plan, resolve_range=_noop_range)
