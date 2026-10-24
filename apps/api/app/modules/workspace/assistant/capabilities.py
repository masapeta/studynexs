"""Executor capabilities — deterministic, tenant-scoped handlers the planner invokes.

Every handler:
  - derives school_id from the authenticated user (never the client / LLM),
  - resolves NL tokens to canonical entities first (spec §5),
  - validates zero results before declaring "none exist" (spec §14),
  - returns a typed response block (metrics / table / entity / clarify / not_found).

Business logic is reused from existing services wherever one exists (spec §7, §25).
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authorization import assert_can_access_student
from app.core.dependencies import CurrentUser
from app.core.staff_permissions import (
    assert_class_access,
    assert_exam_class,
    get_staff_scope,
)
from app.db.models.academic import Class, Subject, TeacherSubjectMapping
from app.db.models.attendance import Attendance
from app.db.models.examination import Exam, ExamMark
from app.db.models.school_ops import StaffProfile
from app.db.models.student import Student
from app.db.models.user import User, UserRole
from app.modules.workspace.assistant.resolver import (
    Resolution,
    resolve_class,
    resolve_student,
    resolve_subject,
    resolve_teacher,
)
from app.modules.workspace.assistant.school_pack import get_school_pack

# ── Shared block builders ─────────────────────────────────────────────────────


def _clarify_block(res: Resolution, noun: str) -> dict[str, Any]:
    """Ambiguous entity → ask which one (spec §5, §22)."""
    return {
        "kind": "clarify",
        "title": f"Which {noun} do you mean?",
        "message": f"I found {len(res.candidates)} matches for “{res.query}”. Please pick one.",
        "options": [{"id": str(c.id), "label": c.label} for c in res.candidates],
    }


def _not_found_block(query: str, noun: str) -> dict[str, Any]:
    return {
        "kind": "not_found",
        "title": f"No {noun} found",
        "message": f"I couldn't find a {noun} matching “{query}”. Check the spelling or ID.",
    }


# ── Authorization (P1.1) ───────────────────────────────────────────────────────
# Scope is enforced server-side here — never via the planner/LLM (spec §2, §7). We REUSE
# the ERP's authoritative rules (assert_can_access_student / StaffScope / assert_exam_class),
# never a parallel model. Enforcement happens AFTER entity resolution: resolving "8B" to a
# class_id does not imply permission to read it (spec §8). A denial returns a non-leaky
# block that neither confirms nor denies the entity's existence or its contents (spec §14).


def _denied_block(noun: str = "information") -> dict[str, Any]:
    """Honest, non-leaky authorization denial (does not reveal names/marks/existence)."""
    return {
        "kind": "not_found",
        "title": "Not available",
        "message": (
            f"You don't have access to that {noun}, or it isn't available to your role. "
            "You can only see data for the classes and students assigned to you."
        ),
    }


async def _authorize_student(
    db: AsyncSession, user: CurrentUser, student_id: uuid.UUID, *, noun: str = "student"
) -> dict[str, Any] | None:
    """Return a denial block if the user may not access this student, else None.

    Reuses assert_can_access_student (admin/ops school-wide, parent=linked child,
    student=self, teacher/incharge=class scope). 403/404 -> non-leaky block.
    """
    try:
        await assert_can_access_student(user, db, student_id)
        return None
    except HTTPException:
        return _denied_block(noun)


async def _authorize_class(
    db: AsyncSession, user: CurrentUser, class_id: uuid.UUID, *, exams: bool = False
) -> dict[str, Any] | None:
    """Return a denial block if the user may not access this class, else None.

    Reuses StaffScope: exam/result views use assert_exam_class (admin|incharge|teaches-class);
    other class views use assert_class_access. Parent/student roles have no class scope here.
    """
    if user.role in ("parent", "student"):
        return _denied_block("class")
    scope = await get_staff_scope(db, user)
    try:
        if exams:
            assert_exam_class(scope, class_id)
        else:
            assert_class_access(scope, class_id)
        return None
    except HTTPException:
        return _denied_block("class")


async def _authorized_class_ids(
    db: AsyncSession, user: CurrentUser, class_ids: list[uuid.UUID], *, exams: bool = False
) -> list[uuid.UUID]:
    """Filter a resolved class list to those the user may access (admin = all).

    Scopes multi-class resolutions ('class 10' -> 10A/10B) at the source, so a scoped
    staff member never sees a class outside their assignments (spec §6, §17).
    """
    if user.role in ("parent", "student"):
        return []
    scope = await get_staff_scope(db, user)
    if scope.is_admin:
        return list(class_ids)
    permitted = scope.all_class_ids() or set()
    return [cid for cid in class_ids if cid in permitted]


async def _resolve_one_student(
    db: AsyncSession, school_id: uuid.UUID, token: str
) -> tuple[Any, dict[str, Any] | None]:
    """Return (ResolvedEntity, None) or (None, block) when empty/ambiguous."""
    res = await resolve_student(db, school_id, token)
    if res.is_empty:
        return None, _not_found_block(token, "student")
    if res.is_ambiguous:
        return None, _clarify_block(res, "student")
    return res.one, None


# ── Student capabilities ──────────────────────────────────────────────────────


async def student_attendance(
    db: AsyncSession, user: CurrentUser, params: dict[str, Any]
) -> dict[str, Any]:
    """Attendance % + breakdown for one student (resolved by admission no / name).

    Honours an optional resolved date range in params['_range'] (a DateRange).
    """
    from app.modules.attendance.services.attendance_service import AttendanceService

    school_id = uuid.UUID(user.school_id)
    token = str(params.get("student") or params.get("student_id") or "").strip()
    entity, block = await _resolve_one_student(db, school_id, token)
    if block:
        return block
    denied = await _authorize_student(db, user, entity.id)
    if denied:
        return denied

    rng = params.get("_range")
    start = rng.start_date if rng and not rng.is_all_time else None
    end = rng.end_date if rng and not rng.is_all_time else None
    summary = await AttendanceService(db).student_summary_in_range(
        school_id, entity.id, start=start, end=end
    )
    total = summary["total"]
    # Re-score the raw status counts under the active school's attendance policy (§4/§5),
    # rather than the service's fixed convention, so a school's denominator/credit rule applies.
    pct = get_school_pack().attendance_percentage(
        {k: summary.get(k, 0) for k in ("present", "late", "half_day", "absent")}
    )
    scope = f" ({rng.label})" if rng and not rng.is_all_time else ""

    if total == 0:
        msg = (
            f"No attendance has been recorded for this student{scope}."
            if scope
            else "No attendance has been recorded for this student yet."
        )
        return {
            "kind": "metrics",
            "title": f"Attendance — {entity.detail['name']}{scope}",
            "source": "Attendance System",
            "message": msg,
            "metrics": [],
            "subtitle": entity.label,
        }
    return {
        "kind": "metrics",
        "title": f"Attendance — {entity.detail['name']}{scope}",
        "subtitle": entity.label,
        "source": "Attendance System",
        "metrics": [
            {"label": "Attendance", "value": pct, "format": "percent"},
            {"label": "Present", "value": summary["present"]},
            {"label": "Absent", "value": summary["absent"]},
            {"label": "Days recorded", "value": total},
        ],
        "href": "/dashboard/attendance",
        "href_label": "Open attendance",
    }


async def fee_collection_period(
    db: AsyncSession, user: CurrentUser, params: dict[str, Any]
) -> dict[str, Any]:
    """Fee collected within a time window (today, this month, a date range, …).

    Uses params['_range'] resolved from the query's temporal token. Without a range
    it reports all-time collection.
    """
    from app.modules.fees.services.fee_service import FeeService

    school_id = uuid.UUID(user.school_id)
    rng = params.get("_range")
    start = rng.start if rng and not rng.is_all_time else None
    end = rng.end if rng and not rng.is_all_time else None
    result = await FeeService(db).collection_in_range(school_id, start=start, end=end)
    scope = rng.label if rng else "all time"
    return {
        "kind": "metrics",
        "title": f"Fee collected — {scope}",
        "source": "Fee System",
        "metrics": [
            {"label": "Collected", "value": result["collected"], "format": "money"},
            {"label": "Receipts", "value": result["receipt_count"]},
        ],
        "href": "/dashboard/finance",
        "href_label": "Open finance",
    }


async def student_profile(
    db: AsyncSession, user: CurrentUser, params: dict[str, Any]
) -> dict[str, Any]:
    """Full profile snapshot for one student (reuses AcademicService.student_profile)."""
    from app.modules.academic.services.academic_service import AcademicService

    school_id = uuid.UUID(user.school_id)
    token = str(params.get("student") or params.get("student_id") or "").strip()
    entity, block = await _resolve_one_student(db, school_id, token)
    if block:
        return block
    denied = await _authorize_student(db, user, entity.id)
    if denied:
        return denied

    profile = await AcademicService(db).student_profile(school_id, entity.id)
    if not profile:
        return _not_found_block(token, "student")
    att = profile.get("attendance") or {}
    fees = profile.get("fees") or {}
    return {
        "kind": "metrics",
        "title": f"Profile — {entity.detail['name']}",
        "subtitle": entity.label,
        "source": "Student Information System",
        "metrics": [
            {"label": "Attendance", "value": att.get("percentage"), "format": "percent"},
            {"label": "Fee pending", "value": fees.get("pending"), "format": "money"},
            {"label": "Fee paid", "value": fees.get("paid"), "format": "money"},
        ],
        "href": "/dashboard/students",
        "href_label": "Open students",
    }


async def student_fees(
    db: AsyncSession, user: CurrentUser, params: dict[str, Any]
) -> dict[str, Any]:
    """Fee balance for one student."""
    from app.modules.academic.services.academic_service import AcademicService

    school_id = uuid.UUID(user.school_id)
    token = str(params.get("student") or params.get("student_id") or "").strip()
    entity, block = await _resolve_one_student(db, school_id, token)
    if block:
        return block
    denied = await _authorize_student(db, user, entity.id)
    if denied:
        return denied
    profile = await AcademicService(db).student_profile(school_id, entity.id)
    fees = (profile or {}).get("fees") or {}
    return {
        "kind": "metrics",
        "title": f"Fees — {entity.detail['name']}",
        "subtitle": entity.label,
        "source": "Fee System",
        "metrics": [
            {"label": "Total", "value": fees.get("total"), "format": "money"},
            {"label": "Paid", "value": fees.get("paid"), "format": "money"},
            {"label": "Pending", "value": fees.get("pending"), "format": "money"},
        ],
        "href": "/dashboard/finance",
        "href_label": "Open finance",
    }


# ── Class capabilities ────────────────────────────────────────────────────────


async def class_roster(
    db: AsyncSession, user: CurrentUser, params: dict[str, Any]
) -> dict[str, Any]:
    """List students in a class (resolved by label)."""
    school_id = uuid.UUID(user.school_id)
    token = str(params.get("class_label") or params.get("class") or "").strip()
    res = await resolve_class(db, school_id, token)
    if res.is_empty:
        return _not_found_block(token, "class")

    # Authorize each resolved class; scoped staff keep only classes they may access.
    allowed = await _authorized_class_ids(db, user, [c.id for c in res.candidates])
    if not allowed:
        return _denied_block("class")
    class_ids = allowed
    rows = (
        await db.execute(
            select(
                User.full_name,
                Student.admission_no,
                Student.roll_no,
                Class.grade,
                Class.section,
            )
            .join(User, User.id == Student.user_id)
            .join(Class, Class.id == Student.class_id)
            .where(Student.school_id == school_id, Student.class_id.in_(class_ids))
            .order_by(Student.admission_no)
        )
    ).all()
    _pack = get_school_pack()
    students = [
        {
            "name": name,
            "admission_no": adm,
            "roll_no": roll or "—",
            "class_label": _pack.class_label(grade, section),
        }
        for name, adm, roll, grade, section in rows
    ]
    label = ", ".join(c.label for c in res.candidates)
    return {
        "kind": "table",
        "title": f"Students in {label}",
        "source": "Student Information System",
        "columns": [
            {"key": "admission_no", "label": "Admission no"},
            {"key": "name", "label": "Student"},
            {"key": "roll_no", "label": "Roll"},
            {"key": "class_label", "label": "Class"},
        ],
        "rows": students,
        "empty_message": f"No students are enrolled in {label} yet.",
        "href": "/dashboard/students",
        "href_label": "Open students",
    }


async def class_attendance_today(
    db: AsyncSession, user: CurrentUser, params: dict[str, Any]
) -> dict[str, Any]:
    """Today's attendance summary for a class (present/absent/%)."""
    from app.modules.attendance.services.attendance_service import AttendanceService

    school_id = uuid.UUID(user.school_id)
    token = str(params.get("class_label") or params.get("class") or "").strip()
    res = await resolve_class(db, school_id, token)
    if res.is_empty:
        return _not_found_block(token, "class")
    if res.is_ambiguous:
        return _clarify_block(res, "class")

    cls = res.one
    denied = await _authorize_class(db, user, cls.id)
    if denied:
        return denied
    summary = await AttendanceService(db).get_summary(school_id, cls.id, date.today())
    total = summary["total"]
    # School-configured denominator/credit policy scores the raw status counts (§4/§5).
    pct = get_school_pack().attendance_percentage(
        {k: summary.get(k, 0) for k in ("present", "late", "half_day", "absent")}
    )
    if total == 0:
        return {
            "kind": "metrics",
            "title": f"Attendance today — {cls.label}",
            "source": "Attendance System",
            "message": "Attendance hasn't been marked for this class today.",
            "metrics": [],
        }
    return {
        "kind": "metrics",
        "title": f"Attendance today — {cls.label}",
        "source": "Attendance System",
        "metrics": [
            {"label": "Attendance", "value": pct, "format": "percent"},
            {"label": "Present", "value": summary["present"]},
            {"label": "Absent", "value": summary["absent"]},
            {"label": "Late", "value": summary["late"]},
        ],
        "href": "/dashboard/attendance",
        "href_label": "Open attendance",
    }


async def low_attendance_students(
    db: AsyncSession, user: CurrentUser, params: dict[str, Any]
) -> dict[str, Any]:
    """Students below an attendance % threshold (default 75), optionally in one class."""
    school_id = uuid.UUID(user.school_id)
    try:
        threshold = float(params.get("below_percent", 75))
    except (TypeError, ValueError):
        threshold = 75.0
    class_token = str(params.get("class_label") or params.get("class") or "").strip()

    class_filter_ids: list[uuid.UUID] | None = None
    class_label = ""
    if class_token:
        res = await resolve_class(db, school_id, class_token)
        if res.is_empty:
            return _not_found_block(class_token, "class")
        # Scope requested classes to those the user may access (§6: scope the source).
        class_filter_ids = await _authorized_class_ids(db, user, [c.id for c in res.candidates])
        if not class_filter_ids:
            return _denied_block("class")
        class_label = ", ".join(
            c.label for c in res.candidates if c.id in set(class_filter_ids)
        )
    else:
        # No class named: a scoped (non-admin) staff member sees only their own classes,
        # never the whole school. Admin -> None (unrestricted).
        scope = await get_staff_scope(db, user)
        if scope.scoped_only:
            permitted = scope.all_class_ids() or set()
            if not permitted:
                return _denied_block("class")
            class_filter_ids = list(permitted)

    # Aggregate per-student, per-STATUS counts (one bounded query), then let the active
    # school's attendance policy score them (§4/§5) — no fixed credited/denominator here.
    q = (
        select(
            Student.id,
            User.full_name,
            Student.admission_no,
            Class.grade,
            Class.section,
            Attendance.status,
            func.count(Attendance.id).label("n"),
        )
        .join(User, User.id == Student.user_id)
        .join(Class, Class.id == Student.class_id)
        .join(Attendance, Attendance.student_id == Student.id)
        .where(Student.school_id == school_id)
        .group_by(
            Student.id, User.full_name, Student.admission_no,
            Class.grade, Class.section, Attendance.status,
        )
    )
    if class_filter_ids:
        q = q.where(Student.class_id.in_(class_filter_ids))

    pack = get_school_pack()
    by_student: dict[uuid.UUID, dict[str, Any]] = {}
    for sid, name, adm, grade, section, status, n in (await db.execute(q)).all():
        rec = by_student.setdefault(
            sid, {"name": name, "adm": adm, "grade": grade, "section": section, "counts": {}}
        )
        key = status.value if hasattr(status, "value") else str(status)
        rec["counts"][key] = rec["counts"].get(key, 0) + int(n)

    students = []
    for rec in by_student.values():
        pct = pack.attendance_percentage(rec["counts"])
        if pct is not None and pct < threshold:
            students.append(
                {
                    "name": rec["name"],
                    "admission_no": rec["adm"],
                    "class_label": pack.class_label(rec["grade"], rec["section"]),
                    "attendance_percent": pct,
                }
            )
    students.sort(key=lambda r: r["attendance_percent"])
    scope = f" in {class_label}" if class_label else ""
    return {
        "kind": "table",
        "title": f"Students below {threshold:g}% attendance{scope}",
        "source": "Attendance System",
        "columns": [
            {"key": "admission_no", "label": "Admission no"},
            {"key": "name", "label": "Student"},
            {"key": "class_label", "label": "Class"},
            {"key": "attendance_percent", "label": "Attendance %", "format": "percent"},
        ],
        "rows": students,
        "empty_message": f"No students are below {threshold:g}% attendance{scope}.",
        "href": "/dashboard/attendance",
        "href_label": "Open attendance",
    }


# ── Teacher capabilities ──────────────────────────────────────────────────────


async def teachers_for_class(
    db: AsyncSession, user: CurrentUser, params: dict[str, Any]
) -> dict[str, Any]:
    """Teachers assigned to classes: BOTH class incharge (homeroom) and subject teachers.

    Fixes the "0 results for 2A" bug: the class incharge lives on Class.class_incharge_id,
    a separate relationship from TeacherSubjectMapping. Omit class_label for all classes.
    """
    school_id = uuid.UUID(user.school_id)
    token = str(params.get("class_label") or params.get("class") or "").strip()

    class_ids: list[uuid.UUID] | None = None
    class_label = ""
    if token:
        res = await resolve_class(db, school_id, token)
        if res.is_empty:
            return _not_found_block(token, "class")
        class_ids = [c.id for c in res.candidates]
        class_label = ", ".join(c.label for c in res.candidates)

    pack = get_school_pack()
    incharge_term = pack.class_incharge_term  # SchoolPack terminology (default "Class Teacher")

    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()

    # 1) Class incharges (the school's "class teacher" role) — Class.class_incharge_id.
    incharge_q = (
        select(User.full_name, Class.grade, Class.section)
        .join(Class, Class.class_incharge_id == User.id)
        .where(Class.school_id == school_id, Class.class_incharge_id.is_not(None))
    )
    if class_ids:
        incharge_q = incharge_q.where(Class.id.in_(class_ids))
    for full_name, grade, section in (await db.execute(incharge_q)).all():
        label = pack.class_label(grade, section)
        key = (full_name, incharge_term, label)
        if key in seen:
            continue
        seen.add(key)
        rows.append({"name": full_name, "role": incharge_term, "class_label": label})

    # 2) Subject teachers — TeacherSubjectMapping.
    subject_q = (
        select(User.full_name, Subject.name, Class.grade, Class.section)
        .join(TeacherSubjectMapping, TeacherSubjectMapping.teacher_id == User.id)
        .join(Subject, Subject.id == TeacherSubjectMapping.subject_id)
        .join(Class, Class.id == TeacherSubjectMapping.class_id)
        .where(TeacherSubjectMapping.school_id == school_id)
    )
    if class_ids:
        subject_q = subject_q.where(TeacherSubjectMapping.class_id.in_(class_ids))
    for full_name, subject_name, grade, section in (await db.execute(subject_q)).all():
        label = pack.class_label(grade, section)
        key = (full_name, subject_name, label)
        if key in seen:
            continue
        seen.add(key)
        rows.append({"name": full_name, "role": subject_name, "class_label": label})

    rows.sort(key=lambda r: (r["class_label"], r["role"] != incharge_term, r["name"]))
    scope = f" for {class_label}" if class_label else ""
    return {
        "kind": "table",
        "title": f"Teachers{scope}" if class_label else "Teachers and their classes",
        "source": "Academic / Class assignments",
        "columns": [
            {"key": "name", "label": "Teacher"},
            {"key": "role", "label": "Role / Subject"},
            {"key": "class_label", "label": "Class"},
        ],
        "rows": rows,
        "empty_message": (
            f"No teachers are assigned{scope} yet."
            if class_label
            else "No teacher assignments found yet."
        ),
        "href": "/dashboard/classes",
        "href_label": "Open classes",
    }


async def teacher_assignments(
    db: AsyncSession, user: CurrentUser, params: dict[str, Any]
) -> dict[str, Any]:
    """What a specific teacher teaches: subjects + classes, and any homeroom class."""
    school_id = uuid.UUID(user.school_id)
    token = str(params.get("teacher") or params.get("teacher_id") or "").strip()
    res = await resolve_teacher(db, school_id, token)
    if res.is_empty:
        return _not_found_block(token, "teacher")
    if res.is_ambiguous:
        return _clarify_block(res, "teacher")

    teacher = res.one
    pack = get_school_pack()
    rows: list[dict[str, Any]] = []

    # Homeroom / class-incharge classes (school's term).
    for grade, section in (
        await db.execute(
            select(Class.grade, Class.section).where(
                Class.school_id == school_id, Class.class_incharge_id == teacher.id
            )
        )
    ).all():
        rows.append(
            {"subject": f"{pack.class_incharge_term} (homeroom)",
             "class_label": pack.class_label(grade, section)}
        )

    # Subject assignments.
    for subject_name, grade, section in (
        await db.execute(
            select(Subject.name, Class.grade, Class.section)
            .join(TeacherSubjectMapping, TeacherSubjectMapping.subject_id == Subject.id)
            .join(Class, Class.id == TeacherSubjectMapping.class_id)
            .where(
                TeacherSubjectMapping.school_id == school_id,
                TeacherSubjectMapping.teacher_id == teacher.id,
            )
        )
    ).all():
        rows.append({"subject": subject_name, "class_label": pack.class_label(grade, section)})

    rows.sort(key=lambda r: (r["class_label"], r["subject"]))
    return {
        "kind": "table",
        "title": f"Assignments — {teacher.detail['name']}",
        "subtitle": teacher.label,
        "source": "Academic / Class assignments",
        "columns": [
            {"key": "subject", "label": "Subject / Role"},
            {"key": "class_label", "label": "Class"},
        ],
        "rows": rows,
        "empty_message": f"{teacher.detail['name']} has no class or subject assignments yet.",
        "href": "/dashboard/classes",
        "href_label": "Open classes",
    }


_STAFF_DIR_ROLES = (
    UserRole.SUPER_ADMIN,
    UserRole.ADMIN,
    UserRole.CLASS_INCHARGE,
    UserRole.TEACHER,
    UserRole.OPERATIONS,
)


async def staff_directory(
    db: AsyncSession, user: CurrentUser, params: dict[str, Any]
) -> dict[str, Any]:
    """List staff (users with a staff role), optionally filtered by department.

    Staff profiles are optional in the ERP, so the profile is LEFT joined — a user
    without an HR profile is still staff and must appear (matches ops directory).
    """
    school_id = uuid.UUID(user.school_id)
    department = str(params.get("department") or "").strip()

    q = (
        select(
            User.full_name,
            StaffProfile.employee_id,
            StaffProfile.department,
            User.role,
        )
        .outerjoin(
            StaffProfile,
            (StaffProfile.user_id == User.id) & (StaffProfile.school_id == school_id),
        )
        .where(
            User.school_id == school_id,
            User.role.in_(_STAFF_DIR_ROLES),
            User.is_active.is_(True),
        )
        .order_by(User.full_name)
    )
    if department:
        q = q.where(StaffProfile.department.ilike(f"%{department}%"))
    rows = [
        {
            "name": name,
            "employee_id": emp or "—",
            "department": dept or "—",
            "role": role.value if hasattr(role, "value") else role,
        }
        for name, emp, dept, role in (await db.execute(q)).all()
    ]
    scope = f" in {department}" if department else ""
    return {
        "kind": "table",
        "title": f"Staff directory{scope}",
        "source": "HR / Staff",
        "columns": [
            {"key": "employee_id", "label": "Employee ID"},
            {"key": "name", "label": "Name"},
            {"key": "department", "label": "Department"},
            {"key": "role", "label": "Role"},
        ],
        "rows": rows,
        "empty_message": f"No staff found{scope}.",
        "href": "/dashboard/staff",
        "href_label": "Open staff",
    }

# ── Exam / marks capabilities (P1) ────────────────────────────────────────────
# Grounded strictly in the audited schema: Exam(class, subject, exam_type, total_marks,
# date?) + ExamMark(marks_obtained, grade_letter?). The ERP models NO "term", NO
# pass/fail. grade_letter is stored-but-optional; a percentage is marks_obtained/total
# and is labelled as such — never asserted as pass/fail. "latest" = most recent by
# exam date (nulls last) then created_at, mirroring get_gradebook's latest-per-subject.


def _mark_pct(obtained: float, total: float) -> float | None:
    return round(obtained / total * 100, 1) if total else None


async def student_marks(
    db: AsyncSession, user: CurrentUser, params: dict[str, Any]
) -> dict[str, Any]:
    """One student's exam marks — every subject, or a single subject if named.

    Returns each exam's obtained/total, percentage (of total), and the stored grade letter
    if the school recorded one. No pass/fail is asserted (the ERP has no such concept).
    """
    school_id = uuid.UUID(user.school_id)
    token = str(params.get("student") or params.get("student_id") or "").strip()
    entity, block = await _resolve_one_student(db, school_id, token)
    if block:
        return block
    denied = await _authorize_student(db, user, entity.id)
    if denied:
        return denied

    student_id = entity.id
    class_id = uuid.UUID(entity.detail["class_id"])
    subject_token = str(params.get("subject") or "").strip()

    q = (
        select(
            Exam.title,
            Subject.name,
            Exam.exam_type,
            Exam.total_marks,
            Exam.date,
            ExamMark.marks_obtained,
            ExamMark.grade_letter,
        )
        .join(Exam, Exam.id == ExamMark.exam_id)
        .join(Subject, Subject.id == Exam.subject_id)
        .where(ExamMark.school_id == school_id, ExamMark.student_id == student_id)
    )
    subject_label = ""
    if subject_token:
        sres = await resolve_subject(db, school_id, subject_token, class_id=class_id)
        if sres.is_empty:
            return _not_found_block(subject_token, "subject")
        q = q.where(Exam.subject_id.in_([c.id for c in sres.candidates]))
        subject_label = f" — {sres.candidates[0].label}"

    rows = (
        await db.execute(q.order_by(Exam.date.desc().nullslast(), Exam.created_at.desc()))
    ).all()
    marks = []
    for title, subject, exam_type, total, exam_date, obtained, grade in rows:
        marks.append(
            {
                "exam": title,
                "subject": subject,
                "type": exam_type.value.replace("_", " ").title()
                if hasattr(exam_type, "value")
                else str(exam_type),
                "obtained": float(obtained),
                "total": float(total),
                "percentage": _mark_pct(float(obtained), float(total)),
                "grade": grade or "—",
                "date": exam_date.isoformat() if exam_date else "—",
            }
        )
    return {
        "kind": "table",
        "title": f"Marks — {entity.detail['name']}{subject_label}",
        "subtitle": entity.label,
        "source": "Examinations",
        "columns": [
            {"key": "exam", "label": "Exam"},
            {"key": "subject", "label": "Subject"},
            {"key": "type", "label": "Type"},
            {"key": "obtained", "label": "Marks"},
            {"key": "total", "label": "Out of"},
            {"key": "percentage", "label": "%", "format": "percent"},
            {"key": "grade", "label": "Grade"},
            {"key": "date", "label": "Date"},
        ],
        "rows": marks,
        "empty_message": (
            f"No exam marks are recorded for this student{subject_label} yet."
        ),
        "href": "/dashboard/teaching",
        "href_label": "Open assessments",
    }


async def class_results(
    db: AsyncSession, user: CurrentUser, params: dict[str, Any]
) -> dict[str, Any]:
    """Class results matrix — latest exam per subject, per student, with an average %.

    Reuses ExamService.get_gradebook (the authoritative consolidation). Supports ranking
    ('top'/'bottom' N by average) and is the basis for comparison across students. The
    average is the mean of per-subject percentages; the grade letter comes from that
    service's banding — surfaced as a convenience, not a school-defined pass mark.
    """
    from app.modules.examinations.services.exam_service import ExamService

    school_id = uuid.UUID(user.school_id)
    token = str(params.get("class_label") or params.get("class") or "").strip()
    res = await resolve_class(db, school_id, token)
    if res.is_empty:
        return _not_found_block(token, "class")
    if res.is_ambiguous:
        return _clarify_block(res, "class")
    cls = res.one
    denied = await _authorize_class(db, user, cls.id, exams=True)
    if denied:
        return denied

    gradebook = await ExamService(db).get_gradebook(school_id, cls.id)
    subjects = gradebook.get("subjects", [])
    students = gradebook.get("students", [])
    if not students:
        return _not_found_block(token, "class")

    # Optional ranking by average %.
    order = str(params.get("order") or "").strip().lower()
    limit_raw = params.get("limit") or params.get("top") or params.get("bottom")
    if params.get("bottom") is not None and not order:
        order = "asc"
    ranked = [s for s in students if s.get("average") is not None]
    unranked = [s for s in students if s.get("average") is None]
    if order in ("asc", "desc") or limit_raw:
        ranked.sort(key=lambda s: s["average"], reverse=(order != "asc"))
    students_sorted = ranked + unranked
    try:
        limit = int(limit_raw) if limit_raw is not None else None
    except (TypeError, ValueError):
        limit = None
    if limit:
        students_sorted = students_sorted[:limit]

    subject_cols = [{"key": f"s_{s['id']}", "label": s["short"]} for s in subjects]
    rows = []
    for s in students_sorted:
        row = {
            "name": s["name"],
            "average": s.get("average"),
            "grade": s.get("grade_letter") or "—",
        }
        for sub in subjects:
            val = s["marks"].get(sub["id"])
            row[f"s_{sub['id']}"] = val if val is not None else "—"
        rows.append(row)

    columns = (
        [{"key": "name", "label": "Student"}]
        + subject_cols
        + [
            {"key": "average", "label": "Average %", "format": "percent"},
            {"key": "grade", "label": "Grade"},
        ]
    )
    rank_note = ""
    if limit:
        rank_note = f" (top {limit})" if order != "asc" else f" (bottom {limit})"
    return {
        "kind": "table",
        "title": f"Results — {cls.label}{rank_note}",
        "subtitle": "Latest exam per subject",
        "source": "Examinations",
        "columns": columns,
        "rows": rows,
        "empty_message": f"No exam marks are recorded for {cls.label} yet.",
        "href": "/dashboard/teaching",
        "href_label": "Open assessments",
    }


async def subject_toppers(
    db: AsyncSession, user: CurrentUser, params: dict[str, Any]
) -> dict[str, Any]:
    """Ranking within a class + subject for its latest exam (top/bottom N by marks).

    Grounds 'who scored highest in Maths in 10A' — a single exam (the latest for that
    class+subject), ranked by marks obtained. No pass/fail; just the ordered scores.
    """
    school_id = uuid.UUID(user.school_id)
    class_token = str(params.get("class_label") or params.get("class") or "").strip()
    subject_token = str(params.get("subject") or "").strip()
    if not class_token or not subject_token:
        return {
            "kind": "clarify",
            "title": "Which class and subject?",
            "message": "Tell me the class and the subject, e.g. 'top scorers in Maths in 10A'.",
            "options": [],
        }
    cres = await resolve_class(db, school_id, class_token)
    if cres.is_empty:
        return _not_found_block(class_token, "class")
    if cres.is_ambiguous:
        return _clarify_block(cres, "class")
    cls = cres.one
    denied = await _authorize_class(db, user, cls.id, exams=True)
    if denied:
        return denied
    sres = await resolve_subject(db, school_id, subject_token, class_id=cls.id)
    if sres.is_empty:
        return _not_found_block(subject_token, "subject")

    # Latest exam for this class+subject.
    exam = (
        await db.execute(
            select(Exam)
            .where(
                Exam.school_id == school_id,
                Exam.class_id == cls.id,
                Exam.subject_id.in_([c.id for c in sres.candidates]),
            )
            .order_by(Exam.date.desc().nullslast(), Exam.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if exam is None:
        return {
            "kind": "not_found",
            "title": "No exam found",
            "message": (
                f"No {sres.candidates[0].label} exam has been recorded for {cls.label} yet."
            ),
        }

    order = str(params.get("order") or "desc").strip().lower()
    if params.get("bottom") is not None:
        order = "asc"
    try:
        limit = int(params.get("limit") or params.get("top") or params.get("bottom") or 0)
    except (TypeError, ValueError):
        limit = 0

    rows = (
        await db.execute(
            select(User.full_name, Student.admission_no, ExamMark.marks_obtained,
                   ExamMark.grade_letter)
            .join(Student, Student.id == ExamMark.student_id)
            .join(User, User.id == Student.user_id)
            .where(ExamMark.school_id == school_id, ExamMark.exam_id == exam.id)
        )
    ).all()
    scores = [
        {
            "admission_no": adm,
            "name": name,
            "obtained": float(obtained),
            "total": float(exam.total_marks),
            "percentage": _mark_pct(float(obtained), float(exam.total_marks)),
            "grade": grade or "—",
        }
        for name, adm, obtained, grade in rows
    ]
    scores.sort(key=lambda r: r["obtained"], reverse=(order != "asc"))
    if limit:
        scores = scores[:limit]
    rank_note = ""
    if limit:
        rank_note = f" — top {limit}" if order != "asc" else f" — bottom {limit}"
    return {
        "kind": "table",
        "title": f"{sres.candidates[0].label} · {cls.label}{rank_note}",
        "subtitle": f"{exam.title} (out of {exam.total_marks:g})",
        "source": "Examinations",
        "columns": [
            {"key": "admission_no", "label": "Admission no"},
            {"key": "name", "label": "Student"},
            {"key": "obtained", "label": "Marks"},
            {"key": "percentage", "label": "%", "format": "percent"},
            {"key": "grade", "label": "Grade"},
        ],
        "rows": scores,
        "empty_message": f"No marks recorded for {exam.title} yet.",
        "href": "/dashboard/teaching",
        "href_label": "Open assessments",
    }

# ── Parent capabilities (Milestone 1) ─────────────────────────────────────────
# Parents ask about THEIR OWN linked children only. These reuse the existing
# parent-scoped portal_service functions (already keyed by the authenticated parent's
# user_id via StudentParentMap), so the data source itself can never return another
# family's child. Child selection happens WITHIN that already-scoped set — never via the
# school-wide resolve_student (which would be a cross-family leak surface). After selection,
# _authorize_student re-runs the authoritative assert_can_access_student as defence-in-depth.
# No student_id is ever accepted from the planner/params — only a free-text `child` hint.


def _parent_child_denied() -> dict[str, Any]:
    """Non-leaky denial that never confirms another family's child exists."""
    return _not_found_block("that child", "child")


def _match_children(children: list[Any], token: str) -> list[Any]:
    """Match the parent's OWN children by a free-text hint (name / class / roll / first name)."""
    needle = token.strip().lower()
    if not needle:
        return list(children)
    hits = []
    for c in children:
        name = (getattr(c, "name", "") or "").lower()
        cls = (getattr(c, "class_label", "") or "").lower()
        roll = (getattr(c, "roll_no", "") or "").lower()
        hay = f"{name} {cls} {roll}"
        if needle in hay or any(needle == part for part in name.split()):
            hits.append(c)
    return hits


def _clarify_children(children: list[Any], noun: str) -> dict[str, Any]:
    """Ask which of the parent's OWN children is meant (only their children are listed)."""
    return {
        "kind": "clarify",
        "title": "Which child do you mean?",
        "message": f"You have {len(children)} children on record. Please pick one to see {noun}.",
        "options": [
            {
                "id": str(c.student_id),
                "label": (
                    f"{c.name} ({c.class_label})"
                    if getattr(c, "class_label", None)
                    else c.name
                ),
            }
            for c in children
        ],
    }


async def _select_one_child(
    children: list[Any], token: str, *, noun: str
) -> tuple[Any, dict[str, Any] | None]:
    """Return (child, None) or (None, block) — clarify for ambiguity, not_found for no match.

    Selection is strictly within the parent's own children list; it can never reach another
    family because the list was built from the parent's StudentParentMap rows.
    """
    if not children:
        return None, {
            "kind": "not_found",
            "title": "No children linked",
            "message": (
                "There are no children linked to your account yet. Please contact the school."
            ),
        }
    token = (token or "").strip()
    if not token:
        if len(children) == 1:
            return children[0], None
        return None, _clarify_children(children, noun)
    hits = _match_children(children, token)
    if len(hits) == 1:
        return hits[0], None
    if not hits:
        return None, _parent_child_denied()
    return None, _clarify_children(hits, noun)


async def my_children_overview(
    db: AsyncSession, user: CurrentUser, params: dict[str, Any]
) -> dict[str, Any]:
    """Overview of all of the authenticated parent's linked children."""
    from app.modules.portal.services.portal_service import build_portal_context

    school_id = uuid.UUID(user.school_id)
    ctx = await build_portal_context(
        db, school_id=school_id, user_id=uuid.UUID(user.id), role="parent"
    )
    rows = [
        {
            "name": c.name,
            "class_label": c.class_label,
            "attendance_pct": c.attendance_pct,
            "fee_pending": c.fee_pending,
            "weak_topic_count": c.weak_topic_count,
        }
        for c in ctx.children
    ]
    return {
        "kind": "table",
        "title": "My children",
        "source": "Student Information System",
        "columns": [
            {"key": "name", "label": "Child"},
            {"key": "class_label", "label": "Class"},
            {"key": "attendance_pct", "label": "Attendance", "format": "percent"},
            {"key": "fee_pending", "label": "Fee pending", "format": "money"},
            {"key": "weak_topic_count", "label": "Weak topics"},
        ],
        "rows": rows,
        "empty_message": "There are no children linked to your account yet.",
        "href": "/parent",
        "href_label": "Open parent home",
    }


async def my_child_attendance(
    db: AsyncSession, user: CurrentUser, params: dict[str, Any]
) -> dict[str, Any]:
    """Attendance for one of the parent's linked children (selected within their own set)."""
    from app.modules.portal.services.portal_service import build_portal_context

    school_id = uuid.UUID(user.school_id)
    ctx = await build_portal_context(
        db, school_id=school_id, user_id=uuid.UUID(user.id), role="parent"
    )
    child, block = await _select_one_child(
        ctx.children, str(params.get("child") or ""), noun="attendance"
    )
    if block:
        return block
    denied = await _authorize_student(db, user, child.student_id, noun="child")
    if denied:
        return denied
    if child.attendance_pct is None:
        return {
            "kind": "metrics",
            "title": f"Attendance — {child.name}",
            "subtitle": child.class_label,
            "source": "Attendance System",
            "message": "No attendance has been recorded for this child yet.",
            "metrics": [],
        }
    return {
        "kind": "metrics",
        "title": f"Attendance — {child.name}",
        "subtitle": child.class_label,
        "source": "Attendance System",
        "metrics": [
            {"label": "Attendance", "value": child.attendance_pct, "format": "percent"},
        ],
        "href": "/parent",
        "href_label": "Open parent home",
    }


async def my_child_progress(
    db: AsyncSession, user: CurrentUser, params: dict[str, Any]
) -> dict[str, Any]:
    """Academic progress + weak topics for one of the parent's linked children."""
    from app.modules.portal.services.portal_service import list_parent_children_progress

    school_id = uuid.UUID(user.school_id)
    children = await list_parent_children_progress(
        db, school_id=school_id, parent_user_id=uuid.UUID(user.id)
    )
    child, block = await _select_one_child(
        children, str(params.get("child") or ""), noun="progress"
    )
    if block:
        return block
    denied = await _authorize_student(db, user, child.student_id, noun="child")
    if denied:
        return denied
    rows = [
        {
            "subject_name": w.subject_name,
            "topic_display": w.topic_display,
            "mastery_pct": w.mastery_pct,
        }
        for w in child.weak_topics
    ]
    return {
        "kind": "table",
        "title": f"Topics to improve — {child.name}",
        "subtitle": child.class_label,
        "source": "Learning / Mastery",
        "columns": [
            {"key": "subject_name", "label": "Subject"},
            {"key": "topic_display", "label": "Topic"},
            {"key": "mastery_pct", "label": "Mastery", "format": "percent"},
        ],
        "rows": rows,
        "empty_message": (
            f"No weak topics are flagged for {child.name} right now — they're on track."
        ),
        "href": "/parent",
        "href_label": "Open parent home",
    }


async def my_child_fees(
    db: AsyncSession, user: CurrentUser, params: dict[str, Any]
) -> dict[str, Any]:
    """Fee records and payment status for one of the parent's linked children."""
    from app.modules.portal.services.portal_service import list_parent_children_fees

    school_id = uuid.UUID(user.school_id)
    children_fees = await list_parent_children_fees(
        db, school_id=school_id, parent_user_id=uuid.UUID(user.id)
    )
    child, block = await _select_one_child(
        children_fees, str(params.get("child") or ""), noun="fees"
    )
    if block:
        return block
    denied = await _authorize_student(db, user, child.student_id, noun="child")
    if denied:
        return denied
    rows = [
        {
            "fee_type": r.fee_type or "—",
            "amount": r.amount,
            "status": r.status,
            "due_date": r.due_date or "—",
        }
        for r in child.records
    ]
    return {
        "kind": "table",
        "title": f"Fees — {child.name}",
        "source": "Fee System",
        "columns": [
            {"key": "fee_type", "label": "Fee"},
            {"key": "amount", "label": "Amount", "format": "money"},
            {"key": "status", "label": "Status"},
            {"key": "due_date", "label": "Due date"},
        ],
        "rows": rows,
        "empty_message": f"No fee records are on file for {child.name}.",
        "href": "/parent/fees",
        "href_label": "Open fees",
    }

# ── Student capabilities (Milestone 2) ────────────────────────────────────────
# Students ask about THEIR OWN learning only. Identity is the authenticated student: the
# student row is resolved from CurrentUser.id (Student.user_id), never from a params-supplied
# id. Handlers reuse the existing authorized tutor/learning services (which themselves verify
# the student belongs to the school); _authorize_student re-runs assert_can_access_student
# (student = self only) as defence-in-depth. ask_tutor is the one METERED path — it reuses
# StudentCopilotService.ask unchanged, so credit reservation/usage controls stay intact.


async def _resolve_self_student_id(
    db: AsyncSession, user: CurrentUser
) -> tuple[uuid.UUID | None, dict[str, Any] | None]:
    """Resolve the authenticated student's own student_id — never from params (self only)."""
    school_id = uuid.UUID(user.school_id)
    row = (
        await db.execute(
            select(Student.id).where(
                Student.user_id == uuid.UUID(user.id),
                Student.school_id == school_id,
            )
        )
    ).first()
    if not row:
        return None, {
            "kind": "not_found",
            "title": "No student profile",
            "message": (
                "There's no student profile linked to your account. Please contact the school."
            ),
        }
    student_id = row[0]
    denied = await _authorize_student(db, user, student_id, noun="learning record")
    if denied:
        return None, denied
    return student_id, None


async def my_daily_plan(
    db: AsyncSession, user: CurrentUser, params: dict[str, Any]
) -> dict[str, Any]:
    """The authenticated student's deterministic daily learning plan (no LLM, no credits)."""
    from app.modules.tutor.services.student_copilot_service import StudentCopilotService

    student_id, block = await _resolve_self_student_id(db, user)
    if block:
        return block
    school_id = uuid.UUID(user.school_id)
    plan = await StudentCopilotService(db).get_daily_plan(
        school_id=school_id, student_id=student_id
    )
    if plan.status != "ready":
        return {
            "kind": "guide",
            "title": "No learning action yet",
            "message": plan.reason,
            "suggestions": [{"label": "Open tutor", "href": "/student/tutor"}],
        }
    metrics = []
    if plan.mastery_pct is not None:
        metrics.append({"label": "Mastery", "value": plan.mastery_pct, "format": "percent"})
    metrics.append({"label": "Curriculum sources", "value": plan.source_count})
    return {
        "kind": "metrics",
        "title": plan.title,
        "subtitle": plan.topic,
        "source": "Learning / Mastery",
        "message": plan.reason,
        "metrics": metrics,
        "href": f"/student/tutor?lesson={plan.lesson_key}" if plan.lesson_key else "/student/tutor",
        "href_label": "Open lesson",
    }


async def my_weak_topics(
    db: AsyncSession, user: CurrentUser, params: dict[str, Any]
) -> dict[str, Any]:
    """Topics to revise + recommended lessons for the authenticated student."""
    from app.modules.tutor.services.tutor_service import list_recommendations

    student_id, block = await _resolve_self_student_id(db, user)
    if block:
        return block
    school_id = uuid.UUID(user.school_id)
    recs = await list_recommendations(db, school_id=school_id, student_id=student_id)
    rows = [
        {
            "topic": r.topic,
            "subject_name": r.subject_name,
            "mastery_pct": r.mastery_pct,
            "reason": r.reason,
        }
        for r in recs
    ]
    return {
        "kind": "table",
        "title": "Topics to improve",
        "source": "Learning / Mastery",
        "columns": [
            {"key": "subject_name", "label": "Subject"},
            {"key": "topic", "label": "Topic"},
            {"key": "mastery_pct", "label": "Mastery", "format": "percent"},
            {"key": "reason", "label": "Why"},
        ],
        "rows": rows,
        "empty_message": (
            "No weak topics are flagged right now — you're on track. Keep practising!"
        ),
        "href": "/student/tutor",
        "href_label": "Open tutor",
    }


async def my_lesson(
    db: AsyncSession, user: CurrentUser, params: dict[str, Any]
) -> dict[str, Any]:
    """A tutor lesson for the authenticated student — the named topic, or their top priority."""
    from app.modules.tutor.services.student_copilot_service import StudentCopilotService
    from app.modules.tutor.services.tutor_service import get_lesson

    student_id, block = await _resolve_self_student_id(db, user)
    if block:
        return block
    school_id = uuid.UUID(user.school_id)
    lesson_key = str(params.get("topic") or params.get("lesson_key") or "").strip()
    if not lesson_key:
        plan = await StudentCopilotService(db).get_daily_plan(
            school_id=school_id, student_id=student_id
        )
        lesson_key = plan.lesson_key or ""
    if not lesson_key:
        return {
            "kind": "guide",
            "title": "No lesson yet",
            "message": (
                "A lesson appears once an assessed topic creates mastery evidence. "
                "Ask your teacher which topic to revise first."
            ),
            "suggestions": [{"label": "Open tutor", "href": "/student/tutor"}],
        }
    lesson = await get_lesson(
        db, school_id=school_id, student_id=student_id, lesson_key=lesson_key
    )
    if lesson is None:
        return _not_found_block(lesson_key, "lesson")
    steps = "\n\n".join(
        f"{i}. {s.title} — {s.narration}" for i, s in enumerate(lesson.steps, start=1)
    )
    return {
        "kind": "document",
        "title": f"Lesson — {lesson.topic}",
        "message": steps or "This lesson has no steps yet.",
        "citations": [],
        "href": f"/student/tutor?lesson={lesson.lesson_key}",
        "href_label": "Open full lesson",
    }


async def ask_tutor(
    db: AsyncSession, user: CurrentUser, params: dict[str, Any]
) -> dict[str, Any]:
    """Grounded AI tutor answer for the authenticated student — METERED (reuses tutor service).

    Reuses StudentCopilotService.ask unchanged: it reserves one `tutor_explain` credit, runs
    the grounded LLM once, and finalizes the usage row (no double charge). This is the single
    metered student capability; the deterministic tools above cost no credits.
    """
    from app.modules.tutor.schemas.copilot import CopilotAskIn
    from app.modules.tutor.services.student_copilot_service import StudentCopilotService

    student_id, block = await _resolve_self_student_id(db, user)
    if block:
        return block
    school_id = uuid.UUID(user.school_id)
    question = str(params.get("question") or "").strip()
    if len(question) < 3:
        return {
            "kind": "clarify",
            "title": "What would you like help with?",
            "message": "Tell me the topic or question you'd like the tutor to explain.",
            "options": [],
        }
    try:
        ask_in = CopilotAskIn(question=question[:800])
    except Exception:  # noqa: BLE001 — invalid question text -> honest clarify, no charge
        return {
            "kind": "clarify",
            "title": "What would you like help with?",
            "message": "Please rephrase your question for the tutor.",
            "options": [],
        }
    try:
        answer = await StudentCopilotService(db).ask(
            school_id=school_id,
            student_id=student_id,
            body=ask_in,
            user_id=uuid.UUID(user.id),
            role=user.role,
        )
    except ValueError as exc:
        return {
            "kind": "guide",
            "title": "I need a bit more to go on",
            "message": str(exc),
            "suggestions": [{"label": "Open tutor", "href": "/student/tutor"}],
        }
    hints = "\n".join(f"• {h}" for h in answer.follow_up_hints)
    message = answer.answer + (f"\n\nTry next:\n{hints}" if hints else "")
    return {
        "kind": "document",
        "title": f"Tutor — {answer.concept_title}" if answer.concept_title else "Tutor",
        "message": message,
        "citations": [],
        "href": "/student/tutor",
        "href_label": "Open tutor",
    }
