"""Governed tool catalog for the agentic assistant.

Each tool wraps an existing deterministic, tenant-scoped service. The LLM planner
may only *choose* a tool and *extract params* — it never produces the data. Tools
enforce role access; the handler returns typed response blocks.

Adding a capability = add one AssistantTool here. No planner changes needed.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser
from app.modules.workspace.assistant import capabilities as cap

ToolHandler = Callable[[AsyncSession, CurrentUser, dict[str, Any]], Awaitable[dict[str, Any]]]


@dataclass(frozen=True)
class AssistantTool:
    name: str
    description: str
    # JSON-ish param spec shown to the planner: {param: "type — description"}.
    params: dict[str, str]
    roles: frozenset[str]
    handler: ToolHandler
    # Temporal contract for the historical-honesty guard:
    #   "event_time"     — filters dated transactional records; PAST ranges are supported
    #                      (fees, attendance).
    #   "current_state"  — reflects only the present relationship/state; the ERP has no
    #                      effective-dated history, so a PAST request cannot be answered
    #                      (teacher/class assignments, student's class, roster).
    #   "timeless"       — no temporal dimension (school overview).
    temporal_mode: str = "timeless"

    @property
    def supports_historical(self) -> bool:
        return self.temporal_mode == "event_time"

    def allowed_for(self, role: str) -> bool:
        return role in self.roles


_STAFF = frozenset({"admin", "super_admin", "class_incharge", "teacher", "operations"})
_ADMIN = frozenset({"admin", "super_admin"})

# Shared help so the planner emits a CANONICAL temporal token, never free text.
TIME_PARAM_HELP = (
    "string OR object, optional — time window. Use ONE canonical token: today, yesterday, "
    "this_week, last_week, this_month, last_month, this_year, last_year, "
    "current_academic_year, previous_academic_year, all_time. For a bare month name use "
    '{"month":"august"} (NEVER guess the year — the system fills it). For an explicit '
    'span use {"from":"YYYY-MM-DD","to":"YYYY-MM-DD"}. Map natural phrasing to these '
    "(e.g. \"today's collection\"->today, 'monthly attendance'->this_month, 'in August'->"
    '{"month":"august"}). Omit if no time is mentioned.'
)


# ── Handlers ─────────────────────────────────────────────────────────────────


async def _school_overview(
    db: AsyncSession, user: CurrentUser, params: dict[str, Any]
) -> dict[str, Any]:
    from app.core.staff_permissions import get_staff_scope
    from app.modules.dashboard.services.dashboard_service import DashboardService

    scope = await get_staff_scope(db, user)
    summary = await DashboardService(db).build_summary(
        uuid.UUID(user.school_id), scope, teacher_name=user.full_name or "Teacher"
    )
    return {
        "kind": "metrics",
        "title": "School overview",
        "source": "Student Information System",
        "metrics": [
            {"label": "Students", "value": summary.total_students},
            {"label": "Teachers", "value": summary.total_teachers},
            {"label": "Classes", "value": summary.total_classes},
            {
                "label": "Attendance today",
                "value": summary.school_attendance_percent,
                "format": "percent",
            },
        ],
        "href": "/dashboard/students",
        "href_label": "Open students",
    }


async def _fee_collection(
    db: AsyncSession, user: CurrentUser, params: dict[str, Any]
) -> dict[str, Any]:
    from app.modules.fees.services.fee_service import FeeService

    stats = await FeeService(db).get_fee_stats(uuid.UUID(user.school_id))
    return {
        "kind": "metrics",
        "title": "Fee collection",
        "source": "Fee System",
        "metrics": [
            {"label": "Collected", "value": stats["total_collected"], "format": "money"},
            {"label": "Pending", "value": stats["pending_amount"], "format": "money"},
            {"label": "Families with dues", "value": stats["pending_families"]},
        ],
        "href": "/dashboard/finance",
        "href_label": "Open finance",
    }


async def _students_fee_pending_over(
    db: AsyncSession, user: CurrentUser, params: dict[str, Any]
) -> dict[str, Any]:
    from app.modules.fees.services.fee_service import FeeService

    try:
        min_percent = float(params.get("min_percent", 50))
    except (TypeError, ValueError):
        min_percent = 50.0
    min_percent = min(max(min_percent, 0.0), 100.0)
    class_label = params.get("class_label") or None

    result = await FeeService(db).students_by_pending_percent(
        uuid.UUID(user.school_id), min_percent=min_percent, class_label=class_label
    )
    scope = f" in class {class_label}" if class_label else ""
    return {
        "kind": "table",
        "title": f"Students with fees pending over {min_percent:g}%{scope}",
        "source": "Fee System",
        "columns": [
            {"key": "name", "label": "Student"},
            {"key": "class_label", "label": "Class"},
            {"key": "total_due", "label": "Total due", "format": "money"},
            {"key": "pending_amount", "label": "Pending", "format": "money"},
            {"key": "pending_percent", "label": "Pending %", "format": "percent"},
        ],
        "rows": result["students"],
        "empty_message": f"No students have fees pending over {min_percent:g}%{scope}.",
        "href": "/dashboard/finance",
        "href_label": "Open finance",
    }


# ── Catalog ──────────────────────────────────────────────────────────────────

ASSISTANT_TOOLS: tuple[AssistantTool, ...] = (
    AssistantTool(
        name="school_overview",
        description="Total counts of students, teachers, classes and today's attendance %.",
        params={},
        roles=_STAFF,
        handler=_school_overview,
    ),
    AssistantTool(
        name="fee_collection",
        description="School-wide fee totals: collected, pending, families with dues.",
        params={},
        roles=_ADMIN,
        handler=_fee_collection,
    ),
    AssistantTool(
        name="students_fee_pending_over",
        description=(
            "List students whose unpaid fee share exceeds a percentage. Use for "
            "questions like 'students with fees pending > 50%' or 'fee defaulters in "
            "class 10'. Returns a table."
        ),
        params={
            "min_percent": "number — pending percentage threshold (default 50)",
            "class_label": "string, optional — narrow to one class, e.g. '10' or 'Class 10 A'",
        },
        roles=_ADMIN,
        handler=_students_fee_pending_over,
    ),
    AssistantTool(
        name="teachers_for_class",
        description=(
            "List teachers assigned to classes — BOTH the class teacher (homeroom/incharge) "
            "and subject teachers. Use for 'who is the class teacher of 2A', 'which teachers "
            "take class 10 B', and 'list all teachers and their classes' (omit class_label "
            "for everyone). Returns a table."
        ),
        params={
            "class_label": (
                "string, optional — a class like '2A' or 'Class 10 B'. Omit to list "
                "all teachers and their classes."
            ),
            "time": TIME_PARAM_HELP,
        },
        roles=_STAFF,
        handler=cap.teachers_for_class,
        temporal_mode="current_state",
    ),
    AssistantTool(
        name="teacher_assignments",
        description=(
            "What one teacher teaches: their subjects, classes, and any homeroom class. "
            "Use for 'what subjects does Deepak Kumar teach', 'which classes does X handle'."
        ),
        params={
            "teacher": "string — teacher name or employee ID, e.g. 'Deepak Kumar'",
            "time": TIME_PARAM_HELP,
        },
        roles=_STAFF,
        handler=cap.teacher_assignments,
        temporal_mode="current_state",
    ),
    AssistantTool(
        name="staff_directory",
        description=(
            "List staff members, optionally filtered by department. Use for 'list all staff', "
            "'teachers in Science department'."
        ),
        params={"department": "string, optional — filter by department name"},
        roles=_STAFF,
        handler=cap.staff_directory,
    ),
    AssistantTool(
        name="student_attendance",
        description=(
            "Attendance percentage and present/absent breakdown for ONE student. Use for "
            "'attendance % of ARM0218', 'ARM0218 attendance this month', 'how many days was "
            "Aarav absent'. Resolves the student by admission number, roll number, or name."
        ),
        params={
            "student": "string — admission no (e.g. 'ARM0218'), roll no, or student name",
            "time": TIME_PARAM_HELP,
        },
        roles=_STAFF,
        handler=cap.student_attendance,
        temporal_mode="event_time",
    ),
    AssistantTool(
        name="fee_collection_period",
        description=(
            "Total fee collected within a time window. Use for 'fee collected today', "
            "\"this month's fee collection\", 'fee collected between Aug 1 and Aug 31'. "
            "For overall school fee status (pending, families with dues) use fee_collection."
        ),
        params={"time": TIME_PARAM_HELP},
        roles=_ADMIN,
        handler=cap.fee_collection_period,
        temporal_mode="event_time",
    ),
    AssistantTool(
        name="student_profile",
        description=(
            "Snapshot of one student: current class, attendance %, fee pending/paid. Use for "
            "'show me ARM0218', 'profile of Aarav Sharma', 'which class is ARM0218 in'."
        ),
        params={
            "student": "string — admission no, roll no, or student name",
            "time": TIME_PARAM_HELP,
        },
        roles=_STAFF,
        handler=cap.student_profile,
        temporal_mode="current_state",
    ),
    AssistantTool(
        name="student_fees",
        description=(
            "Fee balance (total/paid/pending) for ONE student. Use for 'fee balance of "
            "ARM0218', 'how much does Aarav owe'."
        ),
        params={"student": "string — admission no, roll no, or student name"},
        roles=_ADMIN,
        handler=cap.student_fees,
    ),
    AssistantTool(
        name="class_roster",
        description=(
            "List the students enrolled in a class. Use for 'students in 2A', 'class 10 B "
            "roster'."
        ),
        params={
            "class_label": "string — a class like '2A' or 'Class 10 B'",
            "time": TIME_PARAM_HELP,
        },
        roles=_STAFF,
        handler=cap.class_roster,
        temporal_mode="current_state",
    ),
    AssistantTool(
        name="class_attendance_today",
        description=(
            "Today's attendance summary for a class (present/absent/%). Use for 'how many "
            "students are absent today in 5A', 'attendance of class 2A today'."
        ),
        params={"class_label": "string — a class like '5A' or 'Class 2 A'"},
        roles=_STAFF,
        handler=cap.class_attendance_today,
    ),
    AssistantTool(
        name="low_attendance_students",
        description=(
            "Students below an attendance percentage threshold (default 75%), optionally in "
            "one class. Use for 'students with attendance below 75%', 'low attendance in 8A'."
        ),
        params={
            "below_percent": "number — attendance threshold (default 75)",
            "class_label": "string, optional — narrow to one class",
        },
        roles=_STAFF,
        handler=cap.low_attendance_students,
    ),
)


def tools_for_role(role: str) -> list[AssistantTool]:
    return [t for t in ASSISTANT_TOOLS if t.allowed_for(role)]


def get_tool(name: str) -> AssistantTool | None:
    for t in ASSISTANT_TOOLS:
        if t.name == name:
            return t
    return None
