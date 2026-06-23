"""Seed teacher dashboard demo data: staff notices, lesson plan, Class 10 Maths mastery.

Run after seed_demo_ssc, patch_demo_ssc_rbac, seed_exam_marks:
  python scripts/seed_teacher_dashboard.py
"""
from __future__ import annotations

import asyncio
from datetime import date, timedelta

from sqlalchemy import select

from app.core.database import async_session_factory
from app.db.models.academic import Class, Subject
from app.db.models.communication import Notice, NoticeAudience, NoticePriority
from app.db.models.examination import Exam, ExamMark
from app.db.models.lesson_plan import LessonPlan, LessonPlanStatus
from app.db.models.school import School
from app.db.models.user import User, UserRole
from app.modules.curriculum.services.lesson_plan_service import LessonPlanService
from app.modules.mastery.services.mastery_service import recompute_class_subject

TENANT = "test"
MATHS_TOPICS = ["Algebra", "Geometry", "Trigonometry", "Statistics"]


async def main() -> None:
    async with async_session_factory() as db:
        school = (
            await db.execute(select(School).where(School.tenant_slug == TENANT))
        ).scalar_one_or_none()
        if not school:
            print("Demo school not found.")
            return

        principal = (
            await db.execute(
                select(User).where(
                    User.school_id == school.id, User.role == UserRole.SUPER_ADMIN
                )
            )
        ).scalars().first()
        teacher6 = (
            await db.execute(
                select(User).where(User.school_id == school.id, User.username == "teacher6")
            )
        ).scalar_one_or_none()
        if not teacher6:
            print("teacher6 not found — run patch_demo_ssc_rbac.py first.")
            return

        # Internal staff notice
        existing_internal = (
            await db.execute(
                select(Notice).where(
                    Notice.school_id == school.id,
                    Notice.audience == NoticeAudience.INTERNAL,
                )
            )
        ).scalar_one_or_none()
        if not existing_internal and principal:
            db.add(
                Notice(
                    school_id=school.id,
                    title="Staff meeting at 4 PM",
                    content="All teaching staff: monthly review in the staff room. Submit unit test marks by Friday.",
                    audience=NoticeAudience.INTERNAL,
                    target_roles=["teacher", "class_incharge"],
                    priority=NoticePriority.HIGH,
                    created_by=principal.id,
                )
            )
            print("  + internal staff notice")

        cls_10a = (
            await db.execute(
                select(Class).where(
                    Class.school_id == school.id,
                    Class.grade == "Class 10",
                    Class.section == "A",
                )
            )
        ).scalar_one_or_none()
        maths = None
        if cls_10a:
            maths = (
                await db.execute(
                    select(Subject).where(
                        Subject.school_id == school.id,
                        Subject.class_id == cls_10a.id,
                        Subject.name == "Mathematics",
                    )
                )
            ).scalar_one_or_none()

        # Topic-tagged exams for Class 10 Maths → mastery watchlist
        if cls_10a and maths:
            exams = (
                await db.execute(
                    select(Exam).where(
                        Exam.school_id == school.id,
                        Exam.class_id == cls_10a.id,
                        Exam.subject_id == maths.id,
                    )
                )
            ).scalars().all()
            for i, exam in enumerate(exams):
                if not exam.question_schema:
                    topic = MATHS_TOPICS[i % len(MATHS_TOPICS)]
                    exam.topic = topic
                    exam.question_schema = [
                        {"no": "1", "max_marks": float(exam.total_marks) * 0.5, "topic": topic},
                        {"no": "2", "max_marks": float(exam.total_marks) * 0.5, "topic": topic},
                    ]
            marks = (
                await db.execute(
                    select(ExamMark).where(
                        ExamMark.school_id == school.id,
                        ExamMark.exam_id.in_([e.id for e in exams]),
                    )
                )
            ).scalars().all()
            for mark in marks:
                if not mark.question_marks and exams:
                    exam = next(e for e in exams if e.id == mark.exam_id)
                    half = float(mark.marks_obtained) / 2
                    mark.question_marks = {"1": half, "2": float(mark.marks_obtained) - half}
            n = await recompute_class_subject(db, school.id, cls_10a.id, maths.id)
            print(f"  + mastery recomputed for Class 10-A Maths ({n} topic rows)")

        # Draft lesson plan for teacher6
        if cls_10a and maths:
            existing_lp = (
                await db.execute(
                    select(LessonPlan).where(
                        LessonPlan.school_id == school.id,
                        LessonPlan.created_by == teacher6.id,
                    )
                )
            ).scalar_one_or_none()
            if not existing_lp:
                from app.core.staff_permissions import StaffScope

                scope = StaffScope(
                    user_id=teacher6.id,
                    role="teacher",
                    is_admin=False,
                    teaching_pairs={(cls_10a.id, maths.id)},
                )
                plan = await LessonPlanService(db).generate(
                    school.id,
                    scope,
                    class_id=cls_10a.id,
                    subject_id=maths.id,
                    topic="Quadratic Equations",
                    chapter="Algebra",
                    scheduled_for=date.today() + timedelta(days=1),
                )
                plan.segments = LessonPlanService._segments_for_topic("Quadratic Equations")
                print(f"  + lesson plan draft: {plan.title}")

        await db.commit()
        print("Teacher dashboard demo data ready. Login as teacher6 / Demo@1234")


if __name__ == "__main__":
    asyncio.run(main())
