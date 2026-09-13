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

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser
from app.db.models.academic import Class, Subject, TeacherSubjectMapping
from app.db.models.attendance import Attendance
from app.db.models.school_ops import StaffProfile
from app.db.models.student import Student
from app.db.models.user import User, UserRole
from app.modules.workspace.assistant.resolver import (
    Resolution,
    resolve_class,
    resolve_student,
    resolve_teacher,
)

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

    rng = params.get("_range")
    start = rng.start_date if rng and not rng.is_all_time else None
    end = rng.end_date if rng and not rng.is_all_time else None
    summary = await AttendanceService(db).student_summary_in_range(
        school_id, entity.id, start=start, end=end
    )
    total = summary["total"]
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
            {"label": "Attendance", "value": summary["percentage"], "format": "percent"},
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

    class_ids = [c.id for c in res.candidates]
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
    students = [
        {
            "name": name,
            "admission_no": adm,
            "roll_no": roll or "—",
            "class_label": f"{grade} {section}".strip(),
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
    summary = await AttendanceService(db).get_summary(school_id, cls.id, date.today())
    total = summary["total"]
    credited = summary["present"] + summary["late"] + summary["half_day"]
    pct = round(credited / total * 100, 1) if total else None
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
        class_filter_ids = [c.id for c in res.candidates]
        class_label = ", ".join(c.label for c in res.candidates)

    # Aggregate per-student attendance across all recorded days.
    credited_expr = func.sum(
        case(
            (Attendance.status.in_(["present", "late", "half_day"]), 1),
            else_=0,
        )
    )
    q = (
        select(
            Student.id,
            User.full_name,
            Student.admission_no,
            Class.grade,
            Class.section,
            func.count(Attendance.id).label("total"),
            credited_expr.label("credited"),
        )
        .join(User, User.id == Student.user_id)
        .join(Class, Class.id == Student.class_id)
        .join(Attendance, Attendance.student_id == Student.id)
        .where(Student.school_id == school_id)
        .group_by(Student.id, User.full_name, Student.admission_no, Class.grade, Class.section)
    )
    if class_filter_ids:
        q = q.where(Student.class_id.in_(class_filter_ids))

    rows = (await db.execute(q)).all()
    students = []
    for _sid, name, adm, grade, section, total, credited_count in rows:
        if not total:
            continue
        pct = round((credited_count or 0) / total * 100, 1)
        if pct < threshold:
            students.append(
                {
                    "name": name,
                    "admission_no": adm,
                    "class_label": f"{grade} {section}".strip(),
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

    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()

    # 1) Class incharges (homeroom / "Class Teacher") — Class.class_incharge_id.
    incharge_q = (
        select(User.full_name, Class.grade, Class.section)
        .join(Class, Class.class_incharge_id == User.id)
        .where(Class.school_id == school_id, Class.class_incharge_id.is_not(None))
    )
    if class_ids:
        incharge_q = incharge_q.where(Class.id.in_(class_ids))
    for full_name, grade, section in (await db.execute(incharge_q)).all():
        label = f"{grade} {section}".strip()
        key = (full_name, "Class Teacher", label)
        if key in seen:
            continue
        seen.add(key)
        rows.append({"name": full_name, "role": "Class Teacher", "class_label": label})

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
        label = f"{grade} {section}".strip()
        key = (full_name, subject_name, label)
        if key in seen:
            continue
        seen.add(key)
        rows.append({"name": full_name, "role": subject_name, "class_label": label})

    rows.sort(key=lambda r: (r["class_label"], r["role"] != "Class Teacher", r["name"]))
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
    rows: list[dict[str, Any]] = []

    # Homeroom classes.
    for grade, section in (
        await db.execute(
            select(Class.grade, Class.section).where(
                Class.school_id == school_id, Class.class_incharge_id == teacher.id
            )
        )
    ).all():
        rows.append(
            {"subject": "Class Teacher (homeroom)", "class_label": f"{grade} {section}".strip()}
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
        rows.append({"subject": subject_name, "class_label": f"{grade} {section}".strip()})

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
