"""Teacher daily command center — scoped to assigned classes/subjects only."""
from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import date, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.staff_permissions import StaffScope
from app.db.models.academic import Class, Subject
from app.db.models.attendance import Attendance
from app.db.models.communication import NoticeAudience, NoticeReadReceipt
from app.db.models.lesson_plan import LessonPlan, LessonPlanStatus
from app.db.models.mastery import FlagStatus, MasteryFlag, StudentTopicMastery
from app.db.models.question_paper import (
    _INCHARGE_REVIEW_STATUSES,
    _TEACHER_SUBMIT_STATUSES,
    QuestionPaper,
)
from app.db.models.student import Student
from app.db.models.timetable import DayOfWeek, TimetableSlot
from app.db.models.user import User
from app.modules.curriculum.services.lesson_plan_service import LessonPlanService
from app.modules.dashboard.schemas.teacher_home import (
    DashboardActionOut,
    LessonPlanPreviewOut,
    LessonPlanSegmentOut,
    PendingWorkOut,
    StudentAttentionOut,
    SubjectProgressOut,
    TeacherCommandCenterOut,
    TeacherNoticeOut,
    TimetableDayOut,
    TimetableSlotBriefOut,
    TodayClassOut,
)

_WEEKDAY_TO_DAY = {
    0: DayOfWeek.MONDAY,
    1: DayOfWeek.TUESDAY,
    2: DayOfWeek.WEDNESDAY,
    3: DayOfWeek.THURSDAY,
    4: DayOfWeek.FRIDAY,
    5: DayOfWeek.SATURDAY,
}

_DAY_LABEL = {
    DayOfWeek.MONDAY: "Mon",
    DayOfWeek.TUESDAY: "Tue",
    DayOfWeek.WEDNESDAY: "Wed",
    DayOfWeek.THURSDAY: "Thu",
    DayOfWeek.FRIDAY: "Fri",
    DayOfWeek.SATURDAY: "Sat",
}

_DEFAULT_LESSON_SEGMENTS = [
    LessonPlanSegmentOut(duration_min=5, activity="Recap previous topic"),
    LessonPlanSegmentOut(duration_min=12, activity="Concept explanation"),
    LessonPlanSegmentOut(duration_min=8, activity="Class activity / demo"),
    LessonPlanSegmentOut(duration_min=10, activity="Practice questions"),
    LessonPlanSegmentOut(duration_min=5, activity="Exit quiz"),
]


class TeacherHomeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def build(
        self,
        school_id: uuid.UUID,
        scope: StaffScope,
        teacher_name: str,
    ) -> TeacherCommandCenterOut:
        if not scope.teaching_pairs:
            return TeacherCommandCenterOut(
                greeting=f"Hello, {teacher_name.split()[0]}",
                tagline="No subject assignments yet — contact your principal.",
            )

        today = date.today()
        teaching_pairs = scope.teaching_pairs
        class_ids = {cid for cid, _ in teaching_pairs}
        subject_ids = {sid for _, sid in teaching_pairs}

        classes = {
            c.id: c
            for c in (
                await self.db.execute(
                    select(Class).where(Class.school_id == school_id, Class.id.in_(class_ids))
                )
            ).scalars().all()
        }
        subjects = {
            s.id: s
            for s in (
                await self.db.execute(
                    select(Subject).where(
                        Subject.school_id == school_id,
                        Subject.id.in_(subject_ids),
                    )
                )
            ).scalars().all()
        }

        today_day = _WEEKDAY_TO_DAY.get(today.weekday())
        today_classes = await self._today_classes(
            school_id, scope, today, today_day, classes, subjects
        )
        weekly = await self._weekly_timetable(school_id, scope.user_id, classes, subjects)
        progress = await self._subject_progress(
            school_id, teaching_pairs, classes, subjects
        )
        pending = await self._pending_work(school_id, scope, teaching_pairs)
        lesson_plan = await self._load_lesson_plan(
            school_id, scope, classes, subjects, progress
        )
        staff_notices, school_notices = await self._notices(
            school_id, scope
        )
        greeting_period = "morning" if datetime.now().hour < 12 else "afternoon"

        return TeacherCommandCenterOut(
            greeting=f"Good {greeting_period}, {teacher_name.split()[0]}",
            today_classes=today_classes,
            pending_work=pending,
            lesson_plan=lesson_plan,
            weekly_timetable=weekly,
            subject_progress=progress,
            staff_notices=staff_notices,
            school_notices=school_notices,
        )

    async def _today_classes(
        self,
        school_id: uuid.UUID,
        scope: StaffScope,
        today: date,
        today_day: DayOfWeek | None,
        classes: dict[uuid.UUID, Class],
        subjects: dict[uuid.UUID, Subject],
    ) -> list[TodayClassOut]:
        if today_day is None:
            return []

        rows = (
            await self.db.execute(
                select(TimetableSlot)
                .where(
                    TimetableSlot.school_id == school_id,
                    TimetableSlot.teacher_id == scope.user_id,
                    TimetableSlot.day_of_week == today_day,
                )
                .order_by(TimetableSlot.start_time)
            )
        ).scalars().all()

        cards: list[TodayClassOut] = []
        for slot in rows:
            if (slot.class_id, slot.subject_id) not in scope.teaching_pairs:
                continue
            cls = classes.get(slot.class_id)
            subj = subjects.get(slot.subject_id)
            if not cls or not subj:
                continue

            att_status = await self._attendance_status(school_id, scope, slot.class_id, today)
            weak_topic = await self._weakest_topic(school_id, slot.class_id, slot.subject_id)
            can_attend = scope.is_class_incharge(slot.class_id)
            actions: list[DashboardActionOut] = [
                DashboardActionOut(
                    label="Generate QP",
                    href=f"/dashboard/ai-papers?class_id={slot.class_id}&subject_id={slot.subject_id}",
                    variant="outline",
                ),
            ]
            if can_attend:
                actions.insert(
                    0,
                    DashboardActionOut(
                        label="Mark Attendance",
                        href="/dashboard/attendance",
                        variant="primary",
                    ),
                )
            else:
                actions.insert(
                    0,
                    DashboardActionOut(
                        label="View Mastery",
                        href="/dashboard/mastery",
                        variant="primary",
                    ),
                )

            cards.append(
                TodayClassOut(
                    slot_id=slot.id,
                    class_id=slot.class_id,
                    subject_id=slot.subject_id,
                    class_label=f"{cls.grade} - {cls.section}",
                    subject_name=subj.name,
                    period_number=slot.period_number,
                    start_time=slot.start_time.strftime("%H:%M"),
                    end_time=slot.end_time.strftime("%H:%M"),
                    room=cls.room_number,
                    next_topic=weak_topic,
                    attendance_status=att_status,
                    homework_pending=False,
                    actions=actions,
                )
            )
        return cards

    async def _attendance_status(
        self, school_id: uuid.UUID, scope: StaffScope, class_id: uuid.UUID, today: date
    ) -> str:
        if not scope.is_class_incharge(class_id):
            return "not_yours"
        student_count = await self.db.scalar(
            select(func.count())
            .select_from(Student)
            .where(Student.school_id == school_id, Student.class_id == class_id)
        )
        if not student_count:
            return "pending"
        marked = await self.db.scalar(
            select(func.count())
            .select_from(Attendance)
            .where(
                Attendance.school_id == school_id,
                Attendance.class_id == class_id,
                Attendance.date == today,
            )
        )
        return "done" if marked and marked >= student_count else "pending"

    async def _weakest_topic(
        self, school_id: uuid.UUID, class_id: uuid.UUID, subject_id: uuid.UUID
    ) -> str | None:
        row = (
            await self.db.execute(
                select(StudentTopicMastery.topic_display, func.avg(StudentTopicMastery.mastery_pct))
                .where(
                    StudentTopicMastery.school_id == school_id,
                    StudentTopicMastery.class_id == class_id,
                    StudentTopicMastery.subject_id == subject_id,
                )
                .group_by(StudentTopicMastery.topic_display)
                .order_by(func.avg(StudentTopicMastery.mastery_pct).asc())
                .limit(1)
            )
        ).first()
        return row[0] if row else None

    async def _weekly_timetable(
        self,
        school_id: uuid.UUID,
        teacher_id: uuid.UUID,
        classes: dict[uuid.UUID, Class],
        subjects: dict[uuid.UUID, Subject],
    ) -> list[TimetableDayOut]:
        rows = (
            await self.db.execute(
                select(TimetableSlot)
                .where(
                    TimetableSlot.school_id == school_id,
                    TimetableSlot.teacher_id == teacher_id,
                )
                .order_by(TimetableSlot.day_of_week, TimetableSlot.start_time)
            )
        ).scalars().all()

        by_day: dict[DayOfWeek, list[TimetableSlotBriefOut]] = defaultdict(list)
        for slot in rows:
            cls = classes.get(slot.class_id)
            subj = subjects.get(slot.subject_id)
            if not cls or not subj:
                continue
            by_day[slot.day_of_week].append(
                TimetableSlotBriefOut(
                    start_time=slot.start_time.strftime("%H:%M"),
                    class_label=f"{cls.grade.replace('Class ', '')}{cls.section}",
                    subject_name=subj.name,
                )
            )

        order = [
            DayOfWeek.MONDAY, DayOfWeek.TUESDAY, DayOfWeek.WEDNESDAY,
            DayOfWeek.THURSDAY, DayOfWeek.FRIDAY, DayOfWeek.SATURDAY,
        ]
        return [
            TimetableDayOut(
                day=d.value,
                day_label=_DAY_LABEL[d],
                slots=by_day.get(d, []),
            )
            for d in order
            if by_day.get(d)
        ]

    async def _subject_progress(
        self,
        school_id: uuid.UUID,
        teaching_pairs: set[tuple[uuid.UUID, uuid.UUID]],
        classes: dict[uuid.UUID, Class],
        subjects: dict[uuid.UUID, Subject],
    ) -> list[SubjectProgressOut]:
        results: list[SubjectProgressOut] = []
        for class_id, subject_id in sorted(teaching_pairs):
            cls = classes.get(class_id)
            subj = subjects.get(subject_id)
            if not cls or not subj:
                continue

            avg_row = await self.db.execute(
                select(func.avg(StudentTopicMastery.mastery_pct)).where(
                    StudentTopicMastery.school_id == school_id,
                    StudentTopicMastery.class_id == class_id,
                    StudentTopicMastery.subject_id == subject_id,
                )
            )
            avg_mastery = avg_row.scalar()
            weak_rows = (
                await self.db.execute(
                    select(
                        StudentTopicMastery.topic_display,
                        func.avg(StudentTopicMastery.mastery_pct),
                    )
                    .where(
                        StudentTopicMastery.school_id == school_id,
                        StudentTopicMastery.class_id == class_id,
                        StudentTopicMastery.subject_id == subject_id,
                    )
                    .group_by(StudentTopicMastery.topic_display)
                    .order_by(func.avg(StudentTopicMastery.mastery_pct).asc())
                    .limit(3)
                )
            ).all()
            weak = [r[0] for r in weak_rows if r[1] is not None and float(r[1]) < 70]

            flag_rows = (
                await self.db.execute(
                    select(MasteryFlag, User.full_name)
                    .join(Student, Student.id == MasteryFlag.student_id)
                    .join(User, User.id == Student.user_id)
                    .where(
                        MasteryFlag.school_id == school_id,
                        MasteryFlag.class_id == class_id,
                        MasteryFlag.subject_id == subject_id,
                        MasteryFlag.status == FlagStatus.PENDING_REVIEW,
                    )
                    .limit(5)
                )
            ).all()
            attention = [
                StudentAttentionOut(
                    student_id=f.student_id,
                    student_name=name or "Student",
                    reason=f"Weak in {f.topic_display}",
                    topic=f.topic_display,
                )
                for f, name in flag_rows
            ]

            results.append(
                SubjectProgressOut(
                    class_id=class_id,
                    subject_id=subject_id,
                    class_label=f"{cls.grade} - {cls.section}",
                    subject_name=subj.name,
                    average_mastery=round(float(avg_mastery), 1) if avg_mastery else None,
                    weak_concepts=weak,
                    students_needing_attention=attention,
                )
            )
        return results

    async def _pending_work(
        self,
        school_id: uuid.UUID,
        scope: StaffScope,
        teaching_pairs: set[tuple[uuid.UUID, uuid.UUID]],
    ) -> list[PendingWorkOut]:
        items: list[PendingWorkOut] = []

        draft_count = await self.db.scalar(
            select(func.count())
            .select_from(QuestionPaper)
            .where(
                QuestionPaper.school_id == school_id,
                QuestionPaper.created_by == scope.user_id,
                QuestionPaper.status.in_(_TEACHER_SUBMIT_STATUSES),
            )
        )
        if draft_count:
            items.append(
                PendingWorkOut(
                    kind="qp_draft",
                    label="AI question papers awaiting class teacher approval",
                    detail="Submit for approval when ready",
                    href="/dashboard/ai-papers",
                    count=draft_count,
                )
            )

        if scope.incharge_class_ids:
            approve_count = await self.db.scalar(
                select(func.count())
                .select_from(QuestionPaper)
                .where(
                    QuestionPaper.school_id == school_id,
                    QuestionPaper.class_id.in_(scope.incharge_class_ids),
                    QuestionPaper.status.in_(_INCHARGE_REVIEW_STATUSES),
                    QuestionPaper.created_by != scope.user_id,
                )
            )
            if approve_count:
                items.append(
                    PendingWorkOut(
                        kind="qp_approval",
                        label="Question papers to approve",
                        href="/dashboard/ai-papers",
                        count=approve_count,
                    )
                )

        subject_ids = {sid for _, sid in teaching_pairs}
        flag_count = await self.db.scalar(
            select(func.count())
            .select_from(MasteryFlag)
            .where(
                MasteryFlag.school_id == school_id,
                MasteryFlag.subject_id.in_(subject_ids),
                MasteryFlag.status == FlagStatus.PENDING_REVIEW,
            )
        )
        if flag_count:
            items.append(
                PendingWorkOut(
                    kind="flag_review",
                    label="Students flagged for subject review",
                    href="/dashboard/mastery",
                    count=flag_count,
                )
            )

        lp_count = await self.db.scalar(
            select(func.count())
            .select_from(LessonPlan)
            .where(
                LessonPlan.school_id == school_id,
                LessonPlan.created_by == scope.user_id,
                LessonPlan.status == LessonPlanStatus.DRAFT,
            )
        )
        if lp_count:
            items.append(
                PendingWorkOut(
                    kind="lesson_plan",
                    label="Lesson plan(s) pending confirmation",
                    detail="Review and approve before your next class",
                    href="/dashboard",
                    count=lp_count,
                )
            )
        return items

    async def _load_lesson_plan(
        self,
        school_id: uuid.UUID,
        scope: StaffScope,
        classes: dict[uuid.UUID, Class],
        subjects: dict[uuid.UUID, Subject],
        progress: list[SubjectProgressOut],
    ) -> LessonPlanPreviewOut | None:
        svc = LessonPlanService(self.db)
        plan = await svc.next_draft(school_id, scope)
        if plan:
            cls = classes.get(plan.class_id)
            subj = subjects.get(plan.subject_id)
            if cls and subj:
                sched = (
                    f"Scheduled {plan.scheduled_for.isoformat()}"
                    if plan.scheduled_for
                    else "Next class"
                )
                return LessonPlanPreviewOut(
                    id=plan.id,
                    class_id=plan.class_id,
                    subject_id=plan.subject_id,
                    class_label=f"{cls.grade} - {cls.section}",
                    subject_name=subj.name,
                    schedule_label=sched,
                    chapter=plan.chapter,
                    topic=plan.topic,
                    segments=[
                        LessonPlanSegmentOut(**s) for s in (plan.segments or [])
                    ],
                    status=plan.status.value,
                    can_edit=svc.can_edit(scope, plan),
                    can_approve=svc.can_approve(scope, plan),
                    actions=[
                        DashboardActionOut(
                            label="Create Worksheet",
                            href=f"/dashboard/ai-papers?class_id={plan.class_id}&subject_id={plan.subject_id}",
                            variant="outline",
                        ),
                    ],
                )

        if not scope.teaching_pairs:
            return None
        class_id, subject_id = sorted(scope.teaching_pairs)[0]
        cls = classes.get(class_id)
        subj = subjects.get(subject_id)
        if not cls or not subj:
            return None
        prog = next(
            (p for p in progress if p.class_id == class_id and p.subject_id == subject_id),
            None,
        )
        topic = prog.weak_concepts[0] if prog and prog.weak_concepts else None
        return LessonPlanPreviewOut(
            class_id=class_id,
            subject_id=subject_id,
            class_label=f"{cls.grade} - {cls.section}",
            subject_name=subj.name,
            schedule_label="Generate your first plan",
            chapter=subj.name,
            topic=topic,
            segments=_DEFAULT_LESSON_SEGMENTS,
            status="none",
            can_edit=False,
            can_approve=False,
            actions=[
                DashboardActionOut(
                    label="Generate Lesson Plan",
                    href="#generate-lesson-plan",
                    variant="primary",
                ),
            ],
        )

    async def _notices(
        self, school_id: uuid.UUID, scope: StaffScope
    ) -> tuple[list[TeacherNoticeOut], list[TeacherNoticeOut]]:
        from app.modules.communications.services.notice_service import NoticeService

        notices = await NoticeService(self.db).list_notices_for_staff(
            school_id, scope, limit=20
        )
        read_ids = set(
            (
                await self.db.execute(
                    select(NoticeReadReceipt.notice_id).where(
                        NoticeReadReceipt.user_id == scope.user_id
                    )
                )
            ).scalars().all()
        )

        staff: list[TeacherNoticeOut] = []
        school: list[TeacherNoticeOut] = []
        for n in notices:
            out = TeacherNoticeOut(
                id=n.id,
                title=n.title,
                content=n.content[:200],
                priority=n.priority.value,
                created_at=n.created_at.isoformat() if n.created_at else None,
                acknowledged=n.id in read_ids,
                can_acknowledge=n.audience == NoticeAudience.INTERNAL,
            )
            if n.audience == NoticeAudience.INTERNAL:
                staff.append(out)
            elif scope.incharge_class_ids and (
                n.class_id is None or n.class_id in scope.incharge_class_ids
            ):
                school.append(out)
        return staff[:6], school[:4]
