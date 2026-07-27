"""AEI consumer migration contracts for EUI Phase 7A.

Phase 7A is passive dual-read only. These contracts capture internal
comparison evidence between the existing AEI/evaluation path and EUI-derived
signals without changing marks, routing, evidence, API, UI, or source of truth.
"""

from __future__ import annotations

import uuid
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.modules.eui.schemas.platform_capability import CapabilityMode

AEIConsumerMigrationSubjectType = Literal[
    "answer_sheet_evaluation",
    "evaluation_request",
    "academic_answer",
    "unknown",
]

AEIConsumerMigrationMode = Literal["dual_read"]

AEIConsumerMigrationDifferenceType = Literal[
    "equivalent",
    "eui_richer",
    "eui_missing",
    "legacy_ambiguous",
    "product_impacting",
    "unsafe",
]

AEIConsumerMigrationCaptureStatus = Literal[
    "completed",
    "diverged",
    "unsafe_difference",
    "failed",
]


class AEIConsumerMigrationDifference(BaseModel):
    """One deterministic internal comparison signal.

    Difference records are internal evidence only. They intentionally carry
    bounded labels and metadata, not raw answers, OCR text, uploaded content, or
    human free text.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    difference_type: AEIConsumerMigrationDifferenceType
    reason: str
    blocker: bool = False
    legacy_signal: str | None = None
    eui_signal: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AEIConsumerMigrationComparison(BaseModel):
    """Canonical passive dual-read comparison for AEI as an EUI consumer."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(pattern=r"^eui-aei-migration://")
    tenant_id: uuid.UUID
    subject_type: AEIConsumerMigrationSubjectType
    subject_ref: str
    mode: AEIConsumerMigrationMode = "dual_read"
    legacy_source: str = "aei_evaluation"
    eui_source: str = "eui_passive_foundation"
    legacy_summary: dict[str, Any] = Field(default_factory=dict)
    eui_summary: dict[str, Any] = Field(default_factory=dict)
    differences: tuple[AEIConsumerMigrationDifference, ...] = ()
    trust_report_ref: str | None = None
    trust_posture: str | None = None
    trust_consumer_visibility: str | None = None
    eui_identity_present: bool = False
    eui_context_present: bool = False
    capability_mode: CapabilityMode | None = None
    dual_read_enabled: bool = True
    source_flag_enabled: bool = False
    # Phase 7A explicitly forbids EUI source-of-truth switching. Use a literal
    # False field so accidental construction with True fails validation.
    source_switch_active: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def authoritative(self) -> bool:
        return False

    @property
    def has_blockers(self) -> bool:
        return any(difference.blocker for difference in self.differences)

    @property
    def difference_types(self) -> tuple[str, ...]:
        return tuple(difference.difference_type for difference in self.differences)


class AEIConsumerMigrationCapture(BaseModel):
    """Bounded passive capture for validation and certification only."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    subject_type: AEIConsumerMigrationSubjectType
    subject_ref: str
    status: AEIConsumerMigrationCaptureStatus
    duration_ms: float = Field(ge=0.0)
    comparison: AEIConsumerMigrationComparison | None = None
    error: str | None = None
