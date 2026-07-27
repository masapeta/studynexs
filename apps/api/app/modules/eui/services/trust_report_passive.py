"""Passive Trust Report observer for EUI Phase 6.

The observer is default-off, report-only, and exception-isolated. It captures
bounded in-memory evidence for validation; no product consumer depends on it.
"""

from __future__ import annotations

import logging
import time
import uuid
from collections import deque
from dataclasses import dataclass
from threading import Lock
from typing import TypeAlias

from app.core.platform_metrics import platform_metrics
from app.modules.eui.schemas.educational_context import EducationalContext
from app.modules.eui.schemas.educational_graph import EducationalGraphRelationshipProposal
from app.modules.eui.schemas.knowledge_acquisition import EducationalArtifactCandidate
from app.modules.eui.schemas.platform_capability import PlatformCapabilityLookupResult
from app.modules.eui.schemas.trust_report import TrustReport
from app.modules.eui.services.trust_report_builder import TrustReportBuilder

logger = logging.getLogger(__name__)

EUI_TRUST_REPORT_METRIC_TASK = "eui_trust_report"

TrustReportSubject: TypeAlias = (
    EducationalContext
    | PlatformCapabilityLookupResult
    | EducationalArtifactCandidate
    | EducationalGraphRelationshipProposal
)


@dataclass(frozen=True)
class TrustReportPassiveCapture:
    subject_type: str
    subject_ref: str
    status: str
    duration_ms: float
    report: TrustReport | None = None
    error: str | None = None


class TrustReportPassiveCaptureRegistry:
    """Bounded in-memory capture store for passive verification only."""

    def __init__(self, *, max_entries: int = 100) -> None:
        self._items: deque[TrustReportPassiveCapture] = deque(maxlen=max_entries)
        self._lock = Lock()

    def record(self, capture: TrustReportPassiveCapture) -> None:
        with self._lock:
            self._items.append(capture)

    def snapshot(self) -> list[TrustReportPassiveCapture]:
        with self._lock:
            return list(self._items)

    def clear(self) -> None:
        with self._lock:
            self._items.clear()


trust_report_passive_captures = TrustReportPassiveCaptureRegistry()


def observe_trust_report(
    *,
    enabled: bool,
    subject: TrustReportSubject,
    tenant_id: uuid.UUID | None = None,
    builder: TrustReportBuilder | None = None,
) -> TrustReportPassiveCapture | None:
    """Build a Trust Report passively behind a feature flag."""

    if not enabled:
        return None

    subject_type, subject_ref = _subject_labels(subject)
    platform_metrics.record_job_event(task=EUI_TRUST_REPORT_METRIC_TASK, status="invoked")
    started = time.perf_counter()
    try:
        active_builder = builder or TrustReportBuilder()
        report = _build_report(active_builder, subject, tenant_id=tenant_id)
    except Exception as exc:
        duration_ms = _duration_ms(started)
        platform_metrics.record_job_event(
            task=EUI_TRUST_REPORT_METRIC_TASK,
            status="failed",
            duration_ms=duration_ms,
        )
        logger.exception(
            "EUI Trust Report passive generation failed",
            extra={
                "eui_trust_subject_type": subject_type,
                "eui_trust_duration_ms": round(duration_ms, 2),
            },
        )
        capture = TrustReportPassiveCapture(
            subject_type=subject_type,
            subject_ref=subject_ref,
            status="failed",
            duration_ms=duration_ms,
            error=str(exc),
        )
        trust_report_passive_captures.record(capture)
        return None

    duration_ms = _duration_ms(started)
    status = _status_for_report(report)
    platform_metrics.record_job_event(
        task=EUI_TRUST_REPORT_METRIC_TASK,
        status=status,
        duration_ms=duration_ms,
    )
    capture = TrustReportPassiveCapture(
        subject_type=report.subject_type,
        subject_ref=report.subject_ref,
        status=status,
        duration_ms=duration_ms,
        report=report,
    )
    trust_report_passive_captures.record(capture)
    logger.info(
        "EUI Trust Report passive generation completed",
        extra={
            "eui_trust_subject_type": report.subject_type,
            "eui_trust_status": status,
            "eui_trust_overall_posture": report.overall_posture,
            "eui_trust_review_required": report.review_required,
            "eui_trust_dimension_count": len(report.dimensions),
            "eui_trust_warning_count": len(report.warnings),
            "eui_trust_capability_mode": report.capability_mode,
            "eui_trust_duration_ms": round(duration_ms, 2),
        },
    )
    return capture


def _build_report(
    builder: TrustReportBuilder,
    subject: TrustReportSubject,
    *,
    tenant_id: uuid.UUID | None,
) -> TrustReport:
    if isinstance(subject, EducationalContext):
        return builder.build_for_context(subject)
    if isinstance(subject, EducationalArtifactCandidate):
        return builder.build_for_kai_candidate(subject)
    if isinstance(subject, EducationalGraphRelationshipProposal):
        return builder.build_for_ekg_proposal(subject)
    if isinstance(subject, PlatformCapabilityLookupResult):
        if tenant_id is None:
            raise ValueError("tenant_id is required for capability lookup Trust Reports")
        return builder.build_for_capability_lookup(subject, tenant_id=tenant_id)
    raise TypeError(f"Unsupported Trust Report subject: {type(subject).__name__}")


def _subject_labels(subject: TrustReportSubject) -> tuple[str, str]:
    if isinstance(subject, EducationalContext):
        return (
            "educational_context",
            subject.educational_identity_id or str(subject.curriculum_pack_id or "context"),
        )
    if isinstance(subject, EducationalArtifactCandidate):
        return ("kai_candidate", subject.id)
    if isinstance(subject, EducationalGraphRelationshipProposal):
        return ("ekg_relationship_proposal", subject.id)
    if isinstance(subject, PlatformCapabilityLookupResult):
        return (
            "platform_capability_lookup",
            f"{subject.request.domain}:{subject.request.capability_key}",
        )
    return ("unknown", "unknown")


def _status_for_report(report: TrustReport) -> str:
    if report.overall_posture == "unsupported":
        return "unsupported"
    if report.overall_posture == "insufficient_evidence":
        return "insufficient_evidence"
    if report.overall_posture in {"manual_review_required", "review_recommended"}:
        return "manual_review"
    return "completed"


def _duration_ms(started: float) -> float:
    return (time.perf_counter() - started) * 1000
