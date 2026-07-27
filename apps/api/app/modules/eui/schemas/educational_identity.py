"""Canonical Educational Identity contracts for EUI Phase 1.

Phase 1 defines stable identity objects only. It does not add persistence,
consumer migration, context-engine behavior, or product-facing output changes.
"""

from __future__ import annotations

import uuid
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class EducationalIdentityProvenance(BaseModel):
    """Where an Educational Identity was resolved from.

    Provenance is deliberately separate from future Trust Reports. Provenance
    answers source/version/approval lineage; trust answers reliability and
    review posture.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    source: str
    source_id: str | None = None
    source_version: str | None = None
    resolved_from: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class EducationalIdentity(BaseModel):
    """Canonical identity object shared by future EUI consumers."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(pattern=r"^ei://")
    tenant_id: uuid.UUID
    board: str
    curriculum: str
    curriculum_version: str
    grade: str
    subject: str
    unit: str | None = None
    chapter: str | None = None
    topic: str | None = None
    concepts: tuple[str, ...] = ()
    competencies: tuple[str, ...] = ()
    learning_objectives: tuple[str, ...] = ()
    language: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    provenance: EducationalIdentityProvenance


class EducationalIdentityReference(BaseModel):
    """Input reference that can be resolved into an EducationalIdentity."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    school_id: uuid.UUID
    pack_id: uuid.UUID | None = None
    chapter_id: uuid.UUID | None = None
    topic_id: uuid.UUID | None = None
    concept_id: uuid.UUID | None = None
    learning_outcome_id: uuid.UUID | None = None
    raw_label: str | None = None
    board: str | None = None
    grade: str | None = None
    subject: str | None = None
    artifact_type: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def resolution_kind(self) -> Literal[
        "concept",
        "learning_outcome",
        "topic",
        "chapter",
        "pack",
        "label",
        "empty",
    ]:
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
        if self.raw_label and self.raw_label.strip():
            return "label"
        return "empty"
