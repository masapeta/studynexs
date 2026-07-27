"""EUI Phase 1 Sprint 2 — deterministic Educational Context resolver."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.academic import AcademicYear
from app.db.models.school import School
from app.db.models.user import User
from app.modules.eui.schemas.educational_context import EducationalContextReference
from app.modules.eui.schemas.educational_identity import (
    EducationalIdentity,
    EducationalIdentityProvenance,
)
from app.modules.eui.services.educational_context_cache import educational_context_cache
from app.modules.eui.services.educational_context_resolver import (
    EducationalContextNotFound,
    EducationalContextResolver,
)
from tests.test_educational_identity_resolver import _seed_identity_curriculum


@pytest.mark.asyncio
async def test_context_resolver_uses_identity_and_records_field_sources():
    educational_context_cache.clear()
    school_id = uuid.uuid4()
    identity = _identity(school_id)
    resolver = EducationalContextResolver()

    context = await resolver.resolve(
        EducationalContextReference(
            school_id=school_id,
            educational_identity=identity,
            assessment_mode="unit_test",
            evidence_posture="passive",
        )
    )

    assert context.resolution_status == "resolved"
    assert context.tenant_id == school_id
    assert context.board == "CBSE"
    assert context.grade == "Grade 6"
    assert context.subject == "Science"
    assert context.assessment_mode == "unit_test"
    assert context.field_sources["grade"] == "educational_identity"
    assert context.field_sources["assessment_mode"] == "runtime_metadata"
    assert context.metadata["authorization"] == "EUI-PH1-SP2-AUTH-001"


@pytest.mark.asyncio
async def test_context_precedence_records_conflict_without_overriding_identity():
    educational_context_cache.clear()
    school_id = uuid.uuid4()
    identity = _identity(school_id)
    resolver = EducationalContextResolver()

    context = await resolver.resolve(
        EducationalContextReference(
            school_id=school_id,
            educational_identity=identity,
            grade="Grade 7",
            subject="Physics",
            assessment_mode="homework",
        )
    )

    assert context.resolution_status == "resolved_with_conflicts"
    assert context.grade == "Grade 6"
    assert context.subject == "Science"
    assert {conflict.field for conflict in context.conflicts} == {"grade", "subject"}
    grade_conflict = next(conflict for conflict in context.conflicts if conflict.field == "grade")
    assert grade_conflict.chosen_source == "educational_identity"
    assert grade_conflict.rejected_source == "runtime_metadata"
    assert grade_conflict.rejected_value == "Grade 7"


@pytest.mark.asyncio
async def test_context_explicit_reference_precedence_wins_over_identity_metadata():
    educational_context_cache.clear()
    school_id = uuid.uuid4()
    explicit_pack_id = uuid.uuid4()
    identity = _identity(school_id)
    resolver = EducationalContextResolver()

    context = await resolver.resolve(
        EducationalContextReference(
            school_id=school_id,
            educational_identity=identity,
            pack_id=explicit_pack_id,
        )
    )

    assert context.resolution_status == "resolved_with_conflicts"
    assert context.curriculum_pack_id == explicit_pack_id
    assert context.field_sources["curriculum_pack_id"] == "explicit_artifact_reference"
    pack_conflict = next(
        conflict for conflict in context.conflicts if conflict.field == "curriculum_pack_id"
    )
    assert pack_conflict.chosen_source == "explicit_artifact_reference"
    assert pack_conflict.rejected_source == "curriculum_pack_metadata"


@pytest.mark.asyncio
async def test_context_resolver_returns_non_authoritative_ambiguity():
    educational_context_cache.clear()
    school_id = uuid.uuid4()
    resolver = EducationalContextResolver()

    context = await resolver.resolve(
        EducationalContextReference(
            school_id=school_id,
            candidate_context_ids=("ctx-grade-6", "ctx-grade-7"),
        )
    )

    assert context.resolution_status == "ambiguous"
    assert context.tenant_id == school_id
    assert context.ambiguities[0].reason == "multiple_context_candidates"
    assert context.ambiguities[0].candidates == ("ctx-grade-6", "ctx-grade-7")
    assert context.educational_identity_id is None


@pytest.mark.asyncio
async def test_context_resolver_can_resolve_existing_identity_reference_read_only(
    db_session: AsyncSession,
    test_school: School,
    academic_year: AcademicYear,
    admin_user: User,
):
    educational_context_cache.clear()
    seed = await _seed_identity_curriculum(
        db_session,
        school=test_school,
        year=academic_year,
        admin=admin_user,
        section="C",
    )
    resolver = EducationalContextResolver(db_session)

    context = await resolver.resolve(
        EducationalContextReference(
            school_id=test_school.id,
            topic_id=seed.topic.id,
            assessment_mode="unit_test",
            language_medium="English",
        )
    )

    assert context.resolution_status == "resolved"
    assert context.tenant_id == test_school.id
    assert context.curriculum_pack_id == seed.pack.id
    assert context.educational_identity_id is not None
    assert context.topic == "Measuring Length"
    assert context.assessment_mode == "unit_test"
    assert context.language_medium == "English"

    mid = educational_context_cache.snapshot()
    again = await resolver.resolve(
        EducationalContextReference(
            school_id=test_school.id,
            topic_id=seed.topic.id,
            assessment_mode="unit_test",
            language_medium="English",
        )
    )
    after = educational_context_cache.snapshot()
    assert again == context
    assert after.hits > mid.hits


@pytest.mark.asyncio
async def test_context_resolver_rejects_incomplete_reference():
    educational_context_cache.clear()
    resolver = EducationalContextResolver()

    with pytest.raises(EducationalContextNotFound):
        await resolver.resolve(EducationalContextReference(school_id=uuid.uuid4()))


def _identity(school_id: uuid.UUID) -> EducationalIdentity:
    return EducationalIdentity(
        id="ei://cbse/ncf2023/2024/g6/science/ch05/topic-measuring-length",
        tenant_id=school_id,
        board="CBSE",
        curriculum="NCF2023",
        curriculum_version="2024",
        grade="Grade 6",
        subject="Science",
        chapter="Motion and Measurement of Distances",
        topic="Measuring Length",
        concepts=("Standard Units", "SI Units"),
        metadata={"pack_id": str(uuid.uuid4()), "entity_type": "topic"},
        provenance=EducationalIdentityProvenance(
            source="curriculum_pack",
            source_id="topic-1",
            source_version="2024",
            resolved_from="topic",
        ),
    )
