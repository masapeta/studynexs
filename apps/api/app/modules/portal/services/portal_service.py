"""Portal context — role-aware home data for parent, student, and teacher apps."""
from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.academic import Class, Subject
from app.db.models.attendance import Attendance, AttendanceStatus
from app.db.models.fee import FeeStructure, StudentFeeRecord
from app.db.models.mastery import FlagStatus, MasteryFlag, StudentTopicMastery
from app.db.models.student import Parent, Student, StudentParentMap
from app.db.models.user import User
from app.modules.portal.schemas.portal import (
    ChildSummaryOut,
    FeatureTeaserOut,
    FeeRecordSummaryOut,
    ParentChildFeesOut,
    ParentChildProgressOut,
    ParentFeedbackOut,
    ParentWeakTopicOut,
    PortalContextOut,
)

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


async def parent_child_summary(
    db: AsyncSession, *, school_id: uuid.UUID, student_id: uuid.UUID
) -> ChildSummaryOut | None:
    row = (
        await db.execute(
            select(Student, User, Class)
            .join(User, User.id == Student.user_id)
            .join(Class, Class.id == Student.class_id)
            .where(Student.id == student_id, Student.school_id == school_id)
        )
    ).first()
    if not row:
        return None
    stu, user, cls = row
    return await _child_summary(db, school_id, stu, user, cls)


async def list_parent_children_fees(
    db: AsyncSession, *, school_id: uuid.UUID, parent_user_id: uuid.UUID
) -> list[ParentChildFeesOut]:
    children_rows = (
        await db.execute(
            select(Student, User)
            .join(StudentParentMap, StudentParentMap.student_id == Student.id)
            .join(Parent, Parent.id == StudentParentMap.parent_id)
            .join(User, User.id == Student.user_id)
            .where(
                Parent.user_id == parent_user_id,
                Parent.school_id == school_id,
                Student.school_id == school_id,
            )
            .order_by(Student.roll_no)
        )
    ).all()
    if not children_rows:
        return []

    child_map = {stu.id: (stu, user) for stu, user in children_rows}
    student_ids = list(child_map.keys())
    fee_rows = (
        await db.execute(
            select(StudentFeeRecord, FeeStructure)
            .join(
                FeeStructure,
                FeeStructure.id == StudentFeeRecord.fee_structure_id,
            )
            .where(
                StudentFeeRecord.school_id == school_id,
                StudentFeeRecord.student_id.in_(student_ids),
            )
            .order_by(StudentFeeRecord.due_date.desc())
        )
    ).all()

    grouped: dict[uuid.UUID, list[FeeRecordSummaryOut]] = {sid: [] for sid in student_ids}
    for record, structure in fee_rows:
        fee_type = structure.fee_type.value if hasattr(structure.fee_type, "value") else str(structure.fee_type)
        grouped[record.student_id].append(
            FeeRecordSummaryOut(
                id=record.id,
                fee_type=fee_type,
                amount=float(record.amount),
                status=record.status.value if hasattr(record.status, "value") else str(record.status),
                due_date=record.due_date.isoformat() if record.due_date else None,
            )
        )

    return [
        ParentChildFeesOut(
            student_id=stu.id,
            name=user.full_name if user else "Student",
            records=grouped.get(stu.id, []),
        )
        for stu, user in children_rows
    ]


async def _parent_linked_children(
    db: AsyncSession, *, school_id: uuid.UUID, parent_user_id: uuid.UUID
) -> list[tuple[Student, User, Class]]:
    rows = (
        await db.execute(
            select(Student, User, Class)
            .join(StudentParentMap, StudentParentMap.student_id == Student.id)
            .join(Parent, Parent.id == StudentParentMap.parent_id)
            .join(User, User.id == Student.user_id)
            .join(Class, Class.id == Student.class_id)
            .where(
                Parent.user_id == parent_user_id,
                Parent.school_id == school_id,
                Student.school_id == school_id,
            )
            .order_by(Student.roll_no)
        )
    ).all()
    return list(rows)


async def _build_parent_child_progress(
    db: AsyncSession,
    *,
    school_id: uuid.UUID,
    student: Student,
    user: User,
    cls: Class,
    weak_by_student: dict[uuid.UUID, list[ParentWeakTopicOut]],
    feedback_by_student: dict[uuid.UUID, list[ParentFeedbackOut]],
) -> ParentChildProgressOut:
    summary = await _child_summary(db, school_id, student, user, cls)
    weak_topics = weak_by_student.get(student.id, [])
    return ParentChildProgressOut(
        student_id=student.id,
        name=summary.name,
        class_label=summary.class_label,
        roll_no=summary.roll_no,
        attendance_pct=summary.attendance_pct,
        fee_pending=summary.fee_pending,
        weak_topic_count=summary.weak_topic_count,
        weak_topics=weak_topics,
        feedbacks=feedback_by_student.get(student.id, []),
    )


async def list_parent_children_progress(
    db: AsyncSession, *, school_id: uuid.UUID, parent_user_id: uuid.UUID
) -> list[ParentChildProgressOut]:
    children_rows = await _parent_linked_children(db, school_id=school_id, parent_user_id=parent_user_id)
    if not children_rows:
        return []

    student_ids = [stu.id for stu, _, _ in children_rows]
    weak_by_student: dict[uuid.UUID, list[ParentWeakTopicOut]] = {sid: [] for sid in student_ids}
    mastery_rows = (
        await db.execute(
            select(StudentTopicMastery, Subject.name)
            .join(Subject, Subject.id == StudentTopicMastery.subject_id)
            .where(
                StudentTopicMastery.school_id == school_id,
                StudentTopicMastery.student_id.in_(student_ids),
                StudentTopicMastery.mastery_pct < _WEAK_THRESHOLD,
            )
            .order_by(StudentTopicMastery.mastery_pct)
        )
    ).all()
    for stm, subject_name in mastery_rows:
        weak_by_student[stm.student_id].append(
            ParentWeakTopicOut(
                subject_name=subject_name,
                topic=stm.topic,
                topic_display=stm.topic_display,
                mastery_pct=float(stm.mastery_pct),
            )
        )

    feedback_by_student: dict[uuid.UUID, list[ParentFeedbackOut]] = {sid: [] for sid in student_ids}
    flag_rows = (
        await db.execute(
            select(MasteryFlag, Subject.name)
            .join(Subject, Subject.id == MasteryFlag.subject_id)
            .where(
                MasteryFlag.school_id == school_id,
                MasteryFlag.student_id.in_(student_ids),
                MasteryFlag.status == FlagStatus.NOTIFIED,
                MasteryFlag.narrative.isnot(None),
            )
            .order_by(MasteryFlag.notified_at.desc())
        )
    ).all()
    for flag, subject_name in flag_rows:
        feedback_by_student[flag.student_id].append(
            ParentFeedbackOut(
                topic=flag.topic,
                topic_display=flag.topic_display,
                subject_name=subject_name,
                narrative=flag.narrative or "",
                notified_at=flag.notified_at.isoformat() if flag.notified_at else None,
            )
        )

    return [
        await _build_parent_child_progress(
            db,
            school_id=school_id,
            student=stu,
            user=user,
            cls=cls,
            weak_by_student=weak_by_student,
            feedback_by_student=feedback_by_student,
        )
        for stu, user, cls in children_rows
    ]


async def parent_child_progress(
    db: AsyncSession, *, school_id: uuid.UUID, parent_user_id: uuid.UUID, student_id: uuid.UUID
) -> ParentChildProgressOut | None:
    children = await list_parent_children_progress(
        db, school_id=school_id, parent_user_id=parent_user_id
    )
    for child in children:
        if child.student_id == student_id:
            return child
    return None


PRODUCT_FEATURES: list[FeatureTeaserOut] = [
    FeatureTeaserOut(
        id="ai_papers",
        title="AI Question Papers",
        description="Generate and approve board-style papers in minutes.",
        status="live",
        href="/dashboard/ai-papers",
        audiences=["staff"],
    ),
    FeatureTeaserOut(
        id="answer_eval",
        title="Answer Sheet Evaluation",
        description="Snap, AI-grade, teacher approves — marks flow to reports.",
        status="live",
        href="/dashboard/exams",
        audiences=["staff"],
    ),
    FeatureTeaserOut(
        id="mastery",
        title="Topic Mastery",
        description="See weak concepts from real exam data.",
        status="live",
        href="/dashboard/mastery",
        audiences=["staff"],
    ),
    FeatureTeaserOut(
        id="report_cards",
        title="AI Report Cards",
        description="Draft remarks teachers approve before sharing.",
        status="live",
        href="/dashboard/report-cards",
        audiences=["staff"],
    ),
    FeatureTeaserOut(
        id="parent_feed",
        title="Parent Progress Feed",
        description="Weekly AI summaries and weak-concept alerts.",
        status="live",
        href="/parent",
        audiences=["staff", "parent"],
    ),
    FeatureTeaserOut(
        id="tutor",
        title="Mistake Recovery Tutor",
        description="Voice + visuals — teacher explains your exam mistakes; pause & replay.",
        status="live",
        href="/student/tutor",
        audiences=["staff", "student"],
    ),
    FeatureTeaserOut(
        id="whatsapp",
        title="WhatsApp Alerts",
        description="Fee reminders and result notifications.",
        status="preview",
        audiences=["staff", "parent", "student"],
    ),
]


def _audience_for_role(role: str) -> str:
    """Collapse a role into a teaser audience bucket."""
    if role == "parent":
        return "parent"
    if role == "student":
        return "student"
    return "staff"  # teacher / class_incharge / admin / super_admin / operations


def features_for_role(role: str) -> list[FeatureTeaserOut]:
    """Roadmap teasers a given role may see — keeps staff-only features out of the
    parent/student apps (a parent must not get an 'Open' link to a teacher page)."""
    audience = _audience_for_role(role)
    return [f for f in PRODUCT_FEATURES if audience in f.audiences]
