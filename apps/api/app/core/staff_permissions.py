"""
Staff RBAC — class incharge vs subject teacher scoping.

Class incharges are sub-admins for assigned classes (Class.class_incharge_id).
Subject teachers are mapped via TeacherSubjectMapping (class + subject).
School admins (admin / super_admin) bypass class scope.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser
from app.db.models.academic import Class, TeacherSubjectMapping
from app.db.models.curriculum_pack import CurriculumPack
from app.db.models.examination import Exam
from app.db.models.question_paper import _LOCKED_STATUSES, PaperStatus, QuestionPaper
from app.db.models.report_card import ReportCard, ReportStatus

_ADMIN_ROLES = frozenset({"admin", "super_admin"})


@dataclass
class StaffScope:
    """Resolved permissions for a staff user within their school."""

    user_id: uuid.UUID
    role: str
    is_admin: bool
    incharge_class_ids: set[uuid.UUID] = field(default_factory=set)
    teaching_pairs: set[tuple[uuid.UUID, uuid.UUID]] = field(default_factory=set)

    @property
    def teaching_class_ids(self) -> set[uuid.UUID]:
        return {class_id for class_id, _ in self.teaching_pairs}

    @property
    def scoped_only(self) -> bool:
        return not self.is_admin

    def all_class_ids(self) -> set[uuid.UUID] | None:
        """None means unrestricted (admin)."""
        if self.is_admin:
            return None
        return self.incharge_class_ids | self.teaching_class_ids

    def is_class_incharge(self, class_id: uuid.UUID) -> bool:
        return self.is_admin or class_id in self.incharge_class_ids

    def teaches(self, class_id: uuid.UUID, subject_id: uuid.UUID) -> bool:
        return (class_id, subject_id) in self.teaching_pairs

    def can_access_class(self, class_id: uuid.UUID) -> bool:
        if self.is_admin:
            return True
        return class_id in self.all_class_ids()

    def can_mark_attendance(self, class_id: uuid.UUID) -> bool:
        return self.is_class_incharge(class_id)

    def can_edit_timetable(self, class_id: uuid.UUID) -> bool:
        return self.is_class_incharge(class_id)

    def can_generate_report_cards(self, class_id: uuid.UUID) -> bool:
        return self.is_class_incharge(class_id)

    def can_generate_question_paper(self, class_id: uuid.UUID, subject_id: uuid.UUID) -> bool:
        if self.is_admin:
            return True
        if class_id in self.incharge_class_ids:
            return True
        return self.teaches(class_id, subject_id)

    def can_edit_curriculum_draft(self, class_id: uuid.UUID, subject_id: uuid.UUID) -> bool:
        if self.is_admin:
            return True
        if class_id in self.incharge_class_ids:
            return True
        return self.teaches(class_id, subject_id)

    def can_approve_curriculum_pack(self, pack: CurriculumPack) -> bool:
        if self.is_admin:
            return True
        if pack.class_id not in self.incharge_class_ids:
            return False
        if pack.created_by == self.user_id:
            return False
        return True

    def can_edit_question_paper(self, paper: QuestionPaper) -> bool:
        if paper.status in _LOCKED_STATUSES:
            return False
        if self.is_admin:
            return True
        if self.is_class_incharge(paper.class_id):
            return True
        if paper.created_by == self.user_id:
            return True
        return False

    def can_submit_question_paper(self, paper: QuestionPaper) -> bool:
        if paper.status not in (
            PaperStatus.DRAFT,
            PaperStatus.EDITED,
            PaperStatus.REJECTED,
        ):
            return False
        if self.is_admin or self.is_class_incharge(paper.class_id):
            return True
        return paper.created_by == self.user_id

    def can_approve_question_paper(self, paper: QuestionPaper) -> bool:
        if paper.status in (
            PaperStatus.APPROVED,
            PaperStatus.PUBLISHED,
            PaperStatus.ARCHIVED,
        ):
            return False
        if self.is_admin:
            return True
        return self.is_class_incharge(paper.class_id)

    def can_reject_question_paper(self, paper: QuestionPaper) -> bool:
        return self.can_approve_question_paper(paper)

    def can_download_question_paper(self, paper: QuestionPaper) -> bool:
        if self.is_admin:
            return True
        if paper.status in (PaperStatus.APPROVED, PaperStatus.PUBLISHED):
            return self.can_generate_question_paper(paper.class_id, paper.subject_id)
        return self.can_edit_question_paper(paper)

    @property
    def is_subject_only(self) -> bool:
        """Teaches subjects but is not a class incharge or admin."""
        return bool(self.teaching_pairs) and not self.incharge_class_ids and not self.is_admin

    def can_view_class_roster(self, class_id: uuid.UUID) -> bool:
        return self.is_class_incharge(class_id)

    def can_use_exams(self) -> bool:
        return self.is_admin or bool(self.incharge_class_ids) or bool(self.teaching_pairs)

    def can_evaluate_answer_sheets(self, class_id: uuid.UUID, subject_id: uuid.UUID) -> bool:
        if self.is_admin:
            return True
        if class_id in self.incharge_class_ids:
            return True
        return self.teaches(class_id, subject_id)

    def can_review_mastery_flag(self, class_id: uuid.UUID, subject_id: uuid.UUID) -> bool:
        """Approve/edit/notify mastery flags — same scope as flag list for teachers."""
        return self.can_evaluate_answer_sheets(class_id, subject_id)

    def can_view_school_analytics(self) -> bool:
        return self.is_admin

    def can_publish_notice(self, class_id: uuid.UUID | None) -> bool:
        if self.is_admin:
            return True
        if class_id is None:
            return False
        return class_id in self.incharge_class_ids

    def can_publish_internal_notice(self, class_id: uuid.UUID | None) -> bool:
        return self.is_admin

    def can_publish_external_notice(self, class_id: uuid.UUID | None) -> bool:
        return self.can_publish_notice(class_id)

    def can_edit_report_card(self, report: ReportCard) -> bool:
        if self.is_admin:
            return True
        return self.is_class_incharge(report.class_id)

    def can_approve_report_card(self, report: ReportCard) -> bool:
        if report.status == ReportStatus.APPROVED:
            return False
        return self.can_edit_report_card(report)

    def can_access_report_card(self, report: ReportCard) -> bool:
        if self.is_admin:
            return True
        return self.is_class_incharge(report.class_id)

    def subject_ids_for_class(self, class_id: uuid.UUID) -> set[uuid.UUID] | None:
        """None = all subjects (admin or incharge). Empty set = no subjects."""
        if self.is_admin or class_id in self.incharge_class_ids:
            return None
        return {sid for cid, sid in self.teaching_pairs if cid == class_id}


async def get_staff_scope(
    db: AsyncSession, current_user: CurrentUser
) -> StaffScope:
    user_id = uuid.UUID(current_user.id)
    school_id = uuid.UUID(current_user.school_id)
    role = current_user.role
    is_admin = role in _ADMIN_ROLES

    incharge_rows = await db.execute(
        select(Class.id).where(
            Class.school_id == school_id,
            Class.class_incharge_id == user_id,
        )
    )
    incharge_class_ids = set(incharge_rows.scalars().all())

    mapping_rows = await db.execute(
        select(TeacherSubjectMapping.class_id, TeacherSubjectMapping.subject_id).where(
            TeacherSubjectMapping.school_id == school_id,
            TeacherSubjectMapping.teacher_id == user_id,
        )
    )
    teaching_pairs = {(row[0], row[1]) for row in mapping_rows.all()}

    return StaffScope(
        user_id=user_id,
        role=role,
        is_admin=is_admin,
        incharge_class_ids=incharge_class_ids,
        teaching_pairs=teaching_pairs,
    )


def assert_class_access(scope: StaffScope, class_id: uuid.UUID) -> None:
    if not scope.can_access_class(class_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this class",
        )


def assert_attendance_access(scope: StaffScope, class_id: uuid.UUID) -> None:
    if not scope.can_mark_attendance(class_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only class incharges can mark attendance for this class",
        )


def assert_timetable_edit(scope: StaffScope, class_id: uuid.UUID) -> None:
    if not scope.can_edit_timetable(class_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and class incharges can edit the timetable",
        )


def assert_qp_generate(scope: StaffScope, class_id: uuid.UUID, subject_id: uuid.UUID) -> None:
    if not scope.can_generate_question_paper(class_id, subject_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to teach this subject in this class",
        )


def assert_qp_edit(scope: StaffScope, paper: QuestionPaper) -> None:
    if not scope.can_edit_question_paper(paper):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot edit this question paper",
        )


def assert_qp_approve(scope: StaffScope, paper: QuestionPaper) -> None:
    if not scope.can_approve_question_paper(paper):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the class incharge or admin can approve this paper",
        )


def assert_qp_download(scope: StaffScope, paper: QuestionPaper) -> None:
    if not scope.can_download_question_paper(paper):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot access this question paper",
        )


def assert_report_cards(scope: StaffScope, class_id: uuid.UUID) -> None:
    if not scope.can_generate_report_cards(class_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only class incharges can manage report cards for this class",
        )


def assert_class_roster(scope: StaffScope, class_id: uuid.UUID) -> None:
    if not scope.can_view_class_roster(class_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only class incharges can view the class roster",
        )


def assert_exams_access(scope: StaffScope) -> None:
    if not scope.can_use_exams():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and class incharges can access exams and marks",
        )


def assert_exam_class(scope: StaffScope, class_id: uuid.UUID) -> None:
    assert_exams_access(scope)
    if scope.is_admin:
        return
    if class_id in scope.incharge_class_ids:
        return
    if class_id in scope.teaching_class_ids:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You can only manage exams for your assigned class",
    )


def assert_exam_eval_access(scope: StaffScope, exam: Exam) -> None:
    if not scope.can_evaluate_answer_sheets(exam.class_id, exam.subject_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to evaluate answer sheets for this exam",
        )


def assert_notice_publish(scope: StaffScope, class_id: uuid.UUID | None, audience: str) -> None:
    if audience == "internal":
        if not scope.can_publish_internal_notice(class_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only school admins can publish internal staff notices",
            )
        return
    if not scope.can_publish_external_notice(class_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot publish parent/student notices for this scope",
        )


def assert_mastery_flag_review(
    scope: StaffScope, class_id: uuid.UUID, subject_id: uuid.UUID
) -> None:
    if not scope.can_review_mastery_flag(class_id, subject_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to review mastery flags for this class and subject",
        )
