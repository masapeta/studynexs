from __future__ import annotations

from dataclasses import dataclass

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.academic import AcademicYear, Class, Subject
from app.db.models.curriculum_pack import (
    CurriculumChapter,
    CurriculumLearningOutcome,
    CurriculumPack,
    CurriculumTopic,
    PackStatus,
)
from app.db.models.knowledge_graph import CurriculumConcept
from app.db.models.school import School
from app.db.models.user import User
from app.modules.mastery.schemas.mastery_spine import MasterySpineResolutionReference
from app.modules.mastery.services.mastery_spine_resolver import MasterySpineResolver


@dataclass(frozen=True)
class _SpineSeed:
    class_: Class
    subject: Subject
    pack: CurriculumPack
    chapter: CurriculumChapter
    topic: CurriculumTopic
    concept: CurriculumConcept
    outcome: CurriculumLearningOutcome


async def _seed_spine_curriculum(
    db: AsyncSession,
    *,
    school: School,
    year: AcademicYear,
    admin: User,
    section: str = "MS",
    topic_title: str = "Measuring Length",
) -> _SpineSeed:
    class_ = Class(
        school_id=school.id,
        grade="Grade 6",
        section=section,
        academic_year_id=year.id,
    )
    db.add(class_)
    await db.flush()

    subject = Subject(
        school_id=school.id,
        class_id=class_.id,
        name="Science",
        code=f"SCI-{section}",
    )
    db.add(subject)
    await db.flush()

    pack = CurriculumPack(
        school_id=school.id,
        class_id=class_.id,
        subject_id=subject.id,
        academic_year_id=year.id,
        board="CBSE",
        book_title="NCF2023",
        edition="2024",
        version=1,
        status=PackStatus.APPROVED,
        created_by=admin.id,
        approved_by=admin.id,
    )
    db.add(pack)
    await db.flush()

    chapter = CurriculumChapter(
        school_id=school.id,
        pack_id=pack.id,
        number="5",
        title="Motion and Measurement of Distances",
        order_index=0,
    )
    db.add(chapter)
    await db.flush()

    topic = CurriculumTopic(
        school_id=school.id,
        chapter_id=chapter.id,
        title=topic_title,
        concepts=["Standard Units", "SI Units"],
        order_index=0,
    )
    db.add(topic)
    await db.flush()

    concept = CurriculumConcept(
        school_id=school.id,
        pack_id=pack.id,
        topic_id=topic.id,
        slug="si-units",
        title="SI Units",
        order_index=0,
    )
    db.add(concept)
    await db.flush()

    outcome = CurriculumLearningOutcome(
        school_id=school.id,
        topic_id=topic.id,
        chapter_id=None,
        code="LO-5.1",
        description="Measure length using standard SI units.",
        order_index=0,
    )
    db.add(outcome)
    await db.flush()

    return _SpineSeed(
        class_=class_,
        subject=subject,
        pack=pack,
        chapter=chapter,
        topic=topic,
        concept=concept,
        outcome=outcome,
    )


@pytest.mark.asyncio
async def test_resolver_resolves_explicit_topic_id_to_canonical_spine(
    db_session: AsyncSession,
    test_school: School,
    academic_year: AcademicYear,
    admin_user: User,
):
    seed = await _seed_spine_curriculum(
        db_session,
        school=test_school,
        year=academic_year,
        admin=admin_user,
        section="MS1",
    )

    result = await MasterySpineResolver(db_session).resolve(
        MasterySpineResolutionReference(
            school_id=test_school.id,
            academic_year_id=academic_year.id,
            class_id=seed.class_.id,
            subject_id=seed.subject.id,
            topic_id=seed.topic.id,
            source="test_explicit_topic",
        )
    )

    assert result.resolution_status == "resolved"
    assert result.authority_posture == "canonical"
    assert result.spine_level == "topic"
    assert result.topic_id == seed.topic.id
    assert result.educational_identity_id is not None
    assert result.educational_identity_id.startswith("ei://cbse/ncf2023/2024/g6/science")
    assert result.metadata["source_switching"] is False


@pytest.mark.asyncio
async def test_resolver_resolves_label_to_concept_inside_approved_pack(
    db_session: AsyncSession,
    test_school: School,
    academic_year: AcademicYear,
    admin_user: User,
):
    seed = await _seed_spine_curriculum(
        db_session,
        school=test_school,
        year=academic_year,
        admin=admin_user,
        section="MS2",
    )

    result = await MasterySpineResolver(db_session).resolve(
        MasterySpineResolutionReference(
            school_id=test_school.id,
            academic_year_id=academic_year.id,
            class_id=seed.class_.id,
            subject_id=seed.subject.id,
            pack_id=seed.pack.id,
            raw_label="SI Units",
            source="test_label",
        )
    )

    assert result.resolution_status == "resolved"
    assert result.spine_level == "concept"
    assert result.concept_id == seed.concept.id
    assert result.topic_id == seed.topic.id
    assert result.label == "Measuring Length"


@pytest.mark.asyncio
async def test_resolver_returns_ambiguity_for_duplicate_topic_labels(
    db_session: AsyncSession,
    test_school: School,
    academic_year: AcademicYear,
    admin_user: User,
):
    seed = await _seed_spine_curriculum(
        db_session,
        school=test_school,
        year=academic_year,
        admin=admin_user,
        section="MS3",
    )
    second_chapter = CurriculumChapter(
        school_id=test_school.id,
        pack_id=seed.pack.id,
        number="6",
        title="Light",
        order_index=1,
    )
    db_session.add(second_chapter)
    await db_session.flush()
    duplicate_topic = CurriculumTopic(
        school_id=test_school.id,
        chapter_id=second_chapter.id,
        title="Measuring Length",
        order_index=0,
    )
    db_session.add(duplicate_topic)
    await db_session.flush()

    result = await MasterySpineResolver(db_session).resolve(
        MasterySpineResolutionReference(
            school_id=test_school.id,
            academic_year_id=academic_year.id,
            class_id=seed.class_.id,
            subject_id=seed.subject.id,
            pack_id=seed.pack.id,
            raw_label="Measuring Length",
            source="test_duplicate_label",
        )
    )

    assert result.resolution_status == "ambiguous"
    assert result.authority_posture == "ambiguous"
    assert result.ambiguities[0].reason == "multiple_exact_label_matches"
    assert len(result.ambiguities[0].candidates) == 2


@pytest.mark.asyncio
async def test_resolver_preserves_legacy_fallback_when_no_pack_context(
    db_session: AsyncSession,
    test_school: School,
):
    result = await MasterySpineResolver(db_session).resolve(
        MasterySpineResolutionReference(
            school_id=test_school.id,
            raw_label="  Old   Topic  ",
            source="test_legacy_topic",
        )
    )

    assert result.resolution_status == "legacy_fallback"
    assert result.authority_posture == "legacy"
    assert result.spine_level == "label"
    assert result.label == "Old Topic"
    assert result.topic_id is None
    assert result.educational_identity_id is None


@pytest.mark.asyncio
async def test_resolver_is_read_only_for_curriculum_entities(
    db_session: AsyncSession,
    test_school: School,
    academic_year: AcademicYear,
    admin_user: User,
):
    seed = await _seed_spine_curriculum(
        db_session,
        school=test_school,
        year=academic_year,
        admin=admin_user,
        section="MS4",
    )
    before = await db_session.scalar(
        select(func.count()).select_from(CurriculumTopic).where(
            CurriculumTopic.school_id == test_school.id
        )
    )

    await MasterySpineResolver(db_session).resolve(
        MasterySpineResolutionReference(
            school_id=test_school.id,
            academic_year_id=academic_year.id,
            class_id=seed.class_.id,
            subject_id=seed.subject.id,
            pack_id=seed.pack.id,
            raw_label="Measuring Length",
            source="test_read_only",
        )
    )

    after = await db_session.scalar(
        select(func.count()).select_from(CurriculumTopic).where(
            CurriculumTopic.school_id == test_school.id
        )
    )
    assert after == before
