"""EUI Phase 1 Sprint 2 — passive Educational Context runtime observer."""

from __future__ import annotations

import uuid

import pytest

from app.core.config import Settings
from app.core.platform_metrics import platform_metrics
from app.modules.eui.schemas.educational_context import EducationalContextReference
from app.modules.eui.schemas.educational_identity import (
    EducationalIdentity,
    EducationalIdentityProvenance,
)
from app.modules.eui.services.educational_context_cache import educational_context_cache
from app.modules.eui.services.educational_context_passive import (
    EUI_CONTEXT_METRIC_TASK,
    educational_context_passive_captures,
    observe_educational_context_resolution,
)


def test_eui_context_feature_flag_defaults_off():
    assert Settings().EUI_CONTEXT_PASSIVE_ENABLED is False


@pytest.mark.asyncio
async def test_context_passive_observer_is_noop_when_disabled():
    educational_context_passive_captures.clear()

    capture = await observe_educational_context_resolution(
        enabled=False,
        reference=EducationalContextReference(
            school_id=uuid.uuid4(),
            candidate_context_ids=("ctx-a", "ctx-b"),
        ),
    )

    assert capture is None
    assert educational_context_passive_captures.snapshot() == []


@pytest.mark.asyncio
async def test_context_passive_observer_captures_success_without_behavior_dependency():
    educational_context_cache.clear()
    educational_context_passive_captures.clear()
    school_id = uuid.uuid4()

    capture = await observe_educational_context_resolution(
        enabled=True,
        reference=EducationalContextReference(
            school_id=school_id,
            educational_identity=_identity(school_id),
            assessment_mode="unit_test",
        ),
    )

    assert capture is not None
    assert capture.status == "completed"
    assert capture.context is not None
    assert capture.context.assessment_mode == "unit_test"
    assert educational_context_passive_captures.snapshot()[-1] == capture
    assert f'task="{EUI_CONTEXT_METRIC_TASK}",status="completed"' in (
        platform_metrics.prometheus_text()
    )


@pytest.mark.asyncio
async def test_context_passive_observer_records_conflict_passively():
    educational_context_cache.clear()
    educational_context_passive_captures.clear()
    school_id = uuid.uuid4()

    capture = await observe_educational_context_resolution(
        enabled=True,
        reference=EducationalContextReference(
            school_id=school_id,
            educational_identity=_identity(school_id),
            grade="Grade 7",
        ),
    )

    assert capture is not None
    assert capture.status == "conflict"
    assert capture.context is not None
    assert capture.context.grade == "Grade 6"
    assert capture.context.conflicts[0].field == "grade"
    assert f'task="{EUI_CONTEXT_METRIC_TASK}",status="conflict"' in (
        platform_metrics.prometheus_text()
    )


@pytest.mark.asyncio
async def test_context_passive_observer_records_ambiguity_passively():
    educational_context_cache.clear()
    educational_context_passive_captures.clear()

    capture = await observe_educational_context_resolution(
        enabled=True,
        reference=EducationalContextReference(
            school_id=uuid.uuid4(),
            candidate_context_ids=("ctx-a", "ctx-b"),
        ),
    )

    assert capture is not None
    assert capture.status == "ambiguous"
    assert capture.context is not None
    assert capture.context.resolution_status == "ambiguous"


@pytest.mark.asyncio
async def test_context_passive_observer_isolates_unexpected_exceptions():
    class BrokenResolver:
        async def resolve(self, _reference):
            raise RuntimeError("synthetic context resolver failure")

    capture = await observe_educational_context_resolution(
        enabled=True,
        reference=EducationalContextReference(school_id=uuid.uuid4(), grade="Grade 6"),
        resolver=BrokenResolver(),  # type: ignore[arg-type]
    )

    assert capture is None
    assert (
        f'task="{EUI_CONTEXT_METRIC_TASK}",status="failed"'
        in platform_metrics.prometheus_text()
    )


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
