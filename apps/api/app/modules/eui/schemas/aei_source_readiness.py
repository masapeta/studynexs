"""AEI source-readiness review contracts for EUI Phase 7C.

Phase 7C is internal review only. These contracts summarize whether passive
AEI/EUI divergence evidence is mature enough to consider a future, narrow
source-readiness authorization. They never switch sources, assign marks,
change routing, or expose user-facing data.
"""

from __future__ import annotations

import uuid
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.eui.schemas.aei_consumer_migration import (
    AEIConsumerMigrationSubjectType,
)

AEISourceReadinessPosture = Literal[
    "eligible",
    "needs_more_evidence",
    "needs_capability_work",
    "blocked_product_impacting",
    "blocked_unsafe",
]

AEISourceReadinessDimension = Literal[
    "behavior_equivalence",
    "evidence_completeness",
    "capability_posture",
    "trust_posture",
    "tenant_safety",
    "product_impacting_divergence",
    "unsafe_divergence",
    "performance",
    "rollback",
    "regression_coverage",
    "evidence_window",
]

AEISourceReadinessDimensionStatus = Literal[
    "passed",
    "needs_more_evidence",
    "needs_capability_work",
    "blocked_product_impacting",
    "blocked_unsafe",
]

AEISourceReadinessCandidateScope = Literal[
    "context_metadata_only",
    "behavioral_source",
    "marks_source",
    "teacher_review_routing_source",
    "evidence_ledger_source",
]

AEISourceReadinessCandidateState = Literal[
    "ready_for_internal_trial",
    "not_ready_more_evidence",
    "not_ready_capability_work",
    "blocked_product_impacting",
    "blocked_unsafe",
]

AEISourceReadinessEvidenceClass = Literal[
    "educational_identity",
    "educational_context",
    "platform_capability",
    "trust_report",
    "readiness_scorecard",
    "safe_evidence_flags",
    "evidence_window",
    "behavior_equivalence",
    "performance",
    "rollback",
    "regression_coverage",
    "tenant_safety",
    "product_behavior",
    "safety",
]


class AEISourceReadinessDimensionResult(BaseModel):
    """One bounded internal review dimension for source-readiness scoring."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    dimension: AEISourceReadinessDimension
    status: AEISourceReadinessDimensionStatus
    reason: str
    blocker: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class AEISourceReadinessScorecard(BaseModel):
    """Internal AEI/EUI source-readiness scorecard.

    The scorecard is non-authoritative and internal-only. It records whether a
    future source-readiness contract may be considered; it does not make or
    activate any source switch.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(pattern=r"^eui-aei-readiness://")
    tenant_id: uuid.UUID
    consumer: Literal["aei"] = "aei"
    subject_type: AEIConsumerMigrationSubjectType
    scope_ref: str
    review_posture: AEISourceReadinessPosture
    eligible: bool
    evidence_window_required: int = Field(default=2, ge=1)
    evidence_window_count: int = Field(default=0, ge=0)
    reviewed_comparison_ids: tuple[str, ...] = ()
    dimensions: tuple[AEISourceReadinessDimensionResult, ...] = ()
    blocker_categories: tuple[str, ...] = ()
    source_flag_enabled: bool = False
    source_switch_active: Literal[False] = False
    internal_only: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def authoritative(self) -> bool:
        return False

    @model_validator(mode="after")
    def _validate_posture(self) -> "AEISourceReadinessScorecard":
        if self.eligible and self.review_posture != "eligible":
            raise ValueError("eligible scorecards must use eligible review posture")
        if self.review_posture == "eligible" and not self.eligible:
            raise ValueError("eligible review posture requires eligible=true")
        if self.review_posture == "eligible" and self.blocker_categories:
            raise ValueError("eligible scorecards must not carry blocker categories")
        return self


class AEISourceReadinessCandidate(BaseModel):
    """Internal narrow AEI source-readiness candidate.

    Phase 7D candidates are preparation artifacts only. They are never
    authoritative, never activate source switching, and never carry marks,
    answers, raw educational content, or user-facing display data.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(pattern=r"^eui-aei-source-candidate://")
    tenant_id: uuid.UUID
    consumer: Literal["aei"] = "aei"
    subject_type: AEIConsumerMigrationSubjectType
    scope_ref: str
    candidate_scope: AEISourceReadinessCandidateScope = "context_metadata_only"
    readiness_scorecard_ref: str = Field(pattern=r"^eui-aei-readiness://")
    readiness_review_posture: AEISourceReadinessPosture
    candidate_state: AEISourceReadinessCandidateState
    eligible_evidence_classes: tuple[AEISourceReadinessEvidenceClass, ...] = ()
    blocked_evidence_classes: tuple[AEISourceReadinessEvidenceClass, ...] = ()
    source_flag_enabled: bool = False
    source_flag_status: str = "disabled_or_inert"
    source_switch_active: Literal[False] = False
    internal_only: Literal[True] = True
    rollback_posture: str = "feature_flag_disablement"
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def authoritative(self) -> bool:
        return False

    @property
    def ready_for_internal_trial(self) -> bool:
        return self.candidate_state == "ready_for_internal_trial"

    @model_validator(mode="after")
    def _validate_candidate_posture(self) -> "AEISourceReadinessCandidate":
        if (
            self.candidate_state == "ready_for_internal_trial"
            and self.readiness_review_posture != "eligible"
        ):
            raise ValueError(
                "ready source-readiness candidates require eligible review posture"
            )
        if (
            self.candidate_state == "ready_for_internal_trial"
            and self.candidate_scope != "context_metadata_only"
        ):
            raise ValueError(
                "ready source-readiness candidates are limited to context metadata"
            )
        if (
            self.candidate_state == "ready_for_internal_trial"
            and self.blocked_evidence_classes
        ):
            raise ValueError("ready candidates must not carry blocked evidence classes")
        return self
