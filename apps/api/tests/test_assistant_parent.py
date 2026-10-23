"""Parent conversational capabilities (Milestone 1).

A parent asks about THEIR OWN linked children in the existing chat. These tests prove:
  - the four parent tools return grounded, structured blocks for an authorized child;
  - child selection stays strictly within the parent's own linked set (multi-child clarify,
    named selection, and a foreign/unknown name -> non-leaky not_found);
  - a parent can NEVER reach another family's child, even school-wide, and cross-tenant
    requests are non-disclosing;
  - staff tools are invisible to parents and parent tools invisible to staff;
  - the full handle_turn path (planner -> parent tool -> portal service -> block) works.

Fixtures seed two families in one school plus a second school, with real attendance,
mastery, and fee rows so authorized reads return actual data (not fabricated values).
"""

from datetime import date
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.academic import AcademicYear, Class, Subject
from app.db.models.attendance import Attendance, AttendanceStatus
from app.db.models.fee import (
    FeeFrequency,
    FeeStatus,
    FeeStructure,
    FeeType,
    StudentFeeRecord,
)
from app.db.models.mastery import MasteryTrend, StudentTopicMastery
from app.db.models.school import School
from app.db.models.student import Parent, Relationship, Student, StudentParentMap
from app.db.models.user import User, UserRole
from app.modules.workspace.assistant import capabilities as cap
from app.modules.workspace.assistant.planner import PlannerDecision, TemporalIntent


class _U:
    """CurrentUser stand-in (id/school_id/role/full_name/tenant_slug)."""

    def __init__(self, user_id, school_id, role):
        self.id = str(user_id)
        self.school_id = str(school_id)
        self.role = role
        self.full_name = "Parent"
        self.tenant_slug = None


@pytest_asyncio.fixture
async def parent_families(db_session: AsyncSession, test_school: School):
    """Two families in one school: parent_one -> child_one; parent_two -> child_two.

    child_one has attendance, a weak topic, and a pending fee so authorized reads return
    real data. Returns the users + student ids needed by the tests.
    """
    ay = AcademicYear(
        school_id=test_school.id, year_label="2026-2027",
        start_date=date(2026, 6, 1), end_date=date(2027, 5, 31), is_active=True,
    )
    db_session.add(ay)
    await db_session.flush()

    cls = Class(school_id=test_school.id, grade="Class 5", section="A",
                academic_year_id=ay.id)
    db_session.add(cls)
    await db_session.flush()

    subject = Subject(school_id=test_school.id, name="Mathematics", class_id=cls.id)
    db_session.add(subject)
    await db_session.flush()

    def mk_user(uname, role, name):
        u = User(
            school_id=test_school.id, username=uname,
            mobile=f"+9198{abs(hash(uname)) % 100000000:08d}",
            full_name=name, role=role, password_hash="x", is_active=True,
        )
        db_session.add(u)
        return u

    child_one_user = mk_user("child_one", UserRole.STUDENT, "Aarav Sharma")
    child_two_user = mk_user("child_two", UserRole.STUDENT, "Diya Rao")
    parent_one_user = mk_user("parent_one", UserRole.PARENT, "Parent One")
    parent_two_user = mk_user("parent_two", UserRole.PARENT, "Parent Two")
    await db_session.flush()

    child_one = Student(school_id=test_school.id, user_id=child_one_user.id,
                        class_id=cls.id, admission_no="FAM001", roll_no="1")
    child_two = Student(school_id=test_school.id, user_id=child_two_user.id,
                        class_id=cls.id, admission_no="FAM002", roll_no="2")
    db_session.add_all([child_one, child_two])
    await db_session.flush()

    parent_one = Parent(school_id=test_school.id, user_id=parent_one_user.id)
    parent_two = Parent(school_id=test_school.id, user_id=parent_two_user.id)
    db_session.add_all([parent_one, parent_two])
    await db_session.flush()

    db_session.add_all([
        StudentParentMap(school_id=test_school.id, student_id=child_one.id,
                         parent_id=parent_one.id, is_primary=True,
                         relationship_type=Relationship.FATHER),
        StudentParentMap(school_id=test_school.id, student_id=child_two.id,
                         parent_id=parent_two.id, is_primary=True,
                         relationship_type=Relationship.FATHER),
    ])

    # Real data for child_one so authorized reads are grounded.
    db_session.add(Attendance(
        school_id=test_school.id, student_id=child_one.id, class_id=cls.id,
        date=date(2026, 9, 1), status=AttendanceStatus.PRESENT, marked_by=parent_one_user.id,
    ))
    db_session.add(StudentTopicMastery(
        school_id=test_school.id, student_id=child_one.id, class_id=cls.id,
        subject_id=subject.id, academic_year_id=ay.id, topic="fractions",
        topic_display="Fractions", mastery_pct=Decimal("42.00"),
        assessments_count=2, trend=MasteryTrend.INSUFFICIENT,
    ))
    structure = FeeStructure(
        school_id=test_school.id, class_id=cls.id, fee_type=FeeType.TUITION,
        amount=Decimal("5000.00"), frequency=FeeFrequency.ANNUAL, academic_year_id=ay.id,
    )
    db_session.add(structure)
    await db_session.flush()
    db_session.add(StudentFeeRecord(
        school_id=test_school.id, student_id=child_one.id, fee_structure_id=structure.id,
        amount=Decimal("5000.00"), due_date=date(2026, 9, 30), status=FeeStatus.PENDING,
        paid_amount=Decimal("0.00"),
    ))
    await db_session.flush()

    return {
        "parent_one": parent_one_user,
        "parent_two": parent_two_user,
        "child_one_id": child_one.id,
        "child_two_id": child_two.id,
    }


@pytest_asyncio.fixture
async def multi_child_parent(db_session: AsyncSession, test_school: School, parent_families):
    """Link a SECOND child to parent_one so ambiguity/clarify can be exercised."""
    ay = (
        await db_session.execute(
            select(AcademicYear).where(AcademicYear.school_id == test_school.id)
        )
    ).scalars().first()
    cls = Class(school_id=test_school.id, grade="Class 8", section="B",
                academic_year_id=ay.id)
    db_session.add(cls)
    await db_session.flush()
    sib_user = User(
        school_id=test_school.id, username="child_one_sib",
        mobile="+919800000099", full_name="Kabir Sharma", role=UserRole.STUDENT,
        password_hash="x", is_active=True,
    )
    db_session.add(sib_user)
    await db_session.flush()
    sib = Student(school_id=test_school.id, user_id=sib_user.id, class_id=cls.id,
                  admission_no="FAM003", roll_no="3")
    db_session.add(sib)
    await db_session.flush()
    parent_one = (
        await db_session.execute(
            select(Parent).where(Parent.user_id == parent_families["parent_one"].id)
        )
    ).scalar_one()
    db_session.add(StudentParentMap(
        school_id=test_school.id, student_id=sib.id, parent_id=parent_one.id,
        is_primary=False, relationship_type=Relationship.FATHER,
    ))
    await db_session.flush()
    return {"sibling_id": sib.id}


# ── Direct capability tests (authorization is enforced inside the handler) ──────


@pytest.mark.asyncio
async def test_parent_child_attendance_own_child(
    test_school: School, parent_families, db_session: AsyncSession
):
    user = _U(parent_families["parent_one"].id, test_school.id, "parent")
    block = await cap.my_child_attendance(db_session, user, {})
    assert block["kind"] == "metrics"
    assert "Aarav" in block["title"]
    # Grounded: a real attendance percentage is present (not fabricated).
    assert any(m.get("format") == "percent" for m in block["metrics"])


@pytest.mark.asyncio
async def test_parent_child_progress_weak_topics(
    test_school: School, parent_families, db_session: AsyncSession
):
    user = _U(parent_families["parent_one"].id, test_school.id, "parent")
    block = await cap.my_child_progress(db_session, user, {})
    assert block["kind"] == "table"
    topics = " ".join(r.get("topic_display", "") for r in block["rows"])
    assert "Fractions" in topics


@pytest.mark.asyncio
async def test_parent_child_fees(
    test_school: School, parent_families, db_session: AsyncSession
):
    user = _U(parent_families["parent_one"].id, test_school.id, "parent")
    block = await cap.my_child_fees(db_session, user, {})
    assert block["kind"] == "table"
    assert any(r.get("status") == "pending" for r in block["rows"])


@pytest.mark.asyncio
async def test_parent_children_overview(
    test_school: School, parent_families, db_session: AsyncSession
):
    user = _U(parent_families["parent_one"].id, test_school.id, "parent")
    block = await cap.my_children_overview(db_session, user, {})
    assert block["kind"] == "table"
    names = " ".join(r.get("name", "") for r in block["rows"])
    assert "Aarav" in names
    assert "Diya" not in names  # never another family's child


@pytest.mark.asyncio
async def test_parent_multi_child_clarifies(
    test_school: School, parent_families, multi_child_parent, db_session: AsyncSession
):
    user = _U(parent_families["parent_one"].id, test_school.id, "parent")
    block = await cap.my_child_attendance(db_session, user, {})
    assert block["kind"] == "clarify"
    labels = " ".join(o["label"] for o in block["options"])
    assert "Aarav" in labels and "Kabir" in labels
    assert "Diya" not in labels  # only this parent's children are offered


@pytest.mark.asyncio
async def test_parent_multi_child_named_selection(
    test_school: School, parent_families, multi_child_parent, db_session: AsyncSession
):
    user = _U(parent_families["parent_one"].id, test_school.id, "parent")
    block = await cap.my_child_attendance(db_session, user, {"child": "Aarav"})
    assert block["kind"] == "metrics"
    assert "Aarav" in block["title"]


@pytest.mark.asyncio
async def test_parent_cannot_reach_other_family_by_name(
    test_school: School, parent_families, db_session: AsyncSession
):
    """parent_one names the OTHER family's child -> non-leaky not_found, never their data."""
    user = _U(parent_families["parent_one"].id, test_school.id, "parent")
    block = await cap.my_child_attendance(db_session, user, {"child": "Diya"})
    assert block["kind"] == "not_found"
    assert "Diya" not in str(block)  # does not confirm the other child exists


@pytest.mark.asyncio
async def test_parent_foreign_student_id_in_params_is_ignored(
    test_school: School, parent_families, db_session: AsyncSession
):
    """A spoofed student_id in params must have no effect — the tools take no such param."""
    user = _U(parent_families["parent_one"].id, test_school.id, "parent")
    block = await cap.my_child_attendance(
        db_session, user, {"student_id": str(parent_families["child_two_id"]), "child": ""}
    )
    # With one linked child it resolves to the OWN child; the foreign id is never consulted.
    assert block["kind"] == "metrics"
    assert "Aarav" in block["title"]
    assert "Diya" not in str(block)


@pytest.mark.asyncio
async def test_parent_no_children_honest_response(
    test_school: School, parent_families, db_session: AsyncSession
):
    user = _U(parent_families["parent_two"].id, test_school.id, "parent")
    # parent_two's only child is child_two; overview shows that child, not child_one.
    block = await cap.my_children_overview(db_session, user, {})
    names = " ".join(r.get("name", "") for r in block["rows"])
    assert "Diya" in names and "Aarav" not in names


@pytest.mark.asyncio
async def test_cross_tenant_parent_sees_no_children(
    test_school: School, parent_families, db_session: AsyncSession
):
    """A parent id presented against a DIFFERENT school resolves to zero children (non-leaky)."""
    other = School(name="Other School", code="OTHER", tenant_slug="other-school")
    db_session.add(other)
    await db_session.flush()
    user = _U(parent_families["parent_one"].id, other.id, "parent")
    block = await cap.my_children_overview(db_session, user, {})
    assert block["kind"] == "table"
    assert block["rows"] == []  # tenant isolation: no children in the other school


# ── Role visibility ────────────────────────────────────────────────────────────


def test_parent_tools_scoped_to_parent_role():
    from app.modules.workspace.assistant.tools import tools_for_role

    parent_names = {t.name for t in tools_for_role("parent")}
    assert parent_names == {
        "my_children_overview",
        "my_child_attendance",
        "my_child_progress",
        "my_child_fees",
    }
    # Staff tools are invisible to parents.
    assert "students_fee_pending_over" not in parent_names
    assert "class_results" not in parent_names
    # Parent tools are invisible to staff.
    for role in ("teacher", "class_incharge", "admin", "super_admin"):
        staff_names = {t.name for t in tools_for_role(role)}
        assert not (staff_names & parent_names)


def test_registries_still_valid():
    from app.modules.workspace.assistant.contracts import validate_registries

    validate_registries()  # raises on any structural drift


# ── Full assistant turn (planner -> parent tool -> portal service -> block) ─────


@pytest.mark.asyncio
async def test_full_turn_parent_overview(
    test_school: School, parent_families, db_session: AsyncSession, monkeypatch
):
    from app.modules.workspace.assistant import service as service_mod

    async def _fake_plan(text, *, tools, history=None, prev_state=None):
        return PlannerDecision(action="tool", tool="my_children_overview",
                               params={}, temporal=TemporalIntent())

    monkeypatch.setattr(service_mod, "plan", _fake_plan)
    svc = service_mod.AssistantService(db_session)
    user = _U(parent_families["parent_one"].id, test_school.id, "parent")
    r = await svc.handle_turn(
        current_user=user, text="how are my children doing?", session_id=None
    )
    assert r["block"]["kind"] == "table"
    assert r["trace"]["capability"] == "my_children_overview"
    names = " ".join(row.get("name", "") for row in r["block"]["rows"])
    assert "Aarav" in names and "Diya" not in names


@pytest.mark.asyncio
async def test_full_turn_parent_cannot_invoke_staff_tool(
    test_school: School, parent_families, db_session: AsyncSession, monkeypatch
):
    """Even if the planner names a staff tool, a parent session gets a guide, never staff data."""
    from app.modules.workspace.assistant import service as service_mod

    async def _fake_plan(text, *, tools, history=None, prev_state=None):
        return PlannerDecision(action="tool", tool="students_fee_pending_over",
                               params={"min_percent": 50}, temporal=TemporalIntent())

    monkeypatch.setattr(service_mod, "plan", _fake_plan)
    svc = service_mod.AssistantService(db_session)
    user = _U(parent_families["parent_one"].id, test_school.id, "parent")
    r = await svc.handle_turn(
        current_user=user, text="list fee defaulters over 50%", session_id=None
    )
    assert r["block"]["kind"] == "guide"  # tool.allowed_for(parent) is False -> guide
