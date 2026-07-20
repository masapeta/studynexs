"""Lesson plan generation — template-first with optional CurriculumPack grounding."""
from __future__ import annotations

import uuid
from datetime import date, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.staff_permissions import StaffScope, assert_qp_generate
from app.db.models.academic import Class, Subject
from app.db.models.lesson_plan import LessonPlan, LessonPlanStatus
from app.db.models.mastery import StudentTopicMastery
from app.modules.curriculum.services.curriculum_grounding import CurriculumGrounding, ground_approved_pack

if TYPE_CHECKING:
    from app.modules.ai.embeddings import EmbeddingService
    from app.modules.ai.vectorstore.base import VectorStore


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
        pack_id: uuid.UUID | None = None,
        embedder: "EmbeddingService | None" = None,
        store: "VectorStore | None" = None,
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

        grounding: CurriculumGrounding | None = None
        topic_list = [topic] if topic else None
        if pack_id is not None:
            grounding = await ground_approved_pack(
                self.db,
                school_id=school_id,
                pack_id=pack_id,
                class_id=class_id,
                subject_id=subject_id,
                topics=topic_list,
                embedder=embedder,
                store=store,
            )
            if grounding.is_empty:
                raise ValueError(
                    "This curriculum pack has no chapters/topics to ground on yet."
                )

        focus_topic = topic or await self._weakest_topic(school_id, class_id, subject_id)
        if not focus_topic and grounding and grounding.sources:
            focus_topic = grounding.sources[0].get("topic") or "Next topic"
        focus_topic = focus_topic or "Next topic"

        chapter_name = chapter
        if not chapter_name and grounding and grounding.sources:
            chapter_name = grounding.sources[0].get("chapter")
        chapter_name = chapter_name or subj.name

        sched = scheduled_for or (date.today() + timedelta(days=1))

        segments = self._segments_for_topic(focus_topic)
        if grounding and grounding.context_text:
            segments[1]["activity"] = (
                f"Teach {focus_topic} using approved curriculum "
                f"(pack v{grounding.pack_version}): grounded from {grounding.chunk_count} sources"
            )

        plan = LessonPlan(
            school_id=school_id,
            class_id=class_id,
            subject_id=subject_id,
            created_by=scope.user_id,
            title=f"{cls.grade} {cls.section} — {subj.name}: {focus_topic}",
            chapter=chapter_name,
            topic=focus_topic,
            scheduled_for=sched,
            segments=segments,
            status=LessonPlanStatus.DRAFT,
            ai_model="template-v1-grounded" if grounding else "template-v1",
            pack_id=grounding.pack_id if grounding else None,
            grounded=bool(grounding),
            grounding_sources=grounding.sources if grounding else None,
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
        if plan.status != LessonPlanStatus.DRAFT or plan.created_by != scope.user_id:
            return False
        return (
            scope.teaches(plan.class_id, plan.subject_id)
            or scope.is_class_incharge(plan.class_id)
        )

    def can_approve(self, scope: StaffScope, plan: LessonPlan) -> bool:
        if plan.status == LessonPlanStatus.APPROVED:
            return False
        return scope.is_class_incharge(plan.class_id)
