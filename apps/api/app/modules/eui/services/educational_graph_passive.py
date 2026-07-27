"""Passive Educational Knowledge Graph relationship proposal observer."""

from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass
from threading import Lock

from app.core.platform_metrics import platform_metrics
from app.modules.eui.schemas.educational_graph import (
    EducationalGraphRelationshipProposal,
    EducationalGraphRelationshipReference,
)
from app.modules.eui.services.educational_graph_resolver import (
    EducationalGraphProposalResolver,
)

logger = logging.getLogger(__name__)

EUI_EKG_METRIC_TASK = "eui_ekg"


@dataclass(frozen=True)
class EducationalGraphPassiveCapture:
    proposal_kind: str
    status: str
    duration_ms: float
    proposal: EducationalGraphRelationshipProposal | None = None
    error: str | None = None


class EducationalGraphPassiveCaptureRegistry:
    """Bounded in-memory capture store for passive verification only."""

    def __init__(self, *, max_entries: int = 100) -> None:
        self._items: deque[EducationalGraphPassiveCapture] = deque(maxlen=max_entries)
        self._lock = Lock()

    def record(self, capture: EducationalGraphPassiveCapture) -> None:
        with self._lock:
            self._items.append(capture)

    def snapshot(self) -> list[EducationalGraphPassiveCapture]:
        with self._lock:
            return list(self._items)

    def clear(self) -> None:
        with self._lock:
            self._items.clear()


educational_graph_passive_captures = EducationalGraphPassiveCaptureRegistry()


def observe_educational_graph_proposal(
    *,
    enabled: bool,
    reference: EducationalGraphRelationshipReference,
    resolver: EducationalGraphProposalResolver | None = None,
) -> EducationalGraphPassiveCapture | None:
    """Build an EKG relationship proposal passively behind a feature flag."""

    if not enabled:
        return None

    platform_metrics.record_job_event(task=EUI_EKG_METRIC_TASK, status="resolve_invoked")
    started = time.perf_counter()
    try:
        active_resolver = resolver or EducationalGraphProposalResolver()
        proposal = active_resolver.propose(reference)
    except Exception as exc:
        duration_ms = _duration_ms(started)
        platform_metrics.record_job_event(
            task=EUI_EKG_METRIC_TASK,
            status="resolve_failed",
            duration_ms=duration_ms,
        )
        logger.exception(
            "Educational Graph passive proposal failed",
            extra={
                "eui_ekg_proposal_kind": reference.proposal_kind,
                "eui_ekg_duration_ms": round(duration_ms, 2),
            },
        )
        capture = EducationalGraphPassiveCapture(
            proposal_kind=reference.proposal_kind,
            status="resolve_failed",
            duration_ms=duration_ms,
            error=str(exc),
        )
        educational_graph_passive_captures.record(capture)
        return None

    duration_ms = _duration_ms(started)
    status = _status_for_proposal(proposal)
    platform_metrics.record_job_event(
        task=EUI_EKG_METRIC_TASK,
        status=status,
        duration_ms=duration_ms,
    )
    capture = EducationalGraphPassiveCapture(
        proposal_kind=reference.proposal_kind,
        status=status,
        duration_ms=duration_ms,
        proposal=proposal,
    )
    educational_graph_passive_captures.record(capture)
    logger.info(
        "Educational Graph passive proposal completed",
        extra={
            "eui_ekg_proposal_kind": reference.proposal_kind,
            "eui_ekg_status": status,
            "eui_ekg_relationship_category": proposal.relationship_category,
            "eui_ekg_duration_ms": round(duration_ms, 2),
        },
    )
    return capture


def _status_for_proposal(proposal: EducationalGraphRelationshipProposal) -> str:
    if proposal.status == "unsupported":
        return "unsupported"
    if proposal.status == "ambiguous":
        return "ambiguous"
    if proposal.status == "missing_target":
        return "identity_link_missing"
    if proposal.source_candidate_id:
        return "candidate_relationship_proposed"
    if proposal.relationship_category == "identity_link":
        return "identity_link_found"
    return "resolve_completed"


def _duration_ms(started: float) -> float:
    return (time.perf_counter() - started) * 1000
