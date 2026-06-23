"""Lesson plan generation — template-first MVP; LLM/CurriculumPack later."""
from __future__ import annotations

import uuid
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.staff_permissions import StaffScope, assert_qp_generate
from app.db.models.academic import Class, Subject
from app.db.models.lesson_plan import LessonPlan, LessonPlanStatus
from app.db.models.mastery import StudentTopicMastery


class LessonPlanService:
    def __init__(self, db: AsyncSession):
        self.db = db

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

    async def generate(
        self,
        school_id: uuid.UUID,
        scope: StaffScope,
        *,
        class_id: uuid.UUID,
        subject_id: uuid.UUID,
        topic: str | None = None,
        chapter: str | None = None,
        scheduled_for: date | None = None,
    ) -> LessonPlan:
        assert_qp_generate(scope, class_id, subject_id)
        cls = (
            await self.db.execute(
                select(Class).where(Class.id == class_id, Class.school_id == school_id)
            )
        ).scalar_one_or_none()
        subj = (
            await self.db.execute(
                select(Subject).where(Subject.id == subject_id, Subject.school_id == school_id)
            )
        ).scalar_one_or_none()
        if not cls or not subj:
            raise ValueError("Class or subject not found")

        focus_topic = topic or await self._weakest_topic(school_id, class_id, subject_id) or "Next topic"
        chapter_name = chapter or subj.name
        sched = scheduled_for or (date.today() + timedelta(days=1))

        plan = LessonPlan(
            school_id=school_id,
            class_id=class_id,
            subject_id=subject_id,
            created_by=scope.user_id,
            title=f"{cls.grade} {cls.section} — {subj.name}: {focus_topic}",
            chapter=chapter_name,
            topic=focus_topic,
            scheduled_for=sched,
            segments=self._segments_for_topic(focus_topic),
            status=LessonPlanStatus.DRAFT,
            ai_model="template-v1",
        )
        self.db.add(plan)
        await self.db.flush()
        return plan

    @staticmethod
    def _segments_for_topic(topic: str) -> list[dict]:
        return [
            {"duration_min": 5, "activity": f"Quick recap — prerequisites for {topic}"},
            {"duration_min": 12, "activity": f"Teach {topic} with worked examples"},
            {"duration_min": 8, "activity": f"Hands-on activity: {topic}"},
            {"duration_min": 10, "activity": f"Practice set — {topic}"},
            {"duration_min": 5, "activity": "Exit ticket (3 questions)"},
        ]

    async def next_draft(
        self, school_id: uuid.UUID, scope: StaffScope
    ) -> LessonPlan | None:
        if not scope.teaching_pairs:
            return None
        q = (
            select(LessonPlan)
            .where(
                LessonPlan.school_id == school_id,
                LessonPlan.created_by == scope.user_id,
                LessonPlan.status == LessonPlanStatus.DRAFT,
            )
            .order_by(LessonPlan.scheduled_for.asc().nullslast(), LessonPlan.created_at.desc())
            .limit(5)
        )
        for plan in (await self.db.execute(q)).scalars().all():
            if (plan.class_id, plan.subject_id) in scope.teaching_pairs:
                return plan
        return None

    def can_edit(self, scope: StaffScope, plan: LessonPlan) -> bool:
        if scope.is_admin:
            return True
        return plan.created_by == scope.user_id and plan.status == LessonPlanStatus.DRAFT

    def can_approve(self, scope: StaffScope, plan: LessonPlan) -> bool:
        if plan.status == LessonPlanStatus.APPROVED:
            return False
        if scope.is_admin:
            return True
        return plan.created_by == scope.user_id
