"""EUI Phase 1 Sprint 1 — deterministic Educational Identity resolver."""

from __future__ import annotations

from dataclasses import dataclass

import pytest
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
from app.modules.eui.schemas.educational_identity import EducationalIdentityReference
from app.modules.eui.services.educational_identity_cache import educational_identity_cache
from app.modules.eui.services.educational_identity_resolver import (
    EducationalIdentityAmbiguous,
    EducationalIdentityResolver,
)


@dataclass(frozen=True)
class _IdentitySeed:
    class_: Class
    subject: Subject
    pack: CurriculumPack
    chapter: CurriculumChapter
    topic: CurriculumTopic
    concept: CurriculumConcept
    outcome: CurriculumLearningOutcome


async def _seed_identity_curriculum(
    db: AsyncSession,
    *,
    school: School,
    year: AcademicYear,
    admin: User,
    grade: str = "Grade 6",
    section: str = "Z",
    subject_name: str = "Science",
    board: str = "CBSE",
    version: int = 1,
) -> _IdentitySeed:
    class_ = Class(
        school_id=school.id,
        grade=grade,
        section=section,
        academic_year_id=year.id,
    )
    db.add(class_)
    await db.flush()

    subject = Subject(
        school_id=school.id,
        class_id=class_.id,
        name=subject_name,
        code=subject_name[:3].upper(),
    )
    db.add(subject)
    await db.flush()

    pack = CurriculumPack(
        school_id=school.id,
        class_id=class_.id,
        subject_id=subject.id,
        academic_year_id=year.id,
        board=board,
        book_title="NCF2023",
        edition="2024",
        version=version,
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
        title="Measuring Length",
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

    return _IdentitySeed(
        class_=class_,
        subject=subject,
        pack=pack,
        chapter=chapter,
        topic=topic,
        concept=concept,
        outcome=outcome,
    )


@pytest.mark.asyncio
async def test_resolver_resolves_concept_to_canonical_identity(
    db_session: AsyncSession,
    test_school: School,
    academic_year: AcademicYear,
    admin_user: User,
):
    educational_identity_cache.clear()
    seed = await _seed_identity_curriculum(
        db_session,
        school=test_school,
        year=academic_year,
        admin=admin_user,
    )
    resolver = EducationalIdentityResolver(db_session)

    identity = await resolver.resolve(
        EducationalIdentityReference(school_id=test_school.id, concept_id=seed.concept.id)
    )

    assert (
        identity.id
        == "ei://cbse/ncf2023/2024/g6/science/ch05/topic-measuring-length/concept-si-units"
    )
    assert identity.tenant_id == test_school.id
    assert identity.concepts == ("SI Units",)
    assert identity.metadata["entity_type"] == "concept"
    assert identity.provenance.source == "curriculum_pack"
    assert identity.provenance.metadata["authorization"] == "EUI-PH1-AUTH-001"


@pytest.mark.asyncio
async def test_resolver_cache_records_hit_after_first_resolution(
    db_session: AsyncSession,
    test_school: School,
    academic_year: AcademicYear,
    admin_user: User,
):
    educational_identity_cache.clear()
    seed = await _seed_identity_curriculum(
        db_session,
        school=test_school,
        year=academic_year,
        admin=admin_user,
        section="Y",
    )
    resolver = EducationalIdentityResolver(db_session)
    reference = EducationalIdentityReference(school_id=test_school.id, topic_id=seed.topic.id)

    first = await resolver.resolve(reference)
    mid = educational_identity_cache.snapshot()
    second = await resolver.resolve(reference)
    after = educational_identity_cache.snapshot()

    assert first == second
    assert mid.misses >= 1
    assert after.hits > mid.hits


@pytest.mark.asyncio
async def test_resolver_builds_read_only_registry_for_pack(
    db_session: AsyncSession,
    test_school: School,
    academic_year: AcademicYear,
    admin_user: User,
):
    educational_identity_cache.clear()
    seed = await _seed_identity_curriculum(
        db_session,
        school=test_school,
        year=academic_year,
        admin=admin_user,
        section="X",
    )
    resolver = EducationalIdentityResolver(db_session)

    registry = await resolver.build_registry_for_pack(
        school_id=test_school.id,
        pack_id=seed.pack.id,
    )

    concept_identity = registry.resolve_alias(f"concept:{seed.concept.id}")
    assert concept_identity is not None
    assert concept_identity.metadata["entity_type"] == "concept"
    assert registry.get(concept_identity.id) == concept_identity
    outcome_identity = registry.resolve_alias(f"learning_outcome:{seed.outcome.id}")
    assert outcome_identity is not None
    assert outcome_identity.metadata["entity_type"] == "learning_outcome"

    aliases_copy = registry.aliases()
    aliases_copy["new"] = concept_identity.id
    assert registry.resolve_alias("new") is None

    with pytest.raises(TypeError):
        registry._aliases["new"] = concept_identity.id  # type: ignore[index]


@pytest.mark.asyncio
async def test_resolver_resolves_raw_label_with_hints(
    db_session: AsyncSession,
    test_school: School,
    academic_year: AcademicYear,
    admin_user: User,
):
    educational_identity_cache.clear()
    await _seed_identity_curriculum(
        db_session,
        school=test_school,
        year=academic_year,
        admin=admin_user,
        section="W",
    )
    resolver = EducationalIdentityResolver(db_session)

    identity = await resolver.resolve(
        EducationalIdentityReference(
            school_id=test_school.id,
            raw_label="Motion and Measurement of Distances",
            board="CBSE",
            grade="Grade 6",
            subject="Science",
        )
    )

    assert identity.metadata["entity_type"] == "chapter"
    assert identity.chapter == "Motion and Measurement of Distances"


@pytest.mark.asyncio
async def test_resolver_flags_ambiguous_raw_label(
    db_session: AsyncSession,
    test_school: School,
    academic_year: AcademicYear,
    admin_user: User,
):
    educational_identity_cache.clear()
    await _seed_identity_curriculum(
        db_session,
        school=test_school,
        year=academic_year,
        admin=admin_user,
        section="V",
        subject_name="Science",
    )
    await _seed_identity_curriculum(
        db_session,
        school=test_school,
        year=academic_year,
        admin=admin_user,
        section="U",
        subject_name="Physics",
        version=2,
    )
    resolver = EducationalIdentityResolver(db_session)

    with pytest.raises(EducationalIdentityAmbiguous):
        await resolver.resolve(
            EducationalIdentityReference(
                school_id=test_school.id,
                raw_label="Motion and Measurement of Distances",
                board="CBSE",
                grade="Grade 6",
            )
        )
