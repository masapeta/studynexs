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
