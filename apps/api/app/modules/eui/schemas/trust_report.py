"""Trust Report contracts for EUI Phase 6.

Phase 6 produces passive, deterministic Trust Reports beside existing EUI
signals. It does not persist reports, migrate consumers, call LLMs, or change
product behavior.
"""

from __future__ import annotations

import uuid
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.modules.eui.schemas.platform_capability import CapabilityMode

TrustSubjectType = Literal[
    "educational_context",
    "platform_capability_lookup",
    "kai_candidate",
    "ekg_relationship_proposal",
]

TrustDimensionKey = Literal[
    "input_quality",
    "extraction_quality",
    "ocr_confidence",
    "language_confidence",
    "understanding_confidence",
    "subject_confidence",
    "reasoning_confidence",
    "policy_confidence",
    "evidence_availability",
    "human_review_status",
    "auditability",
    "capability_mode",
]

TrustDimensionStatus = Literal[
    "strong",
    "partial",
    "weak",
    "missing",
    "unsupported",
    "not_applicable",
]

TrustOverallPosture = Literal[
    "trusted",
    "review_recommended",
    "manual_review_required",
    "unsupported",
    "insufficient_evidence",
]

TrustWarningSeverity = Literal["info", "warning", "blocker"]

TrustConsumerVisibility = Literal[
    "internal_only",
    "teacher_safe",
    "school_leader_safe",
    "parent_safe",
    "student_safe",
]


class TrustWarning(BaseModel):
    """Structured Trust Report warning."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    code: str
    severity: TrustWarningSeverity
    message: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class TrustProvenanceReference(BaseModel):
    """Reference to source provenance without merging provenance into trust."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    source: str
    source_id: str | None = None
    source_version: str | None = None
    subject_ref: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TrustDimension(BaseModel):
    """One dimension of trust.

    Scores are explanatory only. Authority is derived from status and
    conservative posture precedence, not score averaging.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    status: TrustDimensionStatus
    reason: str
    score: float | None = Field(default=None, ge=0.0, le=1.0)
    evidence_refs: tuple[str, ...] = ()
    warnings: tuple[TrustWarning, ...] = ()
    metadata: dict[str, Any] = Field(default_factory=dict)


class TrustReport(BaseModel):
    """Canonical passive Trust Report object.

    This object is non-authoritative in Phase 6. No consumer may depend on it
    until a later migration is explicitly authorized.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(pattern=r"^trust-report://")
    tenant_id: uuid.UUID
    subject_type: TrustSubjectType
    subject_ref: str
    overall_posture: TrustOverallPosture
    dimensions: dict[TrustDimensionKey, TrustDimension]
    review_required: bool
    evidence_available: bool
    capability_mode: CapabilityMode | None = None
    consumer_visibility: TrustConsumerVisibility = "internal_only"
    provenance_refs: tuple[TrustProvenanceReference, ...] = ()
    warnings: tuple[TrustWarning, ...] = ()
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def authoritative(self) -> bool:
        return False
