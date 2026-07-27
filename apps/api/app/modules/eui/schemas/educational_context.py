"""Canonical Educational Context contracts for EUI Phase 1 Sprint 2.

Educational Context is passive in this sprint. It captures the educational
situation around an artifact without changing consumers, evaluation behavior,
schema, API, or UI.
"""

from __future__ import annotations

import uuid
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.modules.eui.schemas.educational_identity import EducationalIdentity

ContextResolutionStatus = Literal["resolved", "resolved_with_conflicts", "ambiguous", "partial"]


class EducationalContextConflict(BaseModel):
    """A lower-precedence context source disagreed with the chosen value."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    field: str
    chosen_source: str
    rejected_source: str
    chosen_value: str
    rejected_value: str


class EducationalContextAmbiguity(BaseModel):
    """Why a context could not be resolved to one authoritative candidate."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    reason: str
    source_fields: tuple[str, ...] = ()
    candidates: tuple[str, ...] = ()


class EducationalContextProvenance(BaseModel):
    """Where Educational Context was assembled from."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    source: str
    resolved_from: str
    source_id: str | None = None
    source_version: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class EducationalContext(BaseModel):
    """Canonical passive context object for future EUI consumers."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    tenant_id: uuid.UUID
    resolution_status: ContextResolutionStatus
    academic_year_id: uuid.UUID | None = None
    academic_year: str | None = None
    board: str | None = None
    curriculum: str | None = None
    curriculum_version: str | None = None
    grade: str | None = None
    section: str | None = None
    subject: str | None = None
    curriculum_pack_id: uuid.UUID | None = None
    educational_identity_id: str | None = None
    chapter: str | None = None
    topic: str | None = None
    concepts: tuple[str, ...] = ()
    competencies: tuple[str, ...] = ()
    learning_objectives: tuple[str, ...] = ()
    assessment_mode: str | None = None
    language_medium: str | None = None
    evidence_posture: str | None = None
    field_sources: dict[str, str] = Field(default_factory=dict)
    conflicts: tuple[EducationalContextConflict, ...] = ()
    ambiguities: tuple[EducationalContextAmbiguity, ...] = ()
    provenance: EducationalContextProvenance
    metadata: dict[str, Any] = Field(default_factory=dict)


class EducationalContextReference(BaseModel):
    """Input reference that can be passively resolved into EducationalContext."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    school_id: uuid.UUID
    educational_identity: EducationalIdentity | None = None
    educational_identity_id: str | None = None
    pack_id: uuid.UUID | None = None
    chapter_id: uuid.UUID | None = None
    topic_id: uuid.UUID | None = None
    concept_id: uuid.UUID | None = None
    learning_outcome_id: uuid.UUID | None = None
    artifact_type: str | None = None
    artifact_id: uuid.UUID | None = None
    academic_year_id: uuid.UUID | None = None
    academic_year: str | None = None
    board: str | None = None
    curriculum: str | None = None
    curriculum_version: str | None = None
    grade: str | None = None
    section: str | None = None
    subject: str | None = None
    chapter: str | None = None
    topic: str | None = None
    concepts: tuple[str, ...] = ()
    competencies: tuple[str, ...] = ()
    learning_objectives: tuple[str, ...] = ()
    assessment_mode: str | None = None
    language_medium: str | None = None
    evidence_posture: str | None = None
    candidate_context_ids: tuple[str, ...] = ()
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def resolution_kind(self) -> str:
        if self.educational_identity is not None or self.educational_identity_id:
            return "educational_identity"
        if self.concept_id is not None:
            return "concept"
        if self.learning_outcome_id is not None:
            return "learning_outcome"
        if self.topic_id is not None:
            return "topic"
        if self.chapter_id is not None:
            return "chapter"
        if self.pack_id is not None:
            return "pack"
        if self.artifact_type or self.artifact_id:
            return "artifact"
        if self.candidate_context_ids:
            return "candidate_context"
        return "metadata"
