"""Role-aware dashboard summary — only data the caller is allowed to see."""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.staff_permissions import StaffScope
from app.db.models.academic import Class
from app.db.models.attendance import Attendance, AttendanceStatus
from app.db.models.examination import Exam, ExamMark
from app.db.models.question_paper import (
    PaperStatus,
    QuestionPaper,
    _INCHARGE_REVIEW_STATUSES,
)
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


class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def build_summary(
        self, school_id: uuid.UUID, scope: StaffScope, *, teacher_name: str = "Teacher"
    ) -> DashboardSummaryOut:
        if scope.is_admin:
            return await self._admin_summary(school_id, scope)
        if scope.teaching_pairs:
            teacher_home = await TeacherHomeService(self.db).build(
                school_id, scope, teacher_name
            )
            return DashboardSummaryOut(
                persona="teacher",
                subtitle=teacher_home.tagline,
                teacher_home=teacher_home,
            )
        if scope.incharge_class_ids:
            return await self._incharge_summary(school_id, scope)
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
        att = await self.db.execute(
            select(
                func.count().filter(Attendance.status == AttendanceStatus.PRESENT),
                func.count(),
            ).where(
                Attendance.school_id == school_id,
                Attendance.date == today,
            )
        )
        present, total = att.one()
        att_pct = round((present / total) * 100, 1) if total else 0.0

        avg_pct = func.avg(ExamMark.marks_obtained / Exam.total_marks * 100)
        perf_rows = (
            await self.db.execute(
                select(Class.grade, Class.section, avg_pct.label("pct"))
                .join(Exam, Exam.class_id == Class.id)
                .join(ExamMark, ExamMark.exam_id == Exam.id)
                .where(Class.school_id == school_id)
                .group_by(Class.id, Class.grade, Class.section)
                .order_by(avg_pct.desc())
                .limit(3)
            )
        ).all()
        class_perf = [
            {"label": f"{g} - {s}", "percentage": round(float(p or 0), 1)}
            for g, s, p in perf_rows
        ]

        return DashboardSummaryOut(
            persona="admin",
            subtitle="School-wide overview for today.",
            total_students=students or 0,
            total_teachers=teachers or 0,
            total_classes=classes or 0,
            pending_fees=float(fee_stats.get("pending_amount") or 0),
            school_attendance_percent=att_pct,
            admissions_pipeline=pipeline_count or 0,
            expenses_this_month=expenses_month,
            class_performance=class_perf,
            quick_actions=[
                QuickActionOut(label="Add Student", href="/dashboard/students"),
                QuickActionOut(label="Mark Attendance", href="/dashboard/attendance"),
                QuickActionOut(label="Post Notice", href="/dashboard/notices"),
            ],
            notices=await self._notices_brief(school_id, scope),
        )

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

