"""Passive Platform Capability Registry lookup observer."""

from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass
from threading import Lock

from app.core.platform_metrics import platform_metrics
from app.modules.eui.schemas.platform_capability import (
    PlatformCapabilityLookupRequest,
    PlatformCapabilityLookupResult,
)
from app.modules.eui.services.platform_capability_lookup import PlatformCapabilityLookupService

logger = logging.getLogger(__name__)

EUI_CAPABILITY_REGISTRY_METRIC_TASK = "eui_capability_registry"


@dataclass(frozen=True)
class PlatformCapabilityPassiveCapture:
    domain: str
    capability_key: str
    status: str
    duration_ms: float
    result: PlatformCapabilityLookupResult | None = None
    error: str | None = None


class PlatformCapabilityPassiveCaptureRegistry:
    """Bounded in-memory capture store for passive verification only."""

    def __init__(self, *, max_entries: int = 100) -> None:
        self._items: deque[PlatformCapabilityPassiveCapture] = deque(maxlen=max_entries)
        self._lock = Lock()

    def record(self, capture: PlatformCapabilityPassiveCapture) -> None:
        with self._lock:
            self._items.append(capture)

    def snapshot(self) -> list[PlatformCapabilityPassiveCapture]:
        with self._lock:
            return list(self._items)

    def clear(self) -> None:
        with self._lock:
            self._items.clear()


platform_capability_passive_captures = PlatformCapabilityPassiveCaptureRegistry()


def observe_platform_capability_lookup(
    *,
    enabled: bool,
    request: PlatformCapabilityLookupRequest,
    lookup_service: PlatformCapabilityLookupService | None = None,
) -> PlatformCapabilityPassiveCapture | None:
    """Run Platform Capability Registry lookup passively behind a feature flag."""

    if not enabled:
        return None

    platform_metrics.record_job_event(
        task=EUI_CAPABILITY_REGISTRY_METRIC_TASK,
        status="lookup_invoked",
    )
    started = time.perf_counter()
    try:
        service = lookup_service or PlatformCapabilityLookupService()
        platform_metrics.record_job_event(
            task=EUI_CAPABILITY_REGISTRY_METRIC_TASK,
            status="loaded",
        )
        result = service.lookup(request)
    except Exception as exc:
        duration_ms = _duration_ms(started)
        platform_metrics.record_job_event(
            task=EUI_CAPABILITY_REGISTRY_METRIC_TASK,
            status="lookup_failed",
            duration_ms=duration_ms,
        )
        logger.exception(
            "Platform Capability Registry passive lookup failed",
            extra={
                "eui_capability_domain": request.domain,
                "eui_capability_key": request.capability_key,
                "eui_duration_ms": round(duration_ms, 2),
            },
        )
        capture = PlatformCapabilityPassiveCapture(
            domain=request.domain,
            capability_key=request.capability_key,
            status="lookup_failed",
            duration_ms=duration_ms,
            error=str(exc),
        )
        platform_capability_passive_captures.record(capture)
        return None

    duration_ms = _duration_ms(started)
    status = _status_for_result(result)
    platform_metrics.record_job_event(
        task=EUI_CAPABILITY_REGISTRY_METRIC_TASK,
        status=status,
        duration_ms=duration_ms,
    )
    if result.fallback_reason:
        platform_metrics.record_job_event(
            task=EUI_CAPABILITY_REGISTRY_METRIC_TASK,
            status="fallback",
        )

    capture = PlatformCapabilityPassiveCapture(
        domain=request.domain,
        capability_key=request.capability_key,
        status=status,
        duration_ms=duration_ms,
        result=result,
    )
    platform_capability_passive_captures.record(capture)
    logger.info(
        "Platform Capability Registry passive lookup completed",
        extra={
            "eui_capability_domain": request.domain,
            "eui_capability_key": request.capability_key,
            "eui_capability_status": status,
            "eui_capability_mode": result.mode,
            "eui_duration_ms": round(duration_ms, 2),
        },
    )
    return capture


def _status_for_result(result: PlatformCapabilityLookupResult) -> str:
    if result.conflict:
        return "conflict"
    if not result.matched:
        return "unsupported"
    if result.mode == "unsupported":
        return "unsupported"
    return "lookup_completed"


def _duration_ms(started: float) -> float:
    return (time.perf_counter() - started) * 1000
