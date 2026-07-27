"""EUI Phase 1 Sprint 1 — passive Educational Identity runtime observer."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.platform_metrics import platform_metrics
from app.modules.eui.schemas.educational_identity import EducationalIdentityReference
from app.modules.eui.services.educational_identity_cache import educational_identity_cache
from app.modules.eui.services.educational_identity_passive import (
    EUI_IDENTITY_METRIC_TASK,
    educational_identity_passive_captures,
    observe_educational_identity_resolution,
)
from tests.test_educational_identity_resolver import _seed_identity_curriculum


def test_eui_identity_feature_flag_defaults_off():
    assert Settings().EUI_IDENTITY_PASSIVE_ENABLED is False


@pytest.mark.asyncio
async def test_passive_observer_is_noop_when_disabled(
    db_session: AsyncSession,
    test_school,
):
    educational_identity_passive_captures.clear()

    capture = await observe_educational_identity_resolution(
        enabled=False,
        db=db_session,
        reference=EducationalIdentityReference(school_id=test_school.id, raw_label="Anything"),
    )

    assert capture is None
    assert educational_identity_passive_captures.snapshot() == []


@pytest.mark.asyncio
async def test_passive_observer_captures_success_without_behavior_dependency(
    db_session: AsyncSession,
    test_school,
    academic_year,
    admin_user,
):
    educational_identity_cache.clear()
    educational_identity_passive_captures.clear()
    seed = await _seed_identity_curriculum(
        db_session,
        school=test_school,
        year=academic_year,
        admin=admin_user,
        section="T",
    )

    capture = await observe_educational_identity_resolution(
        enabled=True,
        db=db_session,
        reference=EducationalIdentityReference(school_id=test_school.id, topic_id=seed.topic.id),
    )

    assert capture is not None
    assert capture.status == "completed"
    assert capture.identity is not None
    assert capture.identity.topic == "Measuring Length"
    assert educational_identity_passive_captures.snapshot()[-1] == capture
    assert f'task="{EUI_IDENTITY_METRIC_TASK}",status="completed"' in (
        platform_metrics.prometheus_text()
    )


@pytest.mark.asyncio
async def test_passive_observer_isolates_unexpected_exceptions(
    db_session: AsyncSession,
    test_school,
):
    class BrokenResolver:
        async def resolve(self, _reference):
            raise RuntimeError("synthetic resolver failure")

    capture = await observe_educational_identity_resolution(
        enabled=True,
        db=db_session,
        reference=EducationalIdentityReference(school_id=test_school.id, raw_label="Anything"),
        resolver=BrokenResolver(),  # type: ignore[arg-type]
    )

    assert capture is None
    assert (
        f'task="{EUI_IDENTITY_METRIC_TASK}",status="failed"'
        in platform_metrics.prometheus_text()
    )
