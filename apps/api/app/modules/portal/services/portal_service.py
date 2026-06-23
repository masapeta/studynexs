"""Portal context — role-aware home data for parent, student, and teacher apps."""
from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.academic import Class
from app.db.models.attendance import Attendance, AttendanceStatus
from app.db.models.fee import StudentFeeRecord
from app.db.models.mastery import StudentTopicMastery
from app.db.models.student import Parent, Student, StudentParentMap
from app.db.models.user import User
from app.modules.portal.schemas.portal import ChildSummaryOut, FeatureTeaserOut, PortalContextOut

_WEAK_THRESHOLD = 70.0


def resolve_portal(role: str) -> str:
    if role in ("admin", "super_admin", "operations"):
        return "staff"
    if role in ("teacher", "class_incharge"):
        return "teacher"
    if role == "parent":
        return "parent"
    if role == "student":
        return "student"
    return "staff"


async def _attendance_pct(db: AsyncSession, school_id: uuid.UUID, student_id: uuid.UUID) -> float | None:
    rows = (
        await db.execute(
            select(Attendance.status, func.count())
            .where(Attendance.school_id == school_id, Attendance.student_id == student_id)
            .group_by(Attendance.status)
        )
    ).all()
    if not rows:
        return None
    counts = {(s.value if hasattr(s, "value") else str(s)): c for s, c in rows}
    total = sum(counts.values())
    credited = counts.get("present", 0) + counts.get("late", 0) + counts.get("half_day", 0) * 0.5
    return round(credited / total * 100, 1) if total else None


async def _fee_pending(db: AsyncSession, school_id: uuid.UUID, student_id: uuid.UUID) -> float:
    row = (
        await db.execute(
            select(
                func.coalesce(func.sum(StudentFeeRecord.amount), 0),
                func.coalesce(func.sum(StudentFeeRecord.paid_amount), 0),
            ).where(
                StudentFeeRecord.school_id == school_id,
                StudentFeeRecord.student_id == student_id,
            )
        )
    ).first()
    if not row:
        return 0.0
    return round(max(0.0, float(row[0] or 0) - float(row[1] or 0)), 2)


async def _weak_topic_count(db: AsyncSession, school_id: uuid.UUID, student_id: uuid.UUID) -> int:
    result = await db.execute(
        select(func.count())
        .select_from(StudentTopicMastery)
        .where(
            StudentTopicMastery.school_id == school_id,
            StudentTopicMastery.student_id == student_id,
            StudentTopicMastery.mastery_pct < _WEAK_THRESHOLD,
        )
    )
    return int(result.scalar_one() or 0)


async def _child_summary(
    db: AsyncSession, school_id: uuid.UUID, student: Student, user: User | None, cls: Class | None
) -> ChildSummaryOut:
    return ChildSummaryOut(
        student_id=student.id,
        name=user.full_name if user else "Student",
        class_label=f"{cls.grade} - {cls.section}" if cls else "—",
        roll_no=student.roll_no,
        attendance_pct=await _attendance_pct(db, school_id, student.id),
        fee_pending=await _fee_pending(db, school_id, student.id),
        weak_topic_count=await _weak_topic_count(db, school_id, student.id),
    )


async def build_portal_context(
    db: AsyncSession, *, school_id: uuid.UUID, user_id: uuid.UUID, role: str
) -> PortalContextOut:
    portal = resolve_portal(role)

    if role == "parent":
        rows = (
            await db.execute(
                select(Student, User, Class)
                .join(StudentParentMap, StudentParentMap.student_id == Student.id)
                .join(Parent, Parent.id == StudentParentMap.parent_id)
                .join(User, User.id == Student.user_id)
                .join(Class, Class.id == Student.class_id)
                .where(
                    Parent.user_id == user_id,
                    Parent.school_id == school_id,
                    Student.school_id == school_id,
                )
                .order_by(Student.roll_no)
            )
        ).all()
        children = [
            await _child_summary(db, school_id, stu, u, cls) for stu, u, cls in rows
        ]
        return PortalContextOut(portal=portal, role=role, children=children)

    if role == "student":
        row = (
            await db.execute(
                select(Student, User, Class)
                .join(User, User.id == Student.user_id)
                .join(Class, Class.id == Student.class_id)
                .where(Student.user_id == user_id, Student.school_id == school_id)
            )
        ).first()
        if not row:
            return PortalContextOut(portal=portal, role=role)
        stu, u, cls = row
        summary = await _child_summary(db, school_id, stu, u, cls)
        return PortalContextOut(
            portal=portal,
            role=role,
            student_id=stu.id,
            student_name=summary.name,
            class_label=summary.class_label,
            children=[summary],
        )

    return PortalContextOut(portal=portal, role=role)


PRODUCT_FEATURES: list[FeatureTeaserOut] = [
    FeatureTeaserOut(
        id="ai_papers",
        title="AI Question Papers",
        description="Generate and approve board-style papers in minutes.",
        status="live",
        href="/dashboard/ai-papers",
    ),
    FeatureTeaserOut(
        id="answer_eval",
        title="Answer Sheet Evaluation",
        description="Snap, AI-grade, teacher approves — marks flow to reports.",
        status="live",
        href="/dashboard/exams",
    ),
    FeatureTeaserOut(
        id="mastery",
        title="Topic Mastery",
        description="See weak concepts from real exam data.",
        status="live",
        href="/dashboard/mastery",
    ),
    FeatureTeaserOut(
        id="report_cards",
        title="AI Report Cards",
        description="Draft remarks teachers approve before sharing.",
        status="live",
        href="/dashboard/report-cards",
    ),
    FeatureTeaserOut(
        id="parent_feed",
        title="Parent Progress Feed",
        description="Weekly AI summaries and weak-concept alerts.",
        status="live",
        href="/parent",
    ),
    FeatureTeaserOut(
        id="tutor",
        title="Mistake Recovery Tutor",
        description="Voice + visuals — teacher explains your exam mistakes; pause & replay.",
        status="live",
        href="/student/tutor",
    ),
    FeatureTeaserOut(
        id="whatsapp",
        title="WhatsApp Alerts",
        description="Fee reminders and result notifications.",
        status="preview",
    ),
]
