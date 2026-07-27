"""Passive KAI candidate observer for Phase 4."""

from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass
from threading import Lock

from app.core.platform_metrics import platform_metrics
from app.modules.eui.schemas.knowledge_acquisition import (
    EducationalArtifactCandidate,
    KnowledgeAcquisitionInputReference,
)
from app.modules.eui.services.knowledge_acquisition_builder import (
    KnowledgeAcquisitionCandidateBuilder,
)

logger = logging.getLogger(__name__)

EUI_KAI_METRIC_TASK = "eui_kai"


@dataclass(frozen=True)
class KnowledgeAcquisitionPassiveCapture:
    source_type: str
    status: str
    duration_ms: float
    candidate: EducationalArtifactCandidate | None = None
    error: str | None = None


class KnowledgeAcquisitionPassiveCaptureRegistry:
    """Bounded in-memory capture store for passive verification only."""

    def __init__(self, *, max_entries: int = 100) -> None:
        self._items: deque[KnowledgeAcquisitionPassiveCapture] = deque(maxlen=max_entries)
        self._lock = Lock()

    def record(self, capture: KnowledgeAcquisitionPassiveCapture) -> None:
        with self._lock:
            self._items.append(capture)

    def snapshot(self) -> list[KnowledgeAcquisitionPassiveCapture]:
        with self._lock:
            return list(self._items)

    def clear(self) -> None:
        with self._lock:
            self._items.clear()


knowledge_acquisition_passive_captures = KnowledgeAcquisitionPassiveCaptureRegistry()


def observe_knowledge_acquisition_candidate(
    *,
    enabled: bool,
    reference: KnowledgeAcquisitionInputReference,
    builder: KnowledgeAcquisitionCandidateBuilder | None = None,
) -> KnowledgeAcquisitionPassiveCapture | None:
    """Build a KAI candidate passively behind a feature flag."""

    if not enabled:
        return None

    platform_metrics.record_job_event(task=EUI_KAI_METRIC_TASK, status="acquire_invoked")
    started = time.perf_counter()
    try:
        active_builder = builder or KnowledgeAcquisitionCandidateBuilder()
        candidate = active_builder.build(reference)
    except Exception as exc:
        duration_ms = _duration_ms(started)
        platform_metrics.record_job_event(
            task=EUI_KAI_METRIC_TASK,
            status="acquire_failed",
            duration_ms=duration_ms,
        )
        logger.exception(
            "KAI passive candidate generation failed",
            extra={
                "eui_kai_source_type": reference.source_type,
                "eui_kai_duration_ms": round(duration_ms, 2),
            },
        )
        capture = KnowledgeAcquisitionPassiveCapture(
            source_type=reference.source_type,
            status="acquire_failed",
            duration_ms=duration_ms,
            error=str(exc),
        )
        knowledge_acquisition_passive_captures.record(capture)
        return None

    duration_ms = _duration_ms(started)
    status = _status_for_candidate(candidate)
    platform_metrics.record_job_event(
        task=EUI_KAI_METRIC_TASK,
        status=status,
        duration_ms=duration_ms,
    )
    capture = KnowledgeAcquisitionPassiveCapture(
        source_type=reference.source_type,
        status=status,
        duration_ms=duration_ms,
        candidate=candidate,
    )
    knowledge_acquisition_passive_captures.record(capture)
    logger.info(
        "KAI passive candidate generation completed",
        extra={
            "eui_kai_source_type": reference.source_type,
            "eui_kai_status": status,
            "eui_kai_candidate_review_status": candidate.review_status,
            "eui_kai_duration_ms": round(duration_ms, 2),
        },
    )
    return capture


def _status_for_candidate(candidate: EducationalArtifactCandidate) -> str:
    if candidate.review_status == "unsupported":
        return "unsupported_input"
    if candidate.review_status == "ambiguous":
        return "ambiguous"
    if candidate.review_status == "needs_review":
        return "needs_review"
    return "acquire_completed"


def _duration_ms(started: float) -> float:
    return (time.perf_counter() - started) * 1000
