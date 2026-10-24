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
    # Coarse catalog gate: which roles even SEE this tool in the planner catalog. This is a
    # runtime/UI concern, NOT the authoritative authorization — object-level access is enforced
    # server-side inside each capability (P1.1 _authorize_* + get_staff_scope). Kept here, not
    # derived from the contract's `scope`, because `scope` is the object-access shape (student/
    # class/school) while `roles` is which role strings may route to the tool at all.
    roles: frozenset[str]
    handler: ToolHandler

    @property
    def temporal_mode(self) -> str:
        """The temporal contract, read from the single semantic source (CapabilityContract).

        "event_time" (dated records; PAST supported) / "current_state" (present-only; the ERP
        has no effective-dated history, so PAST is refused) / "timeless" (no time dimension).
        No longer declared on the tool — that was a duplicate of the contract (spec §1, §2).
        """
        from app.modules.workspace.assistant.contracts import get_contract

        c = get_contract(self.name)
        return c.temporal_mode if c else "timeless"

    @property
    def supports_historical(self) -> bool:
        return self.temporal_mode == "event_time"

    def allowed_for(self, role: str) -> bool:
        return role in self.roles


_STAFF = frozenset({"admin", "super_admin", "class_incharge", "teacher", "operations"})
_ADMIN = frozenset({"admin", "super_admin"})
_PARENT = frozenset({"parent"})
_STUDENT = frozenset({"student"})

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
    ),
    AssistantTool(
        name="class_attendance_today",
        description=(
            "Today's attendance for ONE NAMED CLASS (present/absent/%). Requires a class. Use for "
            "'how many students are absent today in 5A', 'attendance of class 2A today'. For the "
            "WHOLE school (no class named) use school_attendance instead."
        ),
        params={"class_label": "string — a class like '5A' or 'Class 2 A'"},
        roles=_STAFF,
        handler=cap.class_attendance_today,
    ),
    AssistantTool(
        name="school_attendance",
        description=(
            "WHOLE-SCHOOL attendance for a single day (default today): overall attendance %, "
            "present, absent, late across every class. Use when NO class is named — 'show today's "
            "school attendance', 'what's the school attendance today', 'overall attendance'. NOT "
            "for one class (use class_attendance_today) and NOT the student/teacher/class counts "
            "overview (use school_overview)."
        ),
        params={"time": TIME_PARAM_HELP},
        roles=_ADMIN,
        handler=cap.school_attendance,
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
    AssistantTool(
        name="student_marks",
        description=(
            "Exam marks for ONE student — every subject, or a single subject if named. Shows "
            "marks obtained, out-of, percentage of total, and the recorded grade letter (if "
            "any) per exam. Use for 'ARM0218 marks', 'how did Aarav do in Science', 'show "
            "exam results for roll 12'. Does NOT judge pass/fail (the ERP has no pass mark)."
        ),
        params={
            "student": "string — admission no, roll no, or student name",
            "subject": "string, optional — a subject like 'Mathematics' or 'Science'",
        },
        roles=_STAFF,
        handler=cap.student_marks,
    ),
    AssistantTool(
        name="student_learning_evidence",
        description=(
            "LEARNING EVIDENCE for ONE student: trace a flagged WEAK TOPIC back to the "
            "assessments, question papers and evaluations that produced it, with topic mastery "
            "and whether it's curriculum-grounded. Use for 'show learning evidence for Aarav', "
            "'why is ARM0218 weak in fractions', 'evidence for a student in my class'. This is "
            "the audit trail behind a weakness — NOT raw exam marks (student_marks), NOT the "
            "mastery heatmap, NOT a profile snapshot (student_profile)."
        ),
        params={"student": "string — admission no, roll no, or student name"},
        roles=_STAFF,
        handler=cap.student_learning_evidence,
    ),
    AssistantTool(
        name="class_results",
        description=(
            "Results matrix for a CLASS — each student's marks across subjects (latest exam "
            "per subject) plus an average %. Supports ranking: pass top/bottom + a limit for "
            "'top 5 students in 10A', 'class 9 rank list', 'who are the lowest performers in "
            "8B'. Average = mean of per-subject percentages."
        ),
        params={
            "class_label": "string — a class like '10A' or 'Class 9 B'",
            "top": "number, optional — return the top N students by average",
            "bottom": "number, optional — return the bottom N students by average",
        },
        roles=_STAFF,
        handler=cap.class_results,
    ),
    AssistantTool(
        name="subject_toppers",
        description=(
            "Ranking within a CLASS + SUBJECT for its latest exam. Use for 'top scorers in "
            "Maths in 10A', 'who scored highest in Science in 9B', 'lowest marks in English "
            "in 8A'. Ranks students by marks obtained in that one exam."
        ),
        params={
            "class_label": "string — a class like '10A'",
            "subject": "string — a subject like 'Mathematics'",
            "top": "number, optional — top N by marks (default: all, highest first)",
            "bottom": "number, optional — bottom N by marks",
        },
        roles=_STAFF,
        handler=cap.subject_toppers,
    ),
    # ── Parent capabilities (Milestone 1) — a parent's OWN linked children only ──
    AssistantTool(
        name="my_children_overview",
        description=(
            "Overview of the parent's own linked children: each child's class, attendance, "
            "fee pending, and weak-topic count. Use for 'show my children', 'how are my kids "
            "doing', 'overview of my children's progress'. Returns a table."
        ),
        params={},
        roles=_PARENT,
        handler=cap.my_children_overview,
    ),
    AssistantTool(
        name="my_child_attendance",
        description=(
            "Attendance for ONE of the parent's own children. Use for 'my child's attendance', "
            "'how is Aarav's attendance', 'is my daughter attending regularly'. If the parent "
            "has more than one child and none is named, the system asks which child."
        ),
        params={
            "child": (
                "string, optional — which child (first name or class, e.g. 'Aarav' or '5A'). "
                "Omit if the parent has one child."
            ),
        },
        roles=_PARENT,
        handler=cap.my_child_attendance,
    ),
    AssistantTool(
        name="my_child_progress",
        description=(
            "Academic progress and topics to improve (weak topics) for ONE of the parent's own "
            "children. Use for 'which subjects need improvement', 'my child's weak topics', "
            "'how is my son doing in studies'. Returns a table of subjects and topics."
        ),
        params={
            "child": "string, optional — which child (first name or class). Omit if only one.",
        },
        roles=_PARENT,
        handler=cap.my_child_progress,
    ),
    AssistantTool(
        name="my_child_fees",
        description=(
            "Fees and payment status for ONE of the parent's own children. Use for 'what fees "
            "are due', 'my child's fee status', 'how much do I owe'. Returns a table of fee "
            "records with amount, status, and due date."
        ),
        params={
            "child": "string, optional — which child (first name or class). Omit if only one.",
        },
        roles=_PARENT,
        handler=cap.my_child_fees,
    ),
    # ── Student capabilities (Milestone 2) — the authenticated student's own learning ──
    AssistantTool(
        name="my_daily_plan",
        description=(
            "The student's own 'study this today' plan — the recommended topic and lesson from "
            "their mastery evidence. Use for 'what should I study today', 'help me revise today', "
            "'my learning plan'. Deterministic (no AI generation)."
        ),
        params={},
        roles=_STUDENT,
        handler=cap.my_daily_plan,
    ),
    AssistantTool(
        name="my_weak_topics",
        description=(
            "The student's own weak topics and recommended lessons. Use for 'which topics am I "
            "weak in', 'what should I improve', 'show my recommended lessons', 'help me improve "
            "in Mathematics'. Returns a table. Deterministic (no AI generation)."
        ),
        params={},
        roles=_STUDENT,
        handler=cap.my_weak_topics,
    ),
    AssistantTool(
        name="my_lesson",
        description=(
            "Open a tutor lesson for the student — a named topic, or their top-priority topic if "
            "none is named. Use for 'explain my weakest topic', 'show me the fractions lesson', "
            "'teach me today's topic'. Returns the lesson steps. Deterministic (no AI generation)."
        ),
        params={
            "topic": (
                "string, optional — a topic or lesson key (e.g. 'fractions'). Omit for the "
                "student's top-priority lesson."
            ),
        },
        roles=_STUDENT,
        handler=cap.my_lesson,
    ),
    AssistantTool(
        name="ask_tutor",
        description=(
            "Ask the AI tutor a study question, answered with the student's own curriculum "
            "context. Use for open questions like 'explain photosynthesis', 'why is my answer "
            "wrong', 'help me understand fractions'. This uses AI and consumes one tutor credit."
        ),
        params={
            "question": "string — the student's study question (3-800 characters)",
        },
        roles=_STUDENT,
        handler=cap.ask_tutor,
    ),
)


def tools_for_role(role: str) -> list[AssistantTool]:
    return [t for t in ASSISTANT_TOOLS if t.allowed_for(role)]


def get_tool(name: str) -> AssistantTool | None:
    for t in ASSISTANT_TOOLS:
        if t.name == name:
            return t
    return None
