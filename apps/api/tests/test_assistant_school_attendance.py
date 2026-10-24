"""School-wide attendance capability (admin).

Proves the new `school_attendance` tool:
  - an authorized admin gets an accurate whole-school aggregate for today, scored by the
    active school's policy, from the authoritative Attendance rows — no student-level rows;
  - empty attendance is reported honestly;
  - class-scoped roles (teacher/incharge) and portal roles (parent/student) are denied;
  - tenant/school scope holds (another school's marks never appear);
  - the capability registry still validates;
  - deterministic dispatch routes to the capability (stubbed planner);
  - real-Gemma routing selects it for a whole-school attendance question (skipped if the
    configured LLM provider is unreachable — reported separately from stubbed dispatch).
"""

from datetime import date

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.academic import AcademicYear, Class
from app.db.models.attendance import Attendance, AttendanceStatus
from app.db.models.school import School
from app.db.models.student import Student
from app.db.models.user import User, UserRole
from app.modules.workspace.assistant import capabilities as cap
from app.modules.workspace.assistant.planner import PlannerDecision, TemporalIntent


class _U:
    def __init__(self, user_id, school_id, role):
        self.id = str(user_id)
        self.school_id = str(school_id)
        self.role = role
        self.full_name = "Admin"
        self.tenant_slug = None


@pytest_asyncio.fixture
async def school_attendance_fx(db_session: AsyncSession, test_school: School):
    """Two classes with marked attendance today (admin can read the whole school)."""
    ay = AcademicYear(
        school_id=test_school.id, year_label="2026-2027",
        start_date=date(2026, 6, 1), end_date=date(2027, 5, 31), is_active=True,
    )
    db_session.add(ay)
    await db_session.flush()

    def mk_user(uname, role, name):
        u = User(
            school_id=test_school.id, username=uname,
            mobile=f"+9197{abs(hash(uname)) % 100000000:08d}",
            full_name=name, role=role, password_hash="x", is_active=True,
        )
        db_session.add(u)
        return u

    admin = mk_user("sa_admin", UserRole.ADMIN, "Admin")
    teacher = mk_user("sa_teacher", UserRole.TEACHER, "Teacher")
    await db_session.flush()

    c1 = Class(school_id=test_school.id, grade="Class 5", section="A", academic_year_id=ay.id)
    c2 = Class(school_id=test_school.id, grade="Class 6", section="B", academic_year_id=ay.id)
    db_session.add_all([c1, c2])
    await db_session.flush()

    students = []
    statuses = [
        (c1, AttendanceStatus.PRESENT), (c1, AttendanceStatus.ABSENT),
        (c2, AttendanceStatus.PRESENT), (c2, AttendanceStatus.LATE),
    ]
    for i, (cls, status) in enumerate(statuses):
        su = mk_user(f"sa_stu{i}", UserRole.STUDENT, f"Stu {i}")
        await db_session.flush()
        stu = Student(school_id=test_school.id, user_id=su.id, class_id=cls.id,
                      admission_no=f"SATT{i:03d}", roll_no=str(i + 1))
        db_session.add(stu)
        await db_session.flush()
        students.append(stu)
        db_session.add(Attendance(
            school_id=test_school.id, student_id=stu.id, class_id=cls.id,
            date=date.today(), status=status, marked_by=admin.id,
        ))
    await db_session.flush()

    return {"admin": admin, "teacher": teacher, "c1": c1}


@pytest.mark.asyncio
async def test_admin_school_attendance_today(
    test_school: School, school_attendance_fx, db_session: AsyncSession
):
    user = _U(school_attendance_fx["admin"].id, test_school.id, "admin")
    block = await cap.school_attendance(db_session, user, {})
    assert block["kind"] == "metrics"
    assert "today" in block["title"].lower()
    labels = {m["label"]: m.get("value") for m in block["metrics"]}
    assert labels["Present"] == 2
    assert labels["Absent"] == 1
    assert labels["Late"] == 1
    assert labels["Marks recorded"] == 4
    # No student-level rows leak into the aggregate.
    assert "rows" not in block
    # A real percentage is present (not fabricated / not the overview counts).
    assert any(m.get("format") == "percent" for m in block["metrics"])


@pytest.mark.asyncio
async def test_school_attendance_empty_is_honest(
    test_school: School, db_session: AsyncSession
):
    """No attendance marked anywhere -> honest empty, not a fabricated 0% among real data."""
    admin = User(
        school_id=test_school.id, username="empty_admin", mobile="+919700000001",
        full_name="Admin", role=UserRole.ADMIN, password_hash="x", is_active=True,
    )
    db_session.add(admin)
    await db_session.flush()
    user = _U(admin.id, test_school.id, "admin")
    block = await cap.school_attendance(db_session, user, {})
    assert block["kind"] == "metrics"
    assert block["metrics"] == []
    assert "no attendance" in block["message"].lower()


@pytest.mark.asyncio
async def test_school_attendance_denied_for_teacher(
    test_school: School, school_attendance_fx, db_session: AsyncSession
):
    user = _U(school_attendance_fx["teacher"].id, test_school.id, "teacher")
    block = await cap.school_attendance(db_session, user, {})
    assert block["kind"] == "not_found"
    assert block["title"] == "Not available"  # class-scoped role cannot read the whole school
    assert "Present" not in str(block)  # no aggregate leaked


@pytest.mark.asyncio
async def test_school_attendance_denied_for_parent_and_student(
    test_school: School, school_attendance_fx, db_session: AsyncSession
):
    for role in ("parent", "student"):
        user = _U(school_attendance_fx["admin"].id, test_school.id, role)
        block = await cap.school_attendance(db_session, user, {})
        assert block["kind"] == "not_found"
        assert block["title"] == "Not available"


@pytest.mark.asyncio
async def test_school_attendance_tenant_scoped(
    test_school: School, school_attendance_fx, db_session: AsyncSession
):
    """An admin presented against a DIFFERENT school sees none of this school's marks."""
    other = School(name="Other", code="OTH2", tenant_slug="other2")
    db_session.add(other)
    await db_session.flush()
    user = _U(school_attendance_fx["admin"].id, other.id, "admin")
    block = await cap.school_attendance(db_session, user, {})
    assert block["kind"] == "metrics"
    assert block["metrics"] == []  # no cross-tenant attendance


def test_registries_still_valid():
    from app.modules.workspace.assistant.contracts import validate_registries

    validate_registries()


def test_school_attendance_admin_only_catalog():
    from app.modules.workspace.assistant.tools import tools_for_role

    assert any(t.name == "school_attendance" for t in tools_for_role("admin"))
    assert any(t.name == "school_attendance" for t in tools_for_role("super_admin"))
    for role in ("teacher", "class_incharge", "operations", "parent", "student"):
        assert not any(t.name == "school_attendance" for t in tools_for_role(role))
    # class_attendance_today is unchanged (still staff-visible).
    assert any(t.name == "class_attendance_today" for t in tools_for_role("teacher"))


# ── Dispatch (stubbed planner — proves wiring, NOT real-Gemma routing) ──────────


@pytest.mark.asyncio
async def test_full_turn_school_attendance_dispatch(
    test_school: School, school_attendance_fx, db_session: AsyncSession, monkeypatch
):
    from app.modules.workspace.assistant import service as service_mod

    async def _fake_plan(text, *, tools, history=None, prev_state=None):
        return PlannerDecision(action="tool", tool="school_attendance",
                               params={}, temporal=TemporalIntent())

    monkeypatch.setattr(service_mod, "plan", _fake_plan)
    svc = service_mod.AssistantService(db_session)
    user = _U(school_attendance_fx["admin"].id, test_school.id, "admin")
    r = await svc.handle_turn(
        current_user=user, text="show today's school attendance", session_id=None
    )
    assert r["block"]["kind"] == "metrics"
    assert r["trace"]["capability"] == "school_attendance"


# ── Real-Gemma routing (skipped if the configured provider is unreachable) ──────


@pytest.mark.asyncio
async def test_real_gemma_routes_school_attendance():
    """Live routing: a whole-school attendance question selects school_attendance over
    class_attendance_today / school_overview. Skipped (not failed) if the provider is down."""
    from app.modules.workspace.assistant.planner import plan
    from app.modules.workspace.assistant.tools import tools_for_role

    tools = tools_for_role("admin")
    try:
        decision = await plan("show today's school attendance", tools=tools)
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"LLM provider unavailable: {exc}")
    if decision.action != "tool" or decision.tool is None:
        pytest.skip(f"planner did not return a tool (action={decision.action})")
    assert decision.tool == "school_attendance", (
        f"real Gemma chose {decision.tool!r}, expected school_attendance"
    )
