"""Passive observer for mastery spine resolution.

This module is intentionally invisible to product behavior. It records internal
evidence only when explicitly enabled.
"""

from __future__ import annotations

import time

import structlog

from app.core.platform_metrics import platform_metrics
from app.modules.mastery.schemas.mastery_spine import (
    MasterySpineReference,
    MasterySpineResolutionReference,
)
from app.modules.mastery.services.mastery_spine_resolver import MasterySpineResolver

MASTERY_SPINE_METRIC_TASK = "mastery_spine"

logger = structlog.get_logger()


async def observe_mastery_spine_resolution(
    *,
    enabled: bool,
    resolver: MasterySpineResolver,
    reference: MasterySpineResolutionReference,
) -> MasterySpineReference | None:
    """Resolve a mastery spine reference passively when enabled."""

    if not enabled:
        return None

    started = time.perf_counter()
    platform_metrics.record_job_event(task=MASTERY_SPINE_METRIC_TASK, status="invoked")
    try:
        result = await resolver.resolve(reference)
    except Exception:
        platform_metrics.record_job_event(
            task=MASTERY_SPINE_METRIC_TASK,
            status="failed",
            duration_ms=_elapsed_ms(started),
        )
        logger.exception(
            "mastery_spine_resolve_failed",
            has_class_id=reference.class_id is not None,
            has_subject_id=reference.subject_id is not None,
            has_academic_year_id=reference.academic_year_id is not None,
            has_pack_id=reference.pack_id is not None,
            has_topic_id=reference.topic_id is not None,
            has_concept_id=reference.concept_id is not None,
            has_learning_outcome_id=reference.learning_outcome_id is not None,
            has_raw_label=bool(reference.raw_label),
        )
        return None

    platform_metrics.record_job_event(
        task=MASTERY_SPINE_METRIC_TASK,
        status=result.resolution_status,
    )
    platform_metrics.record_job_event(
        task=MASTERY_SPINE_METRIC_TASK,
        status="completed",
        duration_ms=_elapsed_ms(started),
    )
    logger.info(
        "mastery_spine_resolve_completed",
        resolution_status=result.resolution_status,
        authority_posture=result.authority_posture,
        spine_level=result.spine_level,
        ambiguity_count=len(result.ambiguities),
    )
    return result


def _elapsed_ms(started: float) -> float:
    return (time.perf_counter() - started) * 1000
