"""Passive Educational Context runtime observer.

This mirrors the Sprint 1 passive Educational Identity posture: failures are
isolated, output is captured only for verification, and no production consumer
depends on the result.
"""

from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass
from threading import Lock

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.platform_metrics import platform_metrics
from app.modules.eui.schemas.educational_context import (
    EducationalContext,
    EducationalContextReference,
)
from app.modules.eui.services.educational_context_cache import educational_context_cache
from app.modules.eui.services.educational_context_resolver import (
    EducationalContextNotFound,
    EducationalContextResolver,
)

logger = logging.getLogger(__name__)

EUI_CONTEXT_METRIC_TASK = "eui_context_resolver"


@dataclass(frozen=True)
class EducationalContextPassiveCapture:
    reference_kind: str
    status: str
    duration_ms: float
    context: EducationalContext | None = None
    error: str | None = None
    cache_hits: int = 0
    cache_misses: int = 0


class EducationalContextPassiveCaptureRegistry:
    """Bounded in-memory capture store for passive verification only."""

    def __init__(self, *, max_entries: int = 100) -> None:
        self._items: deque[EducationalContextPassiveCapture] = deque(maxlen=max_entries)
        self._lock = Lock()

    def record(self, capture: EducationalContextPassiveCapture) -> None:
        with self._lock:
            self._items.append(capture)

    def snapshot(self) -> list[EducationalContextPassiveCapture]:
        with self._lock:
            return list(self._items)

    def clear(self) -> None:
        with self._lock:
            self._items.clear()


educational_context_passive_captures = EducationalContextPassiveCaptureRegistry()


async def observe_educational_context_resolution(
    *,
    enabled: bool,
    reference: EducationalContextReference,
    db: AsyncSession | None = None,
    resolver: EducationalContextResolver | None = None,
) -> EducationalContextPassiveCapture | None:
    """Run Educational Context resolution passively behind a feature flag."""

    if not enabled:
        return None

    platform_metrics.record_job_event(task=EUI_CONTEXT_METRIC_TASK, status="invoked")
    cache_before = educational_context_cache.snapshot()
    started = time.perf_counter()
    active_resolver = resolver or EducationalContextResolver(db)
    try:
        context = await active_resolver.resolve(reference)
    except EducationalContextNotFound as exc:
        duration_ms = _duration_ms(started)
        capture = _capture(
            reference=reference,
            status="not_found",
            duration_ms=duration_ms,
            error=str(exc),
            cache_before=cache_before,
        )
        logger.info(
            "Educational Context passive resolution not found",
            extra={
                "eui_reference_kind": reference.resolution_kind,
                "eui_duration_ms": round(duration_ms, 2),
            },
        )
        return capture
    except Exception:
        duration_ms = _duration_ms(started)
        platform_metrics.record_job_event(
            task=EUI_CONTEXT_METRIC_TASK,
            status="failed",
            duration_ms=duration_ms,
        )
        logger.exception(
            "Educational Context passive resolution failed",
            extra={
                "eui_reference_kind": reference.resolution_kind,
                "eui_duration_ms": round(duration_ms, 2),
            },
        )
        return None

    duration_ms = _duration_ms(started)
    status = _status_for_context(context)
    capture = _capture(
        reference=reference,
        status=status,
        duration_ms=duration_ms,
        context=context,
        cache_before=cache_before,
    )
    logger.info(
        "Educational Context passive resolution completed",
        extra={
            "eui_reference_kind": reference.resolution_kind,
            "eui_context_status": status,
            "eui_duration_ms": round(duration_ms, 2),
        },
    )
    return capture


def _capture(
    *,
    reference: EducationalContextReference,
    status: str,
    duration_ms: float,
    cache_before,
    context: EducationalContext | None = None,
    error: str | None = None,
) -> EducationalContextPassiveCapture:
    cache_after = educational_context_cache.snapshot()
    cache_hits = cache_after.hits - cache_before.hits
    cache_misses = cache_after.misses - cache_before.misses
    platform_metrics.record_job_event(
        task=EUI_CONTEXT_METRIC_TASK,
        status=status,
        duration_ms=duration_ms,
    )
    if cache_hits > 0:
        platform_metrics.record_job_event(task=EUI_CONTEXT_METRIC_TASK, status="cache_hit")
    if cache_misses > 0:
        platform_metrics.record_job_event(task=EUI_CONTEXT_METRIC_TASK, status="cache_miss")

    capture = EducationalContextPassiveCapture(
        reference_kind=reference.resolution_kind,
        status=status,
        duration_ms=duration_ms,
        context=context,
        error=error,
        cache_hits=cache_hits,
        cache_misses=cache_misses,
    )
    educational_context_passive_captures.record(capture)
    return capture


def _status_for_context(context: EducationalContext) -> str:
    if context.resolution_status == "ambiguous":
        return "ambiguous"
    if context.conflicts:
        return "conflict"
    return "completed"


def _duration_ms(started: float) -> float:
    return (time.perf_counter() - started) * 1000
