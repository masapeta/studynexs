"""Role-scoped authorization for assistant capabilities (P1.1).

The Phase 6 benchmark found a teacher could read class_results for a class outside their
scope. These tests prove server-side scope enforcement, REUSING the ERP's authoritative
rules (assert_can_access_student / StaffScope / assert_exam_class). Enforcement happens
after entity resolution — resolving a class/student never implies permission (spec §8) —
and is never delegated to the planner/LLM (spec §2, §7).

Scope model under test (derived from the ERP, not invented):
  super_admin/admin -> school-wide
  class_incharge    -> assigned class (Class.class_incharge_id)
  teacher           -> classes they teach (TeacherSubjectMapping)
  parent            -> linked children
  student           -> self
"""

from datetime import date
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.academic import AcademicYear, Class, Subject, TeacherSubjectMapping
from app.db.models.attendance import Attendance, AttendanceStatus
from app.db.models.examination import Exam, ExamMark, ExamType
from app.db.models.school import School
from app.db.models.student import Parent, Relationship, Student, StudentParentMap
from app.db.models.user import User, UserRole
from app.modules.workspace.assistant import capabilities as cap


class _U:
    """CurrentUser stand-in (id/school_id/role/full_name)."""

    def __init__(self, user_id, school_id, role):
        self.id = str(user_id)
        self.school_id = str(school_id)
        self.role = role
        self.full_name = "T"


@pytest_asyncio.fixture
async def scoped_school(db_session: AsyncSession, test_school: School):
    """Two classes, each with a different incharge; a subject teacher assigned to class A only.

    teacher_a  -> incharge of class A
    teacher_b  -> incharge of class B
    subj_a     -> subject teacher (Mathematics) in class A only
    student_a  -> in class A (with marks + attendance)
    student_b  -> in class B
    """
    ay = AcademicYear(
        school_id=test_school.id, year_label="2026-2027",
        start_date=date(2026, 6, 1), end_date=date(2027, 5, 31), is_active=True,
    )
    db_session.add(ay)
    await db_session.flush()

    def mk_user(uname, role, name):
        u = User(
            school_id=test_school.id, username=uname, mobile=f"+9199{abs(hash(uname)) % 100000000:08d}",
            full_name=name, role=role, password_hash="x", is_active=True,
        )
        db_session.add(u)
        return u

    teacher_a = mk_user("t_a", UserRole.CLASS_INCHARGE, "Teacher A")
    teacher_b = mk_user("t_b", UserRole.CLASS_INCHARGE, "Teacher B")
    subj_a = mk_user("s_a", UserRole.TEACHER, "Subject A")
    await db_session.flush()

    class_a = Class(school_id=test_school.id, grade="Class 7", section="A",
                    academic_year_id=ay.id, class_incharge_id=teacher_a.id)
    class_b = Class(school_id=test_school.id, grade="Class 8", section="B",
                    academic_year_id=ay.id, class_incharge_id=teacher_b.id)
    db_session.add_all([class_a, class_b])
    await db_session.flush()

    math_a = Subject(school_id=test_school.id, name="Mathematics", class_id=class_a.id)
    math_b = Subject(school_id=test_school.id, name="Mathematics", class_id=class_b.id)
    db_session.add_all([math_a, math_b])
    await db_session.flush()

    # subj_a teaches Mathematics in class A only.
    db_session.add(TeacherSubjectMapping(
        school_id=test_school.id, teacher_id=subj_a.id, subject_id=math_a.id, class_id=class_a.id,
    ))
    await db_session.flush()

    def mk_student(uname, adm, cls):
        u = mk_user(uname, UserRole.STUDENT, f"Stu {uname}")
        return u, cls

    stu_a_user = mk_user("stu_a", UserRole.STUDENT, "Student A")
    stu_b_user = mk_user("stu_b", UserRole.STUDENT, "Student B")
    await db_session.flush()
    student_a = Student(school_id=test_school.id, user_id=stu_a_user.id, class_id=class_a.id,
                        admission_no="SCA001", roll_no="1")
    student_b = Student(school_id=test_school.id, user_id=stu_b_user.id, class_id=class_b.id,
                        admission_no="SCB001", roll_no="1")
    db_session.add_all([student_a, student_b])
    await db_session.flush()

    # Marks + attendance for student_a so authorized reads return real data.
    exam_a = Exam(school_id=test_school.id, class_id=class_a.id, subject_id=math_a.id,
                  exam_type=ExamType.MID_TERM, title="Mid Term — Mathematics",
                  total_marks=Decimal("100.00"), date=date(2026, 9, 1), created_by=teacher_a.id)
    db_session.add(exam_a)
    await db_session.flush()
    db_session.add(ExamMark(school_id=test_school.id, exam_id=exam_a.id, student_id=student_a.id,
                            marks_obtained=Decimal("77.00"), grade_letter="B"))
    db_session.add(Attendance(school_id=test_school.id, student_id=student_a.id,
                              class_id=class_a.id, date=date(2026, 9, 1),
                              status=AttendanceStatus.PRESENT, marked_by=teacher_a.id))
    await db_session.flush()

    return {
        "teacher_a": teacher_a, "teacher_b": teacher_b, "subj_a": subj_a,
        "class_a": class_a, "class_b": class_b,
        "student_a": student_a, "student_b": student_b,
        "stu_a_user": stu_a_user, "stu_b_user": stu_b_user,
    }


# ── Teacher class scope: exam results ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_incharge_can_read_own_class_results(
    test_school: School, scoped_school, db_session: AsyncSession
):
    user = _U(scoped_school["teacher_a"].id, test_school.id, "class_incharge")
    block = await cap.class_results(db_session, user, {"class_label": "Class 7 A"})
    assert block["kind"] == "table"  # ALLOW


@pytest.mark.asyncio
async def test_incharge_denied_other_class_results(
    test_school: School, scoped_school, db_session: AsyncSession
):
    """Teacher A (incharge of 7A) must NOT read 8B results -> denied, no data leaked."""
    user = _U(scoped_school["teacher_a"].id, test_school.id, "class_incharge")
    block = await cap.class_results(db_session, user, {"class_label": "Class 8 B"})
    assert block["kind"] == "not_found"
    assert block["title"] == "Not available"
    assert "77" not in str(block)  # no marks leaked


@pytest.mark.asyncio
async def test_subject_teacher_scope_on_results(
    test_school: School, scoped_school, db_session: AsyncSession
):
    # subj_a teaches Maths in class A -> may read class A results, not class B.
    user = _U(scoped_school["subj_a"].id, test_school.id, "teacher")
    ok = await cap.class_results(db_session, user, {"class_label": "Class 7 A"})
    assert ok["kind"] == "table"
    denied = await cap.class_results(db_session, user, {"class_label": "Class 8 B"})
    assert denied["title"] == "Not available"


@pytest.mark.asyncio
async def test_subject_toppers_scope(
    test_school: School, scoped_school, db_session: AsyncSession
):
    user = _U(scoped_school["teacher_a"].id, test_school.id, "class_incharge")
    denied = await cap.subject_toppers(
        db_session, user, {"class_label": "Class 8 B", "subject": "Mathematics"}
    )
    assert denied["title"] == "Not available"


# ── Teacher student scope ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_teacher_denied_out_of_scope_student_marks(
    test_school: School, scoped_school, db_session: AsyncSession
):
    """Teacher A may read student_a (class 7A) marks, not student_b (class 8B)."""
    user = _U(scoped_school["teacher_a"].id, test_school.id, "class_incharge")
    ok = await cap.student_marks(db_session, user, {"student": "SCA001"})
    assert ok["kind"] == "table"
    denied = await cap.student_marks(db_session, user, {"student": "SCB001"})
    assert denied["title"] == "Not available"


@pytest.mark.asyncio
async def test_teacher_denied_out_of_scope_attendance(
    test_school: School, scoped_school, db_session: AsyncSession
):
    user = _U(scoped_school["teacher_a"].id, test_school.id, "class_incharge")
    denied = await cap.student_attendance(db_session, user, {"student": "SCB001"})
    assert denied["title"] == "Not available"


# ── Class roster + attendance scope ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_class_roster_scope(
    test_school: School, scoped_school, db_session: AsyncSession
):
    user = _U(scoped_school["teacher_a"].id, test_school.id, "class_incharge")
    ok = await cap.class_roster(db_session, user, {"class_label": "Class 7 A"})
    assert ok["kind"] == "table"
    denied = await cap.class_roster(db_session, user, {"class_label": "Class 8 B"})
    assert denied["title"] == "Not available"


@pytest.mark.asyncio
async def test_low_attendance_scoped_to_own_classes(
    test_school: School, scoped_school, db_session: AsyncSession
):
    """A scoped teacher asking school-wide low attendance only sees their own classes."""
    user = _U(scoped_school["subj_a"].id, test_school.id, "teacher")
    # No class named -> must be limited to subj_a's classes (class A), never class B.
    block = await cap.low_attendance_students(db_session, user, {"below_percent": 100})
    assert block["kind"] == "table"
    labels = {r["class_label"] for r in block["rows"]}
    assert "Class 8 B" not in labels  # never leaks another class
    # Explicitly requesting an out-of-scope class is denied.
    denied = await cap.low_attendance_students(
        db_session, user, {"below_percent": 100, "class_label": "Class 8 B"}
    )
    assert denied["title"] == "Not available"


# ── Admin: full scope ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_admin_school_wide(
    test_school: School, scoped_school, admin_user, db_session: AsyncSession
):
    user = _U(admin_user.id, test_school.id, "super_admin")
    a = await cap.class_results(db_session, user, {"class_label": "Class 7 A"})
    b = await cap.class_results(db_session, user, {"class_label": "Class 8 B"})
    assert a["kind"] == "table" and b["kind"] in ("table", "not_found")
    # not_found for B only if it truly has no marks — never an authz denial for admin.
    assert b["title"] != "Not available"


# ── Parent scope ──────────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def parent_of_a(db_session: AsyncSession, test_school: School, scoped_school):
    u = User(school_id=test_school.id, username="par_a", mobile="+919000000021",
             full_name="Parent A", role=UserRole.PARENT, password_hash="x", is_active=True)
    db_session.add(u)
    await db_session.flush()
    p = Parent(school_id=test_school.id, user_id=u.id)
    db_session.add(p)
    await db_session.flush()
    db_session.add(StudentParentMap(
        school_id=test_school.id, student_id=scoped_school["student_a"].id, parent_id=p.id,
        is_primary=True, relationship_type=Relationship.FATHER,
    ))
    await db_session.flush()
    return u


@pytest.mark.asyncio
async def test_parent_own_child_allowed_other_denied(
    test_school: School, scoped_school, parent_of_a, db_session: AsyncSession
):
    user = _U(parent_of_a.id, test_school.id, "parent")
    ok = await cap.student_attendance(db_session, user, {"student": "SCA001"})
    assert ok["kind"] == "metrics"  # own child
    denied = await cap.student_attendance(db_session, user, {"student": "SCB001"})
    assert denied["title"] == "Not available"  # another child


# ── Student scope ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_student_self_allowed_other_denied(
    test_school: School, scoped_school, db_session: AsyncSession
):
    user = _U(scoped_school["stu_a_user"].id, test_school.id, "student")
    ok = await cap.student_marks(db_session, user, {"student": "SCA001"})
    assert ok["kind"] == "table"  # self
    denied = await cap.student_marks(db_session, user, {"student": "SCB001"})
    assert denied["title"] == "Not available"  # another student
