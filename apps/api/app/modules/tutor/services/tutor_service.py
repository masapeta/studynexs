"""Mistake Recovery Tutor — lessons from mastery + exam misconceptions."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.academic import Subject
from app.db.models.concept_card import ConceptCard, ConceptCardStatus
from app.db.models.knowledge_graph import CurriculumConcept
from app.db.models.mastery import StudentTopicMastery
from app.db.models.misconception import MisconceptionEntry
from app.db.models.student import Student
from app.modules.curriculum.services.concept_card_service import ConceptCardService
from app.modules.knowledge_graph.services.student_weak_concept_service import (
    StudentWeakConceptService,
)
from app.modules.tutor.schemas.tutor import TutorLessonOut, TutorRecommendationOut
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
            select(
                StudentTopicMastery.topic,
                StudentTopicMastery.topic_display,
                Subject.name,
                StudentTopicMastery.mastery_pct,
            )
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
    return [(display or topic, subject, float(pct)) for topic, display, subject, pct in rows]


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


async def _student_weak_concept_card_for_lesson(
    db: AsyncSession,
    *,
    school_id: uuid.UUID,
    student_id: uuid.UUID,
    lesson_key: str,
) -> tuple[ConceptCard, CurriculumConcept, dict | None] | None:
    """Resolve a lesson slug through the student's own weak-concept evidence first.

    Multiple approved CurriculumPacks can legitimately contain the same concept
    slug (for example, repeated rehearsal packs). A school-wide slug lookup can
    therefore choose a different pack than the daily plan. The student lesson
    must preserve the daily-plan evidence chain, so prefer the matching
    student-specific weak concept and its approved ConceptCard before falling
    back to global/template resolution.
    """
    for concept, meta in await StudentWeakConceptService(db).get_weak_concepts_for_student(
        school_id=school_id, student_id=student_id
    ):
        if concept.slug != lesson_key:
            continue
        card = (
            await db.execute(
                select(ConceptCard).where(
                    ConceptCard.school_id == school_id,
                    ConceptCard.concept_id == concept.id,
                    ConceptCard.status == ConceptCardStatus.APPROVED,
                )
            )
        ).scalar_one_or_none()
        if card is not None:
            return card, concept, meta
    return None


async def _student_weak_concept_card_for_topic(
    db: AsyncSession,
    *,
    school_id: uuid.UUID,
    student_id: uuid.UUID,
    topic: str,
) -> tuple[ConceptCard, CurriculumConcept, dict | None] | None:
    """Resolve an exam/mastery topic through the student's current weak evidence."""
    topic_key = topic.strip().casefold()
    if not topic_key:
        return None
    for concept, meta in await StudentWeakConceptService(db).get_weak_concepts_for_student(
        school_id=school_id, student_id=student_id
    ):
        mastery_topic = str((meta or {}).get("topic") or "").strip().casefold()
        if mastery_topic != topic_key and topic_key not in concept.title.strip().casefold():
            continue
        card = (
            await db.execute(
                select(ConceptCard).where(
                    ConceptCard.school_id == school_id,
                    ConceptCard.concept_id == concept.id,
                    ConceptCard.status == ConceptCardStatus.APPROVED,
                )
            )
        ).scalar_one_or_none()
        if card is not None:
            return card, concept, meta
    return None


async def _subject_name_from_weak_meta(
    db: AsyncSession, *, school_id: uuid.UUID, meta: dict | None
) -> str:
    subject_id = (meta or {}).get("subject_id")
    if not subject_id:
        return "Curriculum"
    try:
        subject_uuid = uuid.UUID(str(subject_id))
    except (TypeError, ValueError):
        return "Curriculum"
    return (
        await db.scalar(
            select(Subject.name).where(
                Subject.id == subject_uuid,
                Subject.school_id == school_id,
            )
        )
    ) or "Curriculum"


async def list_recommendations(
    db: AsyncSession, *, school_id: uuid.UUID, student_id: uuid.UUID
) -> list[TutorRecommendationOut]:
    recs: list[TutorRecommendationOut] = []
    seen: set[str] = set()
    card_svc = ConceptCardService(db)

    async def _subject_name_for_misconception(mc: MisconceptionEntry) -> str:
        name = (
            await db.scalar(
                select(Subject.name).where(
                    Subject.id == mc.subject_id,
                    Subject.school_id == school_id,
                )
            )
        )
        return name or "From your exam"

    def _rec_from_card(
        *,
        card_match,
        topic: str,
        subject_name: str,
        reason: str,
        mastery_pct: float | None = None,
    ) -> TutorRecommendationOut:
        if card_match is not None:
            _card, concept = card_match
            return TutorRecommendationOut(
                lesson_key=concept.slug,
                topic=topic,
                subject_name=subject_name,
                mastery_pct=mastery_pct,
                reason=reason,
                pack_id=concept.pack_id,
                concept_id=concept.id,
                concept_slug=concept.slug,
                source="concept_card",
            )
        return TutorRecommendationOut(
            lesson_key=slugify_lesson_key(topic),
            topic=topic,
            subject_name=subject_name,
            mastery_pct=mastery_pct,
            reason=reason,
            source="template",
        )

    # Exam mistakes first — same chain as parent briefing and seeded unit test.
    for mc in await _student_misconceptions(db, school_id, student_id):
        student_match = await _student_weak_concept_card_for_topic(
            db, school_id=school_id, student_id=student_id, topic=mc.topic
        )
        card_match = (
            (student_match[0], student_match[1])
            if student_match is not None
            else await card_svc.resolve_approved_lesson(school_id=school_id, topic=mc.topic)
        )
        key = card_match[1].slug if card_match else slugify_lesson_key(mc.topic)
        if key in seen:
            continue
        seen.add(key)
        recs.append(
            _rec_from_card(
                card_match=card_match,
                topic=mc.topic,
                subject_name=await _subject_name_for_misconception(mc),
                reason=f"Exam mistake: {mc.common_mistake[:120]}",
            )
        )

    for topic, subject, pct in await _weak_topics(db, school_id, student_id):
        student_match = await _student_weak_concept_card_for_topic(
            db, school_id=school_id, student_id=student_id, topic=topic
        )
        card_match = (
            (student_match[0], student_match[1])
            if student_match is not None
            else await card_svc.resolve_approved_lesson(school_id=school_id, topic=topic)
        )
        key = card_match[1].slug if card_match else slugify_lesson_key(topic)
        if key in seen:
            continue
        seen.add(key)
        recs.append(
            _rec_from_card(
                card_match=card_match,
                topic=topic,
                subject_name=subject,
                mastery_pct=pct,
                reason=f"Weak topic — {pct:.0f}% mastery",
            )
        )

    # Graph weak concepts last (longitudinal spine — may predate latest exam).
    for concept, meta in await StudentWeakConceptService(db).get_weak_concepts_for_student(
        school_id=school_id, student_id=student_id
    ):
        key = concept.slug
        if key in seen:
            continue
        seen.add(key)
        pct = float(meta["mastery_pct"]) if meta and meta.get("mastery_pct") is not None else None
        reason = (
            f"Weak concept — {pct:.0f}% mastery"
            if pct is not None
            else "Weak concept from your graph"
        )
        approved_card = await card_svc.get_approved_by_slug(
            school_id=school_id,
            slug=concept.slug,
            pack_id=concept.pack_id,
        )
        recs.append(
            TutorRecommendationOut(
                lesson_key=key,
                topic=concept.title,
                subject_name="Curriculum",
                mastery_pct=pct,
                reason=reason,
                pack_id=concept.pack_id,
                concept_id=concept.id,
                concept_slug=concept.slug,
                source="concept_card" if approved_card else "weak_concept",
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

    student_card_match = await _student_weak_concept_card_for_lesson(
        db,
        school_id=school_id,
        student_id=student_id,
        lesson_key=lesson_key,
    )
    if student_card_match is not None:
        card, concept, meta = student_card_match
        mastery_pct = None
        if meta and meta.get("mastery_pct") is not None:
            mastery_pct = float(meta["mastery_pct"])
        return build_lesson_from_concept_card(
            card=card,
            concept=concept,
            subject_name=await _subject_name_from_weak_meta(
                db, school_id=school_id, meta=meta
            ),
            mastery_pct=mastery_pct,
            trigger="concept_card",
        )

    card_match = await ConceptCardService(db).get_approved_by_slug(
        school_id=school_id, slug=lesson_key
    )
    if card_match is None:
        from app.db.models.content_review import ContentReviewSource
        from app.modules.curriculum.services.content_review_service import (
            ContentReviewService,
        )

        await ContentReviewService(db).enqueue_concept_gap_by_slug(
            school_id=school_id,
            slug=lesson_key,
            created_by=student.user_id,
            source=ContentReviewSource.TUTOR_GAP,
        )

    if card_match is not None:
        card, concept = card_match
        weak = await _weak_topics(db, school_id, student_id)
        pct = None
        subject = "Curriculum"
        for t, s, p in weak:
            if (
                slugify_lesson_key(t) == lesson_key
                or slugify_lesson_key(concept.title) == lesson_key
            ):
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
    card_svc = ConceptCardService(db)
    for mc in await _student_misconceptions(db, school_id, student_id):
        if slugify_lesson_key(mc.topic) == lesson_key or (
            await card_svc.resolve_approved_lesson_key(school_id=school_id, topic=mc.topic)
        ) == lesson_key:
            resolved = await card_svc.resolve_approved_lesson_key(
                school_id=school_id, topic=mc.topic
            )
            if resolved:
                card_match = await card_svc.get_approved_by_slug(
                    school_id=school_id, slug=resolved
                )
                if card_match is not None:
                    card, concept = card_match
                    weak = await _weak_topics(db, school_id, student_id)
                    pct = None
                    subject = (
                        await db.scalar(
                            select(Subject.name).where(
                                Subject.id == mc.subject_id,
                                Subject.school_id == school_id,
                            )
                        )
                    ) or "Curriculum"
                    for t, s, p in weak:
                        if t.lower() in mc.topic.lower() or mc.topic.lower() in t.lower():
                            pct = p
                            subject = s
                            break
                    return build_lesson_from_concept_card(
                        card=card,
                        concept=concept,
                        subject_name=subject,
                        mastery_pct=pct,
                        trigger="concept_card",
                        mistake_summary=mc.common_mistake,
                    )
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
