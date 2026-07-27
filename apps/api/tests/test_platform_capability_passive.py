"""EUI Phase 1 Sprint 3 — passive Platform Capability Registry observer."""

from __future__ import annotations

from app.core.config import Settings
from app.core.platform_metrics import platform_metrics
from app.modules.eui.schemas.platform_capability import PlatformCapabilityLookupRequest
from app.modules.eui.services.platform_capability_passive import (
    EUI_CAPABILITY_REGISTRY_METRIC_TASK,
    observe_platform_capability_lookup,
    platform_capability_passive_captures,
)


def test_platform_capability_registry_feature_flag_defaults_off():
    assert Settings().EUI_PLATFORM_CAPABILITY_REGISTRY_ENABLED is False


def test_platform_capability_passive_observer_is_noop_when_disabled():
    platform_capability_passive_captures.clear()

    capture = observe_platform_capability_lookup(
        enabled=False,
        request=PlatformCapabilityLookupRequest(
            domain="mathematics",
            capability_key="numeric_normalization",
        ),
    )

    assert capture is None
    assert platform_capability_passive_captures.snapshot() == []


def test_platform_capability_passive_observer_captures_supported_lookup():
    platform_capability_passive_captures.clear()

    capture = observe_platform_capability_lookup(
        enabled=True,
        request=PlatformCapabilityLookupRequest(
            domain="mathematics",
            capability_key="numeric_normalization",
            board="CBSE",
            curriculum="NCF2023",
            grade="10",
            subject="Mathematics",
        ),
    )

    assert capture is not None
    assert capture.status == "lookup_completed"
    assert capture.result is not None
    assert capture.result.mode == "supported"
    assert platform_capability_passive_captures.snapshot()[-1] == capture
    assert f'task="{EUI_CAPABILITY_REGISTRY_METRIC_TASK}",status="lookup_completed"' in (
        platform_metrics.prometheus_text()
    )


def test_platform_capability_passive_observer_records_unsupported_safely():
    platform_capability_passive_captures.clear()

    capture = observe_platform_capability_lookup(
        enabled=True,
        request=PlatformCapabilityLookupRequest(
            domain="commerce",
            capability_key="ledger_auto_grading",
            subject="Commerce",
        ),
    )

    assert capture is not None
    assert capture.status == "unsupported"
    assert capture.result is not None
    assert capture.result.matched is False
    assert capture.result.mode == "unsupported"
    assert f'task="{EUI_CAPABILITY_REGISTRY_METRIC_TASK}",status="unsupported"' in (
        platform_metrics.prometheus_text()
    )


def test_platform_capability_passive_observer_records_conflict_passively():
    platform_capability_passive_captures.clear()

    capture = observe_platform_capability_lookup(
        enabled=True,
        request=PlatformCapabilityLookupRequest(
            domain="test",
            capability_key="conflict_resolution_probe",
            board="CBSE",
            grade="8",
            subject="Science",
        ),
    )

    assert capture is not None
    assert capture.status == "conflict"
    assert capture.result is not None
    assert capture.result.conflict is True
    assert capture.result.mode == "manual_review"


def test_platform_capability_passive_observer_isolates_exceptions():
    class BrokenLookupService:
        def lookup(self, _request):
            raise RuntimeError("synthetic capability lookup failure")

    capture = observe_platform_capability_lookup(
        enabled=True,
        request=PlatformCapabilityLookupRequest(
            domain="mathematics",
            capability_key="numeric_normalization",
        ),
        lookup_service=BrokenLookupService(),  # type: ignore[arg-type]
    )

    assert capture is None
    assert (
        f'task="{EUI_CAPABILITY_REGISTRY_METRIC_TASK}",status="lookup_failed"'
        in platform_metrics.prometheus_text()
    )
