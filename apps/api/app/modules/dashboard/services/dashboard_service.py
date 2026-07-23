"""Role-aware dashboard summary — only data the caller is allowed to see."""
from __future__ import annotations

import re
import uuid
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.staff_permissions import StaffScope
from app.db.models.academic import Class
from app.db.models.attendance import Attendance, AttendanceStatus
from app.db.models.question_paper import _INCHARGE_REVIEW_STATUSES, QuestionPaper
from app.db.models.student import Student
from app.db.models.user import User, UserRole
from app.modules.communications.services.notice_service import NoticeService
from app.modules.dashboard.schemas.dashboard import (
    DashboardSummaryOut,
    InchargeClassSummaryOut,
    NoticeBriefOut,
    QuickActionOut,
)
from app.modules.dashboard.services.teacher_home_service import TeacherHomeService
from app.modules.fees.services.fee_service import FeeService


def _grade_sort_num(grade: str) -> int:
    match = re.search(r"\d+", grade or "")
    return int(match.group()) if match else 0


class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def build_summary(
        self, school_id: uuid.UUID, scope: StaffScope, *, teacher_name: str = "Teacher"
    ) -> DashboardSummaryOut:
        if scope.is_admin:
            return await self._admin_summary(school_id, scope)
        if scope.incharge_class_ids:
            return await self._incharge_summary(school_id, scope)
        if scope.teaching_pairs:
            teacher_home = await TeacherHomeService(self.db).build(
                school_id, scope, teacher_name
            )
            return DashboardSummaryOut(
                persona="teacher",
                subtitle=teacher_home.tagline,
                teacher_home=teacher_home,
            )
        return DashboardSummaryOut(
            persona="teacher",
            subtitle="Your teaching workspace",
            teacher_home=await TeacherHomeService(self.db).build(
                school_id, scope, teacher_name
            ),
        )

    async def _notices_brief(self, school_id: uuid.UUID, scope: StaffScope) -> list[NoticeBriefOut]:
        notices = await NoticeService(self.db).list_notices_for_staff(
            school_id, scope, limit=5
        )
        return [
            NoticeBriefOut(
                id=n.id,
                title=n.title,
                content=n.content[:120],
                audience=n.audience.value,
                priority=n.priority.value,
                created_at=n.created_at.isoformat() if n.created_at else None,
            )
            for n in notices
        ]

    async def _admin_summary(
        self, school_id: uuid.UUID, scope: StaffScope
    ) -> DashboardSummaryOut:
        students = await self.db.scalar(
            select(func.count()).select_from(Student).where(Student.school_id == school_id)
        )
        teachers = await self.db.scalar(
            select(func.count())
            .select_from(User)
            .where(
                User.school_id == school_id,
                User.role.in_([UserRole.TEACHER, UserRole.CLASS_INCHARGE]),
                User.is_active.is_(True),
            )
        )
        classes = await self.db.scalar(
            select(func.count()).select_from(Class).where(Class.school_id == school_id)
        )
        fee_stats = await FeeService(self.db).get_fee_stats(school_id)

        from app.db.models.school_ops import AdmissionCandidate, AdmissionStage
        from app.modules.school_ops.services.ops_service import SchoolOpsService

        pipeline_count = await self.db.scalar(
            select(func.count())
            .select_from(AdmissionCandidate)
            .where(
                AdmissionCandidate.school_id == school_id,
                AdmissionCandidate.stage != AdmissionStage.ENROLLED,
            )
        )
        expenses_month = await SchoolOpsService(self.db).expenses_month_total(school_id)

        today = date.today()
        att_status, att_pct, marked_today, enrolled = await self._school_attendance_state(
            school_id, today
        )

        class_perf: list[dict] = []
        if att_status != "not_recorded":
            class_perf = await self._class_attendance_bars(
                school_id, limit=6, chart_date=today
            )

        pending_qp = await self.db.scalar(
            select(func.count())
            .select_from(QuestionPaper)
            .where(
                QuestionPaper.school_id == school_id,
                QuestionPaper.status.in_(_INCHARGE_REVIEW_STATUSES),
            )
        )

        return DashboardSummaryOut(
            persona="admin",
            subtitle=self._admin_subtitle(att_status),
            total_students=students or 0,
            total_teachers=teachers or 0,
            total_classes=classes or 0,
            pending_fees=float(fee_stats.get("pending_amount") or 0),
            school_attendance_status=att_status,
            school_attendance_percent=att_pct,
            attendance_marked_today=marked_today,
            attendance_enrolled=enrolled,
            admissions_pipeline=pipeline_count or 0,
            expenses_this_month=expenses_month,
            class_performance=class_perf,
            pending_qp_approvals=pending_qp or 0,
            quick_actions=[
                QuickActionOut(label="Add Student", href="/dashboard/students"),
                QuickActionOut(label="Mark Attendance", href="/dashboard/attendance"),
                QuickActionOut(label="Post Notice", href="/dashboard/notices"),
            ],
            notices=await self._notices_brief(school_id, scope),
        )

    async def _school_attendance_state(
        self, school_id: uuid.UUID, on_date: date
    ) -> tuple[str, float | None, int, int]:
        """Truthful attendance state for today — never treat zero records as 0% failure."""
        enrolled = int(
            await self.db.scalar(
                select(func.count()).select_from(Student).where(Student.school_id == school_id)
            )
            or 0
        )
        row = await self.db.execute(
            select(
                func.count().filter(Attendance.status == AttendanceStatus.PRESENT),
                func.count(func.distinct(Attendance.student_id)),
            ).where(
                Attendance.school_id == school_id,
                Attendance.date == on_date,
            )
        )
        present, marked = row.one()
        present_i = int(present or 0)
        marked_i = int(marked or 0)

        if marked_i == 0:
            return "not_recorded", None, 0, enrolled

        pct = round((present_i / marked_i) * 100, 1)
        if enrolled > 0 and marked_i < enrolled:
            return "in_progress", pct, marked_i, enrolled
        if pct < 90.0:
            return "attention_needed", pct, marked_i, enrolled
        return "healthy", pct, marked_i, enrolled

    @staticmethod
    def _admin_subtitle(att_status: str) -> str:
        if att_status == "not_recorded":
            return "Attendance has not been recorded yet today."
        if att_status == "in_progress":
            return "Roll call is in progress across the school."
        return "School-wide overview for today."

    async def _class_attendance_bars(
        self, school_id: uuid.UUID, *, limit: int = 6, chart_date: date
    ) -> list[dict]:
        """Per-class attendance for the principal insights chart (single date, no fallback)."""
        rows = (
            await self.db.execute(
                select(
                    Class.grade,
                    Class.section,
                    func.count(Student.id).label("strength"),
                    func.count(Attendance.id)
                    .filter(Attendance.status == AttendanceStatus.PRESENT)
                    .label("present"),
                )
                .select_from(Class)
                .join(Student, Student.class_id == Class.id)
                .outerjoin(
                    Attendance,
                    (Attendance.student_id == Student.id)
                    & (Attendance.school_id == school_id)
                    & (Attendance.date == chart_date),
                )
                .where(Class.school_id == school_id)
                .group_by(Class.id, Class.grade, Class.section)
                .having(func.count(Student.id) > 0)
            )
        ).all()

        bars: list[dict] = []
        for grade, section, strength, present in rows:
            strength_i = int(strength or 0)
            present_i = int(present or 0)
            pct = round((present_i / strength_i) * 100, 1) if strength_i else 0.0
            bars.append(
                (
                    _grade_sort_num(grade),
                    str(section),
                    {
                        "label": f"{grade} - {section}",
                        "present": present_i,
                        "strength": strength_i,
                        "percentage": pct,
                        "date": chart_date.isoformat(),
                    },
                )
            )

        bars.sort(key=lambda row: (row[0], row[1]), reverse=True)
        return [row[2] for row in bars[:limit]]

    async def _incharge_summary(
        self, school_id: uuid.UUID, scope: StaffScope
    ) -> DashboardSummaryOut:
        today = date.today()
        incharge_rows: list[InchargeClassSummaryOut] = []
        for class_id in sorted(scope.incharge_class_ids):
            cls = (
                await self.db.execute(
                    select(Class).where(Class.id == class_id, Class.school_id == school_id)
                )
            ).scalar_one_or_none()
            if not cls:
                continue
            att = await self.db.execute(
                select(
                    func.count().filter(Attendance.status == AttendanceStatus.PRESENT),
                    func.count(),
                ).where(
                    Attendance.school_id == school_id,
                    Attendance.class_id == class_id,
                    Attendance.date == today,
                )
            )
            present, total = att.one()
            pending_qp = await self.db.scalar(
                select(func.count())
                .select_from(QuestionPaper)
                .where(
                    QuestionPaper.school_id == school_id,
                    QuestionPaper.class_id == class_id,
                    QuestionPaper.status.in_(_INCHARGE_REVIEW_STATUSES),
                    QuestionPaper.created_by != scope.user_id,
                )
            )
            incharge_rows.append(
                InchargeClassSummaryOut(
                    class_id=class_id,
                    class_label=f"{cls.grade} - {cls.section}",
                    attendance_percent=round((present / total) * 100, 1) if total else None,
                    pending_qp_approvals=pending_qp or 0,
                )
            )

        return DashboardSummaryOut(
            persona="class_incharge",
            subtitle="Your class(es) — attendance, papers awaiting approval, and notices.",
            incharge_classes=incharge_rows,
            quick_actions=[
                QuickActionOut(label="Mark Attendance", href="/dashboard/attendance"),
                QuickActionOut(label="Parent Notice", href="/dashboard/notices"),
                QuickActionOut(label="Report Cards", href="/dashboard/report-cards"),
                QuickActionOut(label="AI Papers", href="/dashboard/ai-papers"),
            ],
            notices=await self._notices_brief(school_id, scope),
        )

