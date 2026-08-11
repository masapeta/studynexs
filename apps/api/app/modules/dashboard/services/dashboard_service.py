"""Role-aware dashboard summary — only data the caller is allowed to see."""
from __future__ import annotations

import re
import uuid
from datetime import date

from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.core.staff_permissions import StaffScope
from app.db.models.academic import Class, Subject, TeacherSubjectMapping
from app.db.models.attendance import Attendance, AttendanceStatus
from app.db.models.mastery import FlagSeverity, FlagStatus, MasteryFlag, StudentTopicMastery
from app.db.models.question_paper import _INCHARGE_REVIEW_STATUSES, QuestionPaper
from app.db.models.student import Student
from app.db.models.user import User, UserRole
from app.modules.communications.services.notice_service import NoticeService
from app.modules.dashboard.schemas.dashboard import (
    DashboardSummaryOut,
    InchargeClassSummaryOut,
    NoticeBriefOut,
    PrincipalInterventionEvidenceOut,
    PrincipalInterventionOut,
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

        attendance_trend = await self._attendance_trend(school_id, days=7)

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
            attendance_trend=attendance_trend,
            pending_qp_approvals=pending_qp or 0,
            principal_interventions=await self._principal_interventions(school_id),
            quick_actions=[
                QuickActionOut(label="Add Student", href="/dashboard/students"),
                QuickActionOut(label="Mark Attendance", href="/dashboard/attendance"),
                QuickActionOut(label="Post Notice", href="/dashboard/notices"),
            ],
            notices=await self._notices_brief(school_id, scope),
        )

    async def _principal_interventions(
        self, school_id: uuid.UUID, *, limit: int = 3
    ) -> list[PrincipalInterventionOut]:
        """Evidence-backed academic interventions for the principal decision workspace.

        This consumes the certified Learning Intelligence flag ledger and links to the
        existing mastery evidence-chain endpoint for full lineage. It intentionally does
        not invent scores or surface generic KPI noise: no actionable human follow-up
        means no intervention card.
        """
        StudentUser = aliased(User)
        SubjectTeacher = aliased(User)
        ClassIncharge = aliased(User)

        rows = (
            await self.db.execute(
                select(
                    MasteryFlag,
                    StudentUser.full_name.label("student_name"),
                    Class.grade,
                    Class.section,
                    Subject.name.label("subject_name"),
                    SubjectTeacher.full_name.label("teacher_name"),
                    ClassIncharge.full_name.label("incharge_name"),
                    StudentTopicMastery.mastery_pct,
                    StudentTopicMastery.class_avg_pct,
                    StudentTopicMastery.assessments_count,
                )
                .join(Student, Student.id == MasteryFlag.student_id)
                .join(StudentUser, StudentUser.id == Student.user_id)
                .join(Class, Class.id == MasteryFlag.class_id)
                .join(Subject, Subject.id == MasteryFlag.subject_id)
                .outerjoin(
                    TeacherSubjectMapping,
                    and_(
                        TeacherSubjectMapping.school_id == school_id,
                        TeacherSubjectMapping.class_id == MasteryFlag.class_id,
                        TeacherSubjectMapping.subject_id == MasteryFlag.subject_id,
                        TeacherSubjectMapping.is_primary.is_(True),
                    ),
                )
                .outerjoin(SubjectTeacher, SubjectTeacher.id == TeacherSubjectMapping.teacher_id)
                .outerjoin(ClassIncharge, ClassIncharge.id == Class.class_incharge_id)
                .outerjoin(
                    StudentTopicMastery,
                    and_(
                        StudentTopicMastery.school_id == school_id,
                        StudentTopicMastery.student_id == MasteryFlag.student_id,
                        StudentTopicMastery.subject_id == MasteryFlag.subject_id,
                        StudentTopicMastery.academic_year_id == MasteryFlag.academic_year_id,
                        StudentTopicMastery.topic == MasteryFlag.topic,
                    ),
                )
                .where(
                    MasteryFlag.school_id == school_id,
                    MasteryFlag.status.in_(
                        [
                            FlagStatus.PENDING_REVIEW,
                            FlagStatus.APPROVED,
                            FlagStatus.NOTIFIED,
                        ]
                    ),
                )
                .order_by(
                    case((MasteryFlag.severity == FlagSeverity.HIGH, 0), else_=1),
                    case((MasteryFlag.status == FlagStatus.PENDING_REVIEW, 0), else_=1),
                    MasteryFlag.created_at.desc(),
                )
                .limit(limit)
            )
        ).all()

        interventions: list[PrincipalInterventionOut] = []
        seen_flag_ids: set[uuid.UUID] = set()
        for (
            flag,
            student_name,
            grade,
            section,
            subject_name,
            teacher_name,
            incharge_name,
            mastery_pct,
            class_avg_pct,
            assessments_count,
        ) in rows:
            if flag.id in seen_flag_ids:
                continue
            seen_flag_ids.add(flag.id)
            class_label = f"{grade} - {section}"
            owner = teacher_name or incharge_name or "Class incharge"
            mastery_value = float(mastery_pct) if mastery_pct is not None else None
            class_avg_value = float(class_avg_pct) if class_avg_pct is not None else None
            severity = "high" if flag.severity == FlagSeverity.HIGH else "medium"
            issue = f"{class_label} {subject_name}: {flag.topic_display} needs intervention"
            if mastery_value is not None:
                why = (
                    f"{student_name} is at {mastery_value:.0f}% mastery"
                    f" on {flag.topic_display}."
                )
            else:
                why = f"{student_name} has a teacher-review flag for {flag.topic_display}."

            evidence: list[PrincipalInterventionEvidenceOut] = []
            if mastery_value is not None:
                evidence.append(
                    PrincipalInterventionEvidenceOut(
                        label="Mastery",
                        value=f"{mastery_value:.0f}%",
                    )
                )
            if class_avg_value is not None:
                evidence.append(
                    PrincipalInterventionEvidenceOut(
                        label="Class average",
                        value=f"{class_avg_value:.0f}%",
                    )
                )
            if assessments_count:
                evidence.append(
                    PrincipalInterventionEvidenceOut(
                        label="Assessment evidence",
                        value=f"{assessments_count} assessment"
                        f"{'' if int(assessments_count) == 1 else 's'}",
                    )
                )
            evidence.append(
                PrincipalInterventionEvidenceOut(
                    label="Teacher review",
                    value=flag.status.value.replace("_", " "),
                    href=f"/dashboard/teaching/mastery?flag_id={flag.id}",
                )
            )
            if flag.notified_at:
                evidence.append(
                    PrincipalInterventionEvidenceOut(
                        label="Parent signal",
                        value="Parent notified",
                    )
                )
            if flag.reasons:
                evidence.append(
                    PrincipalInterventionEvidenceOut(
                        label="Flag reason",
                        value=", ".join(str(reason).replace("_", " ") for reason in flag.reasons),
                    )
                )

            interventions.append(
                PrincipalInterventionOut(
                    id=f"mastery_flag:{flag.id}",
                    severity=severity,
                    issue=issue,
                    why_it_matters=why,
                    affected_scope=f"{class_label} · {subject_name} · {student_name}",
                    owner=owner,
                    recommended_intervention=(
                        f"Meet {owner} this week to review {flag.topic_display} outcomes "
                        "and agree a human-led remediation plan."
                    ),
                    status=flag.status.value,
                    href=f"/dashboard/teaching/mastery?flag_id={flag.id}",
                    evidence_chain_href=f"/api/v1/mastery/flags/{flag.id}/evidence-chain",
                    evidence=evidence,
                )
            )

        return interventions

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

    async def _attendance_trend(self, school_id: uuid.UUID, *, days: int = 7) -> list[float]:
        """School-wide present % for the last `days` recorded days, oldest first.

        Only days with actual records appear — holidays/weekends are skipped,
        so the sparkline never shows a fake 0%.
        """
        rows = (
            await self.db.execute(
                select(
                    Attendance.date,
                    func.count().filter(Attendance.status == AttendanceStatus.PRESENT),
                    func.count(func.distinct(Attendance.student_id)),
                )
                .where(Attendance.school_id == school_id)
                .group_by(Attendance.date)
                .order_by(Attendance.date.desc())
                .limit(days)
            )
        ).all()
        trend = [
            round((int(present or 0) / int(marked)) * 100, 1)
            for _day, present, marked in rows
            if int(marked or 0) > 0
        ]
        trend.reverse()  # oldest first for left-to-right sparkline
        return trend

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
