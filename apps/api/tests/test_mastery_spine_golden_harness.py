import json
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.academic import AcademicYear
from app.db.models.curriculum_pack import CurriculumChapter, CurriculumTopic
from app.db.models.school import School
from app.db.models.user import User
from app.modules.mastery.schemas.mastery_spine import MasterySpineResolutionReference
from app.modules.mastery.services.mastery_spine_resolver import MasterySpineResolver
from tests.test_mastery_spine_resolver import _seed_spine_curriculum

MASTERY_SPINE_CASES_PATH = (
    Path(__file__).parent
    / "golden"
    / "learning_intelligence"
    / "mastery_spine_resolution_cases.json"
)


def _load_cases() -> dict:
    with MASTERY_SPINE_CASES_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


@pytest.mark.asyncio
async def test_mastery_spine_golden_cases_execute_deterministically(
    db_session: AsyncSession,
    test_school: School,
    academic_year: AcademicYear,
    admin_user: User,
):
    data = _load_cases()

    assert data["version"] == "mastery-spine-resolution-v1"
    case_ids: set[str] = set()
    seed = await _seed_spine_curriculum(
        db_session,
        school=test_school,
        year=academic_year,
        admin=admin_user,
        section="MSG",
    )
    resolver = MasterySpineResolver(db_session)

    for case in data["cases"]:
        assert case["id"] not in case_ids
        case_ids.add(case["id"])

        if case["scenario"] == "duplicate_topic_label":
            second_chapter = CurriculumChapter(
                school_id=test_school.id,
                pack_id=seed.pack.id,
                number="6",
                title="Light",
                order_index=10,
            )
            db_session.add(second_chapter)
            await db_session.flush()
            db_session.add(
                CurriculumTopic(
                    school_id=test_school.id,
                    chapter_id=second_chapter.id,
                    title="Measuring Length",
                    order_index=0,
                )
            )
            await db_session.flush()

        reference = _reference_for_case(
            case,
            school=test_school,
            year=academic_year,
            seed=seed,
        )
        first = await resolver.resolve(reference)
        second = await resolver.resolve(reference)

        assert first == second, case["id"]
        expected = case["expected"]
        assert first.resolution_status == expected["resolution_status"], case["id"]
        assert first.authority_posture == expected["authority_posture"], case["id"]
        assert first.spine_level == expected["spine_level"], case["id"]
        assert first.metadata["source_switching"] is expected["source_switching"], case["id"]
        if "label" in expected:
            assert first.label == expected["label"], case["id"]
        if "ambiguity_reason" in expected:
            assert first.ambiguities
            assert first.ambiguities[0].reason == expected["ambiguity_reason"], case["id"]


def _reference_for_case(
    case: dict,
    *,
    school: School,
    year: AcademicYear,
    seed,
) -> MasterySpineResolutionReference:
    scenario = case["scenario"]
    raw_label = (case.get("input") or {}).get("raw_label")
    if scenario == "explicit_topic_id":
        return MasterySpineResolutionReference(
            school_id=school.id,
            academic_year_id=year.id,
            class_id=seed.class_.id,
            subject_id=seed.subject.id,
            topic_id=seed.topic.id,
            source="golden_explicit_topic",
        )
    if scenario in {"exact_concept_label", "duplicate_topic_label"}:
        return MasterySpineResolutionReference(
            school_id=school.id,
            academic_year_id=year.id,
            class_id=seed.class_.id,
            subject_id=seed.subject.id,
            pack_id=seed.pack.id,
            raw_label=raw_label,
            source=f"golden_{scenario}",
        )
    if scenario == "legacy_fallback_without_pack_context":
        return MasterySpineResolutionReference(
            school_id=school.id,
            raw_label=raw_label,
            source="golden_legacy_fallback",
        )
    return MasterySpineResolutionReference(
        school_id=school.id,
        source="golden_unresolved",
    )
