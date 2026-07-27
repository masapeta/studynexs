"""Rich EUI evidence binder for AEI consumer migration Phase 7B.

Phase 7B enriches the already-passive Phase 7A AEI dual-read comparison with
available EUI evidence. It is deliberately non-authoritative: failures are
isolated, evidence is bounded, nothing is persisted, and production evaluation
behavior remains unchanged.
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.platform_metrics import platform_metrics
from app.db.models.examination import Exam
from app.db.models.question_paper import QuestionPaper
from app.modules.eui.schemas.aei_consumer_migration import (
    AEIConsumerMigrationEvidenceBundle,
    AEIConsumerMigrationSubjectType,
)
from app.modules.eui.schemas.educational_context import (
    EducationalContext,
    EducationalContextReference,
)
from app.modules.eui.schemas.platform_capability import (
    PlatformCapabilityLookupRequest,
    PlatformCapabilityLookupResult,
)
from app.modules.eui.schemas.trust_report import TrustReport
from app.modules.eui.services.educational_context_resolver import (
    EducationalContextNotFound,
    EducationalContextResolver,
)
from app.modules.eui.services.platform_capability_lookup import PlatformCapabilityLookupService
from app.modules.eui.services.trust_report_builder import TrustReportBuilder

logger = logging.getLogger(__name__)

EUI_AEI_RICH_EVIDENCE_METRIC_TASK = "eui_consumer_migration.rich_evidence"

QUERY_BUDGET = {
    "strategy": "single_evaluation_context",
    "per_question_db_traversal": False,
    "max_question_paper_queries": 1,
    "max_context_resolutions": 1,
    "max_capability_lookups": 1,
    "max_trust_reports": 1,
}


@dataclass(frozen=True)
class AEIConsumerMigrationBoundEvidence:
    """Evidence objects and sanitized summary for the Phase 7A observer."""

    bundle: AEIConsumerMigrationEvidenceBundle
    educational_context: EducationalContext | None = None
    capability_lookup: PlatformCapabilityLookupResult | None = None
    trust_report: TrustReport | None = None

    @property
    def eui_summary(self) -> dict[str, Any]:
        return {
            "rich_evidence_available": self.bundle.status != "failed",
            "rich_evidence_status": self.bundle.status,
            "educational_identity_id": self.bundle.educational_identity_id,
            "context_available": self.educational_context is not None,
            "context_status": self.bundle.context_status,
            "capability_mode": self.bundle.capability_mode,
            "capability_matched": self.bundle.capability_matched,
            "trust_report_id": self.bundle.trust_report_ref,
            "trust_posture": self.bundle.trust_posture,
            "trust_consumer_visibility": self.bundle.trust_consumer_visibility,
            "missing_evidence": self.bundle.missing_evidence,
            "ambiguous_evidence": self.bundle.ambiguous_evidence,
            "query_budget": self.bundle.query_budget,
            "runtime_authoritative": False,
        }


class AEIConsumerMigrationEvidenceBinder:
    """Bind available EUI evidence into AEI passive dual-read comparison."""

    def __init__(
        self,
        *,
        context_resolver: EducationalContextResolver | None = None,
        capability_lookup: PlatformCapabilityLookupService | None = None,
        trust_builder: TrustReportBuilder | None = None,
    ) -> None:
        self.context_resolver = context_resolver
        self.capability_lookup = capability_lookup or PlatformCapabilityLookupService()
        self.trust_builder = trust_builder or TrustReportBuilder()

    async def bind(
        self,
        *,
        enabled: bool,
        db: AsyncSession | None,
        tenant_id: uuid.UUID,
        subject_type: AEIConsumerMigrationSubjectType,
        subject_ref: str,
        artifact_id: uuid.UUID | None = None,
        exam: Exam | None = None,
        question_paper: QuestionPaper | None = None,
    ) -> AEIConsumerMigrationBoundEvidence | None:
        """Bind rich evidence behind the 7B feature flag.

        Disabled returns ``None`` and intentionally records nothing, preserving
        Phase 7A behavior. Enabled never raises to callers.
        """

        if not enabled:
            return None

        started = time.perf_counter()
        platform_metrics.record_job_event(
            task=EUI_AEI_RICH_EVIDENCE_METRIC_TASK,
            status="invoked",
        )
        missing: set[str] = set()
        ambiguous: set[str] = set()
        context: EducationalContext | None = None
        capability: PlatformCapabilityLookupResult | None = None
        trust: TrustReport | None = None

        try:
            paper = question_paper or await _load_question_paper(
                db=db,
                tenant_id=tenant_id,
                exam=exam,
            )
            reference = _context_reference(
                tenant_id=tenant_id,
                subject_type=subject_type,
                artifact_id=artifact_id,
                exam=exam,
                question_paper=paper,
            )
            context = await self._resolve_context(db=db, reference=reference)
            if context is None:
                missing.add("context")
                missing.add("identity")
            else:
                if not context.educational_identity_id:
                    missing.add("identity")
                if context.ambiguities:
                    ambiguous.add("context")

            capability = self._lookup_capability(
                context=context,
                reference=reference,
            )
            if capability is None or not capability.matched:
                missing.add("capability")
            if capability is not None and capability.conflict:
                ambiguous.add("capability")

            trust = self._build_trust(
                tenant_id=tenant_id,
                context=context,
                capability=capability,
            )
            if trust is None:
                missing.add("trust")
            elif trust.consumer_visibility != "internal_only":
                missing.add("trust_unsafe")

            duration_ms = _duration_ms(started)
            bundle = _bundle(
                tenant_id=tenant_id,
                subject_type=subject_type,
                subject_ref=subject_ref,
                context=context,
                capability=capability,
                trust=trust,
                missing=missing,
                ambiguous=ambiguous,
                duration_ms=duration_ms,
            )
            self._record_status(bundle)
            logger.info(
                "EUI AEI rich evidence binding completed",
                extra={
                    "eui_consumer": "aei",
                    "eui_subject_type": subject_type,
                    "eui_rich_evidence_status": bundle.status,
                    "eui_duration_ms": round(duration_ms, 2),
                },
            )
            return AEIConsumerMigrationBoundEvidence(
                bundle=bundle,
                educational_context=context,
                capability_lookup=capability,
                trust_report=trust,
            )
        except Exception as exc:
            duration_ms = _duration_ms(started)
            platform_metrics.record_job_event(
                task=EUI_AEI_RICH_EVIDENCE_METRIC_TASK,
                status="failed",
                duration_ms=duration_ms,
            )
            logger.exception(
                "EUI AEI rich evidence binding failed",
                extra={
                    "eui_consumer": "aei",
                    "eui_subject_type": subject_type,
                    "eui_duration_ms": round(duration_ms, 2),
                },
            )
            return AEIConsumerMigrationBoundEvidence(
                bundle=AEIConsumerMigrationEvidenceBundle(
                    tenant_id=tenant_id,
                    subject_type=subject_type,
                    subject_ref=subject_ref,
                    status="failed",
                    missing_evidence=("identity", "context", "capability", "trust"),
                    duration_ms=duration_ms,
                    query_budget=dict(QUERY_BUDGET),
                    metadata={
                        "authorization": "EUI-PH7B-AEI-RICH-EVIDENCE-AUTH-001",
                        "passive": True,
                        "runtime_authoritative": False,
                        "error_type": type(exc).__name__,
                    },
                )
            )

    async def _resolve_context(
        self,
        *,
        db: AsyncSession | None,
        reference: EducationalContextReference,
    ) -> EducationalContext | None:
        resolver = self.context_resolver or EducationalContextResolver(db)
        try:
            return await resolver.resolve(reference)
        except EducationalContextNotFound:
            return None

    def _lookup_capability(
        self,
        *,
        context: EducationalContext | None,
        reference: EducationalContextReference,
    ) -> PlatformCapabilityLookupResult | None:
        domain, capability_key = _capability_target(context=context, reference=reference)
        if context is not None:
            return self.capability_lookup.lookup_for_context(
                context=context,
                domain=domain,
                capability_key=capability_key,
                artifact_type=reference.artifact_type,
            )
        return self.capability_lookup.lookup(
            PlatformCapabilityLookupRequest(
                domain=domain,
                capability_key=capability_key,
                board=reference.board,
                curriculum=reference.curriculum,
                curriculum_version=reference.curriculum_version,
                grade=reference.grade,
                subject=reference.subject,
                language=reference.language_medium,
                artifact_type=reference.artifact_type,
                assessment_mode=reference.assessment_mode,
                metadata={"source": "aei_rich_evidence_reference"},
            )
        )

    def _build_trust(
        self,
        *,
        tenant_id: uuid.UUID,
        context: EducationalContext | None,
        capability: PlatformCapabilityLookupResult | None,
    ) -> TrustReport | None:
        if context is not None:
            return self.trust_builder.build_for_context(context)
        if capability is not None:
            return self.trust_builder.build_for_capability_lookup(
                capability,
                tenant_id=tenant_id,
            )
        return None

    @staticmethod
    def _record_status(bundle: AEIConsumerMigrationEvidenceBundle) -> None:
        platform_metrics.record_job_event(
            task=EUI_AEI_RICH_EVIDENCE_METRIC_TASK,
            status=bundle.status,
            duration_ms=bundle.duration_ms,
        )
        for evidence in bundle.missing_evidence:
            platform_metrics.record_job_event(
                task=EUI_AEI_RICH_EVIDENCE_METRIC_TASK,
                status=f"missing_{evidence}",
            )
        if bundle.ambiguous_evidence:
            platform_metrics.record_job_event(
                task=EUI_AEI_RICH_EVIDENCE_METRIC_TASK,
                status="ambiguous",
            )


async def bind_aei_consumer_migration_evidence(
    *,
    enabled: bool,
    db: AsyncSession | None,
    tenant_id: uuid.UUID,
    subject_type: AEIConsumerMigrationSubjectType,
    subject_ref: str,
    artifact_id: uuid.UUID | None = None,
    exam: Exam | None = None,
    question_paper: QuestionPaper | None = None,
    binder: AEIConsumerMigrationEvidenceBinder | None = None,
) -> AEIConsumerMigrationBoundEvidence | None:
    """Convenience wrapper for the answer-sheet evaluation integration hook."""

    if not enabled:
        return None

    active_binder = binder or AEIConsumerMigrationEvidenceBinder()
    return await active_binder.bind(
        enabled=enabled,
        db=db,
        tenant_id=tenant_id,
        subject_type=subject_type,
        subject_ref=subject_ref,
        artifact_id=artifact_id,
        exam=exam,
        question_paper=question_paper,
    )


async def _load_question_paper(
    *,
    db: AsyncSession | None,
    tenant_id: uuid.UUID,
    exam: Exam | None,
) -> QuestionPaper | None:
    if db is None or exam is None or exam.source_paper_id is None:
        return None
    result = await db.execute(
        select(QuestionPaper).where(
            QuestionPaper.id == exam.source_paper_id,
            QuestionPaper.school_id == tenant_id,
        )
    )
    return result.scalar_one_or_none()


def _context_reference(
    *,
    tenant_id: uuid.UUID,
    subject_type: str,
    artifact_id: uuid.UUID | None,
    exam: Exam | None,
    question_paper: QuestionPaper | None,
) -> EducationalContextReference:
    assessment_mode = _exam_mode(exam) or "answer_sheet_evaluation"
    topic = _first_present(
        getattr(exam, "topic", None),
        _single_topic(getattr(question_paper, "topics", None)),
    )
    return EducationalContextReference(
        school_id=tenant_id,
        pack_id=getattr(question_paper, "pack_id", None),
        artifact_type=subject_type,
        artifact_id=artifact_id,
        board=getattr(question_paper, "board", None),
        curriculum=getattr(question_paper, "curriculum", None),
        curriculum_version=getattr(question_paper, "curriculum_version", None),
        grade=getattr(question_paper, "grade", None),
        subject=getattr(question_paper, "subject_name", None),
        topic=topic,
        assessment_mode=assessment_mode,
        language_medium=getattr(question_paper, "language_medium", None),
        candidate_context_ids=tuple(getattr(question_paper, "candidate_context_ids", ()) or ()),
        evidence_posture="passive_dual_read_rich_evidence",
        metadata={
            "authorization": "EUI-PH7B-AEI-RICH-EVIDENCE-AUTH-001",
            "passive": True,
            "source": "answer_sheet_evaluation",
        },
    )


def _capability_target(
    *,
    context: EducationalContext | None,
    reference: EducationalContextReference,
) -> tuple[str, str]:
    subject = _normalize_label(
        (context.subject if context is not None else None) or reference.subject
    )
    if "math" in subject:
        return "mathematics", "numeric_normalization"
    if "chem" in subject:
        return "science", "reaction_balancing"
    if "bio" in subject:
        return "visual", "biology_diagrams"
    if "science" in subject or "physics" in subject:
        return "evaluation", "diagrams"
    return "evaluation", "numeric_equivalence"


def _bundle(
    *,
    tenant_id: uuid.UUID,
    subject_type: AEIConsumerMigrationSubjectType,
    subject_ref: str,
    context: EducationalContext | None,
    capability: PlatformCapabilityLookupResult | None,
    trust: TrustReport | None,
    missing: set[str],
    ambiguous: set[str],
    duration_ms: float,
) -> AEIConsumerMigrationEvidenceBundle:
    status = _status(missing=missing, ambiguous=ambiguous)
    return AEIConsumerMigrationEvidenceBundle(
        tenant_id=tenant_id,
        subject_type=subject_type,
        subject_ref=subject_ref,
        status=status,
        educational_identity_id=(
            context.educational_identity_id if context is not None else None
        ),
        context_status=context.resolution_status if context is not None else None,
        capability_mode=capability.mode if capability is not None else None,
        capability_matched=capability.matched if capability is not None else None,
        trust_report_ref=trust.id if trust is not None else None,
        trust_posture=trust.overall_posture if trust is not None else None,
        trust_consumer_visibility=trust.consumer_visibility if trust is not None else None,
        missing_evidence=tuple(sorted(missing)),
        ambiguous_evidence=tuple(sorted(ambiguous)),
        duration_ms=duration_ms,
        query_budget=dict(QUERY_BUDGET),
        metadata={
            "authorization": "EUI-PH7B-AEI-RICH-EVIDENCE-AUTH-001",
            "passive": True,
            "runtime_authoritative": False,
            "source_of_truth": "legacy_aei_evaluation",
        },
    )


def _status(*, missing: set[str], ambiguous: set[str]) -> str:
    if not missing and not ambiguous:
        return "resolved"
    if len(missing) >= 4:
        return "missing"
    return "partial"


def _exam_mode(exam: Exam | None) -> str | None:
    if exam is None:
        return None
    value = getattr(exam, "exam_type", None)
    return getattr(value, "value", None) or (str(value) if value is not None else None)


def _single_topic(topics: Any) -> str | None:
    if isinstance(topics, (list, tuple)) and len(topics) == 1:
        return str(topics[0])
    return None


def _first_present(*values: Any) -> Any | None:
    for value in values:
        if value is not None and value != "":
            return value
    return None


def _normalize_label(value: str | None) -> str:
    return " ".join((value or "").casefold().split())


def _duration_ms(started: float) -> float:
    return (time.perf_counter() - started) * 1000
