import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.academic import AcademicYear
from app.db.models.school import School
from app.db.models.user import User
from app.modules.mastery.schemas.mastery_spine import MasterySpineResolutionReference
from app.modules.mastery.services.mastery_spine_passive import (
    observe_mastery_spine_resolution,
)
from app.modules.mastery.services.mastery_spine_resolver import MasterySpineResolver
from tests.test_mastery_spine_resolver import _seed_spine_curriculum


@pytest.mark.asyncio
async def test_passive_observer_is_noop_when_disabled(
    db_session: AsyncSession,
    test_school: School,
):
    result = await observe_mastery_spine_resolution(
        enabled=False,
        resolver=MasterySpineResolver(db_session),
        reference=MasterySpineResolutionReference(
            school_id=test_school.id,
            raw_label="Algebra",
        ),
    )

    assert result is None


@pytest.mark.asyncio
async def test_passive_observer_returns_internal_evidence_when_enabled(
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
        section="MSP",
    )

    result = await observe_mastery_spine_resolution(
        enabled=True,
        resolver=MasterySpineResolver(db_session),
        reference=MasterySpineResolutionReference(
            school_id=test_school.id,
            academic_year_id=academic_year.id,
            class_id=seed.class_.id,
            subject_id=seed.subject.id,
            topic_id=seed.topic.id,
            source="passive_test",
        ),
    )

    assert result is not None
    assert result.resolution_status == "resolved"
    assert result.topic_id == seed.topic.id
    assert result.metadata["passive"] is True
    assert result.metadata["source_switching"] is False
