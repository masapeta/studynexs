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
