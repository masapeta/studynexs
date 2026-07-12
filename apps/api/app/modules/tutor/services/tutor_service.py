"""Mistake Recovery Tutor — lessons from mastery + exam misconceptions."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.academic import Subject
from app.db.models.mastery import StudentTopicMastery
from app.db.models.misconception import MisconceptionEntry
from app.db.models.student import Student
from app.modules.tutor.schemas.tutor import TutorLessonOut, TutorRecommendationOut
from app.modules.curriculum.services.concept_card_service import ConceptCardService
from app.modules.tutor.services.concept_card_lesson import build_lesson_from_concept_card
from app.modules.tutor.services.lesson_templates import (
    LESSON_TEMPLATES,
    build_lesson_from_template,
    match_lesson_key,
    slugify_lesson_key,
)

_WEAK_THRESHOLD = 70.0
_DEMO_LESSON = "fractions"


async def _weak_topics(
    db: AsyncSession, school_id: uuid.UUID, student_id: uuid.UUID
) -> list[tuple[str, str, float]]:
    rows = (
        await db.execute(
            select(StudentTopicMastery.topic, Subject.name, StudentTopicMastery.mastery_pct)
            .join(Subject, Subject.id == StudentTopicMastery.subject_id)
            .where(
                StudentTopicMastery.school_id == school_id,
                StudentTopicMastery.student_id == student_id,
                StudentTopicMastery.mastery_pct < _WEAK_THRESHOLD,
            )
            .order_by(StudentTopicMastery.mastery_pct.asc())
            .limit(8)
        )
    ).all()
    return [(topic, subject, float(pct)) for topic, subject, pct in rows]


async def _student_misconceptions(
    db: AsyncSession, school_id: uuid.UUID, student_id: uuid.UUID, limit: int = 5
) -> list[MisconceptionEntry]:
    result = await db.execute(
        select(MisconceptionEntry)
        .where(
            MisconceptionEntry.school_id == school_id,
            MisconceptionEntry.student_id == student_id,
        )
        .order_by(MisconceptionEntry.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def list_recommendations(
    db: AsyncSession, *, school_id: uuid.UUID, student_id: uuid.UUID
) -> list[TutorRecommendationOut]:
    recs: list[TutorRecommendationOut] = []
    seen: set[str] = set()

    for mc in await _student_misconceptions(db, school_id, student_id):
        key = slugify_lesson_key(mc.topic)
        if key in seen:
            continue
        seen.add(key)
        recs.append(
            TutorRecommendationOut(
                lesson_key=key,
                topic=mc.topic,
                subject_name="From your exam",
                reason=f"Exam mistake: {mc.common_mistake[:120]}",
            )
        )

    for topic, subject, pct in await _weak_topics(db, school_id, student_id):
        key = slugify_lesson_key(topic)
        if key in seen:
            continue
        seen.add(key)
        recs.append(
            TutorRecommendationOut(
                lesson_key=key,
                topic=topic,
                subject_name=subject,
                mastery_pct=pct,
                reason=f"Weak topic — {pct:.0f}% mastery",
            )
        )

    if not recs:
        tpl = LESSON_TEMPLATES[_DEMO_LESSON]
        recs.append(
            TutorRecommendationOut(
                lesson_key=_DEMO_LESSON,
                topic=tpl["topic"],
                subject_name=tpl["subject_name"],
                reason="Sample lesson — starts after your first marked exam",
            )
        )
    return recs


async def get_lesson(
    db: AsyncSession,
    *,
    school_id: uuid.UUID,
    student_id: uuid.UUID,
    lesson_key: str,
) -> TutorLessonOut | None:
    student = (
        await db.execute(
            select(Student).where(Student.id == student_id, Student.school_id == school_id)
        )
    ).scalar_one_or_none()
    if not student:
        return None

    card_match = await ConceptCardService(db).get_approved_by_slug(
        school_id=school_id, slug=lesson_key
    )
    if card_match is not None:
        card, concept = card_match
        weak = await _weak_topics(db, school_id, student_id)
        pct = None
        subject = "Curriculum"
        for t, s, p in weak:
            if slugify_lesson_key(t) == lesson_key or slugify_lesson_key(concept.title) == lesson_key:
                pct = p
                subject = s
                break
        return build_lesson_from_concept_card(
            card=card,
            concept=concept,
            subject_name=subject,
            mastery_pct=pct,
            trigger="concept_card",
        )

    if lesson_key in LESSON_TEMPLATES:
        weak = await _weak_topics(db, school_id, student_id)
        pct = None
        subject = LESSON_TEMPLATES[lesson_key]["subject_name"]
        for t, s, p in weak:
            if match_lesson_key(t) == lesson_key:
                pct = p
                subject = s
                break
        return build_lesson_from_template(
            lesson_key,
            topic=LESSON_TEMPLATES[lesson_key]["topic"],
            subject_name=subject,
            mastery_pct=pct,
            trigger="weak_topic" if pct is not None else "demo",
        )

    # Match misconception or weak topic by slug
    for mc in await _student_misconceptions(db, school_id, student_id):
        if slugify_lesson_key(mc.topic) == lesson_key:
            key = match_lesson_key(mc.topic)
            return build_lesson_from_template(
                key if key in LESSON_TEMPLATES else lesson_key,
                topic=mc.topic,
                subject_name="From your exam",
                trigger="exam_mistake",
                mistake_summary=mc.common_mistake,
            )

    for topic, subject, pct in await _weak_topics(db, school_id, student_id):
        if slugify_lesson_key(topic) == lesson_key:
            key = match_lesson_key(topic)
            return build_lesson_from_template(
                key if key in LESSON_TEMPLATES else lesson_key,
                topic=topic,
                subject_name=subject,
                mastery_pct=pct,
                trigger="weak_topic",
            )

    if lesson_key == _DEMO_LESSON or lesson_key.startswith("topic-"):
        return build_lesson_from_template(
            _DEMO_LESSON,
            topic=LESSON_TEMPLATES[_DEMO_LESSON]["topic"],
            subject_name=LESSON_TEMPLATES[_DEMO_LESSON]["subject_name"],
            trigger="demo",
        )
    return None
