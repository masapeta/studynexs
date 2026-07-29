"""Passive mastery spine contracts.

These models are internal Phase A contracts for topic-ID / mastery spine
unification. They do not alter mastery persistence or product-facing output.
"""

from __future__ import annotations

import uuid
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

MasterySpineLevel = Literal[
    "learning_outcome",
    "concept",
    "topic",
    "label",
    "unresolved",
]
MasterySpineResolutionStatus = Literal[
    "resolved",
    "legacy_fallback",
    "ambiguous",
    "unresolved",
    "unsupported",
]
MasterySpineAuthorityPosture = Literal[
    "canonical",
    "legacy",
    "ambiguous",
    "unresolved",
    "unsupported",
]


class MasterySpineProvenance(BaseModel):
    """Where a passive mastery spine reference came from."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    source: str
    source_id: str | None = None
    resolved_from: str
    precedence: int
    metadata: dict[str, Any] = Field(default_factory=dict)


class MasterySpineAmbiguity(BaseModel):
    """Structured ambiguity evidence for safe passive resolution."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    reason: str
    candidates: tuple[dict[str, Any], ...] = ()
    metadata: dict[str, Any] = Field(default_factory=dict)


class MasterySpineReference(BaseModel):
    """Canonical passive learning-intelligence spine reference.

    Labels are display/provenance only. IDs and EducationalIdentity references
    are the future authority once a later source-adoption phase is authorized.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    tenant_id: uuid.UUID
    school_id: uuid.UUID
    academic_year_id: uuid.UUID | None = None
    class_id: uuid.UUID | None = None
    subject_id: uuid.UUID | None = None
    pack_id: uuid.UUID | None = None
    chapter_id: uuid.UUID | None = None
    topic_id: uuid.UUID | None = None
    concept_id: uuid.UUID | None = None
    learning_outcome_id: uuid.UUID | None = None
    educational_identity_id: str | None = Field(default=None, pattern=r"^ei://")
    spine_level: MasterySpineLevel
    label: str | None = None
    language: str | None = None
    resolution_status: MasterySpineResolutionStatus
    authority_posture: MasterySpineAuthorityPosture
    provenance: MasterySpineProvenance
    ambiguities: tuple[MasterySpineAmbiguity, ...] = ()
    metadata: dict[str, Any] = Field(default_factory=dict)


class MasterySpineResolutionReference(BaseModel):
    """Input contract for passive mastery spine resolution."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    school_id: uuid.UUID
    tenant_id: uuid.UUID | None = None
    academic_year_id: uuid.UUID | None = None
    class_id: uuid.UUID | None = None
    subject_id: uuid.UUID | None = None
    pack_id: uuid.UUID | None = None
    chapter_id: uuid.UUID | None = None
    topic_id: uuid.UUID | None = None
    concept_id: uuid.UUID | None = None
    learning_outcome_id: uuid.UUID | None = None
    educational_identity_id: str | None = Field(default=None, pattern=r"^ei://")
    educational_identity_metadata: dict[str, Any] = Field(default_factory=dict)
    raw_label: str | None = None
    language: str | None = None
    source: str = "legacy_mastery_topic"
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def effective_tenant_id(self) -> uuid.UUID:
        return self.tenant_id or self.school_id

    @model_validator(mode="after")
    def _validate_tenant_scope(self) -> "MasterySpineResolutionReference":
        if self.tenant_id is not None and self.tenant_id != self.school_id:
            raise ValueError("tenant_id must match school_id for passive mastery spine resolution")
        return self
