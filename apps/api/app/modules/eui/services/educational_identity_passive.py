"""Passive Educational Identity runtime observer.

This module mirrors the AEI passive-integration posture: failures are isolated,
output is captured only for verification, and no production consumer depends on
the result.
"""

from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass
from threading import Lock

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.platform_metrics import platform_metrics
from app.modules.eui.schemas.educational_identity import (
    EducationalIdentity,
    EducationalIdentityReference,
)
from app.modules.eui.services.educational_identity_cache import educational_identity_cache
from app.modules.eui.services.educational_identity_resolver import (
    EducationalIdentityAmbiguous,
    EducationalIdentityNotFound,
    EducationalIdentityResolver,
)

logger = logging.getLogger(__name__)

EUI_IDENTITY_METRIC_TASK = "eui_identity_resolver"


@dataclass(frozen=True)
class EducationalIdentityPassiveCapture:
    reference_kind: str
    status: str
    duration_ms: float
    identity: EducationalIdentity | None = None
    error: str | None = None
    cache_hits: int = 0
    cache_misses: int = 0


class EducationalIdentityPassiveCaptureRegistry:
    """Bounded in-memory capture store for passive verification only."""

    def __init__(self, *, max_entries: int = 100) -> None:
        self._items: deque[EducationalIdentityPassiveCapture] = deque(maxlen=max_entries)
        self._lock = Lock()

    def record(self, capture: EducationalIdentityPassiveCapture) -> None:
        with self._lock:
            self._items.append(capture)

    def snapshot(self) -> list[EducationalIdentityPassiveCapture]:
        with self._lock:
            return list(self._items)

    def clear(self) -> None:
        with self._lock:
            self._items.clear()


educational_identity_passive_captures = EducationalIdentityPassiveCaptureRegistry()


async def observe_educational_identity_resolution(
    *,
    enabled: bool,
    db: AsyncSession,
    reference: EducationalIdentityReference,
    resolver: EducationalIdentityResolver | None = None,
) -> EducationalIdentityPassiveCapture | None:
    """Run Educational Identity resolution passively behind a feature flag."""

    if not enabled:
        return None

    platform_metrics.record_job_event(task=EUI_IDENTITY_METRIC_TASK, status="invoked")
    cache_before = educational_identity_cache.snapshot()
    started = time.perf_counter()
    active_resolver = resolver or EducationalIdentityResolver(db)
    try:
        identity = await active_resolver.resolve(reference)
    except EducationalIdentityAmbiguous as exc:
        duration_ms = _duration_ms(started)
        capture = _capture(
            reference=reference,
            status="ambiguous",
            duration_ms=duration_ms,
            error=str(exc),
            cache_before=cache_before,
        )
        logger.info(
            "Educational Identity passive resolution ambiguous",
            extra={
                "eui_reference_kind": reference.resolution_kind,
                "eui_duration_ms": round(duration_ms, 2),
            },
        )
        return capture
    except EducationalIdentityNotFound as exc:
        duration_ms = _duration_ms(started)
        capture = _capture(
            reference=reference,
            status="not_found",
            duration_ms=duration_ms,
            error=str(exc),
            cache_before=cache_before,
        )
        logger.info(
            "Educational Identity passive resolution not found",
            extra={
                "eui_reference_kind": reference.resolution_kind,
                "eui_duration_ms": round(duration_ms, 2),
            },
        )
        return capture
    except Exception:
        duration_ms = _duration_ms(started)
        platform_metrics.record_job_event(
            task=EUI_IDENTITY_METRIC_TASK,
            status="failed",
            duration_ms=duration_ms,
        )
        logger.exception(
            "Educational Identity passive resolution failed",
            extra={
                "eui_reference_kind": reference.resolution_kind,
                "eui_duration_ms": round(duration_ms, 2),
            },
        )
        return None

    duration_ms = _duration_ms(started)
    capture = _capture(
        reference=reference,
        status="completed",
        duration_ms=duration_ms,
        identity=identity,
        cache_before=cache_before,
    )
    logger.info(
        "Educational Identity passive resolution completed",
        extra={
            "eui_reference_kind": reference.resolution_kind,
            "eui_duration_ms": round(duration_ms, 2),
        },
    )
    return capture


def _capture(
    *,
    reference: EducationalIdentityReference,
    status: str,
    duration_ms: float,
    cache_before,
    identity: EducationalIdentity | None = None,
    error: str | None = None,
) -> EducationalIdentityPassiveCapture:
    cache_after = educational_identity_cache.snapshot()
    cache_hits = cache_after.hits - cache_before.hits
    cache_misses = cache_after.misses - cache_before.misses
    platform_metrics.record_job_event(
        task=EUI_IDENTITY_METRIC_TASK,
        status=status,
        duration_ms=duration_ms,
    )
    if cache_hits > 0:
        platform_metrics.record_job_event(task=EUI_IDENTITY_METRIC_TASK, status="cache_hit")
    if cache_misses > 0:
        platform_metrics.record_job_event(task=EUI_IDENTITY_METRIC_TASK, status="cache_miss")

    capture = EducationalIdentityPassiveCapture(
        reference_kind=reference.resolution_kind,
        status=status,
        duration_ms=duration_ms,
        identity=identity,
        error=error,
        cache_hits=cache_hits,
        cache_misses=cache_misses,
    )
    educational_identity_passive_captures.record(capture)
    return capture


def _duration_ms(started: float) -> float:
    return (time.perf_counter() - started) * 1000
