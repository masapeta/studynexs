"""Unit tests for staff RBAC scope helpers."""
from __future__ import annotations

import uuid

from app.core.staff_permissions import StaffScope
from app.db.models.question_paper import PaperStatus, QuestionPaper
from app.db.models.report_card import ReportCard, ReportStatus


def _paper(class_id: uuid.UUID, subject_id: uuid.UUID, creator: uuid.UUID) -> QuestionPaper:
    return QuestionPaper(
        school_id=uuid.uuid4(),
        class_id=class_id,
        subject_id=subject_id,
        created_by=creator,
        title="Test",
        board="SSC",
        grade="Class 10",
        subject_name="Maths",
        total_marks=80,
        sections=[],
        status=PaperStatus.DRAFT,
    )


def test_subject_teacher_cannot_approve_own_paper() -> None:
    class_id = uuid.uuid4()
    subject_id = uuid.uuid4()
    teacher_id = uuid.uuid4()
    scope = StaffScope(
        user_id=teacher_id,
        role="teacher",
        is_admin=False,
        teaching_pairs={(class_id, subject_id)},
    )
    paper = _paper(class_id, subject_id, teacher_id)
    assert scope.can_generate_question_paper(class_id, subject_id)
    assert not scope.can_approve_question_paper(paper)


def test_class_incharge_can_approve_subject_teacher_draft() -> None:
    class_id = uuid.uuid4()
    subject_id = uuid.uuid4()
    incharge_id = uuid.uuid4()
    subject_teacher = uuid.uuid4()
    scope = StaffScope(
        user_id=incharge_id,
        role="class_incharge",
        is_admin=False,
        incharge_class_ids={class_id},
    )
    paper = _paper(class_id, subject_id, subject_teacher)
    assert scope.can_approve_question_paper(paper)


def test_ungrounded_exception_requires_submit_before_approval() -> None:
    class_id = uuid.uuid4()
    subject_id = uuid.uuid4()
    incharge = StaffScope(
        user_id=uuid.uuid4(),
        role="class_incharge",
        is_admin=False,
        incharge_class_ids={class_id},
    )
    paper = _paper(class_id, subject_id, uuid.uuid4())
    paper.ungrounded_reason = "Approved pack unavailable; every item requires manual review."

    assert incharge.can_generate_ungrounded_question_paper(class_id)
    assert not incharge.can_approve_question_paper(paper)
    paper.status = PaperStatus.PENDING_APPROVAL
    assert incharge.can_approve_question_paper(paper)


def test_class_incharge_can_reject_pending_paper() -> None:
    class_id = uuid.uuid4()
    subject_id = uuid.uuid4()
    incharge_id = uuid.uuid4()
    subject_teacher = uuid.uuid4()
    scope = StaffScope(
        user_id=incharge_id,
        role="class_incharge",
        is_admin=False,
        incharge_class_ids={class_id},
    )
    paper = _paper(class_id, subject_id, subject_teacher)
    paper.status = PaperStatus.PENDING_APPROVAL
    assert scope.can_reject_question_paper(paper)


def test_subject_teacher_can_submit_own_draft() -> None:
    class_id = uuid.uuid4()
    subject_id = uuid.uuid4()
    teacher_id = uuid.uuid4()
    scope = StaffScope(
        user_id=teacher_id,
        role="teacher",
        is_admin=False,
        teaching_pairs={(class_id, subject_id)},
    )
    paper = _paper(class_id, subject_id, teacher_id)
    assert scope.can_submit_question_paper(paper)
    assert not scope.can_reject_question_paper(paper)


def test_attendance_only_for_incharge() -> None:
    class_id = uuid.uuid4()
    incharge = StaffScope(
        user_id=uuid.uuid4(),
        role="class_incharge",
        is_admin=False,
        incharge_class_ids={class_id},
    )
    subject_only = StaffScope(
        user_id=uuid.uuid4(),
        role="teacher",
        is_admin=False,
        teaching_pairs={(class_id, uuid.uuid4())},
    )
    assert incharge.can_mark_attendance(class_id)
    assert not subject_only.can_mark_attendance(class_id)


def test_report_cards_incharge_only() -> None:
    class_id = uuid.uuid4()
    report = ReportCard(
        school_id=uuid.uuid4(),
        student_id=uuid.uuid4(),
        class_id=class_id,
        created_by=uuid.uuid4(),
        title="Term 1",
        student_name="Student",
        class_name="10-A",
        subjects=[],
        status=ReportStatus.DRAFT,
    )
    incharge = StaffScope(
        user_id=uuid.uuid4(),
        role="class_incharge",
        is_admin=False,
        incharge_class_ids={class_id},
    )
    teacher = StaffScope(
        user_id=uuid.uuid4(),
        role="teacher",
        is_admin=False,
        teaching_pairs={(class_id, uuid.uuid4())},
    )
    assert incharge.can_access_report_card(report)
    assert not teacher.can_access_report_card(report)
