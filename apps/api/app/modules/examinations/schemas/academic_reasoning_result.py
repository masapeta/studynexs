"""Canonical AcademicReasoningResult model for AEI v1.

Batch 3 introduces academic semantics without marks, policy, teacher-review
routing, or Evaluation Service integration.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Literal, Mapping

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

ReasoningResultStatus = Literal[
    "interpreted",
    "equivalent",
    "not_equivalent",
    "matched",
    "not_matched",
    "balanced",
    "unbalanced",
    "checklist",
    "not_applicable",
]


class ReasonerTraceEntry(BaseModel):
    """Structured trace entry for one Academic Reasoner decision."""

    model_config = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=True)

    reasoner: str
    status: Literal["executed", "skipped"]
    supported: bool
    result: str | None = None
    metadata: Mapping[str, Any] = Field(default_factory=dict)

    @field_validator("metadata", mode="after")
    @classmethod
    def _freeze_metadata(cls, value: Mapping[str, Any]) -> Mapping[str, Any]:
        return _freeze_mapping(value)

    @field_serializer("metadata")
    def _serialize_metadata(self, value: Mapping[str, Any]) -> dict[str, Any]:
        return dict(value)


class AcademicReasoningResult(BaseModel):
    """Immutable top-level academic meaning result produced by Batch 3 reasoners."""

    model_config = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=True)

    reasoning_type: str
    result: ReasoningResultStatus
    subject: str | None = None
    capability: str | None = None
    explanation: str | None = None
    interpreted_value: str | None = None
    matched_value: str | None = None
    evidence: Mapping[str, Any] = Field(default_factory=dict)
    review_signals: tuple[str, ...] = ()
    reasoner_trace: tuple[ReasonerTraceEntry, ...] = ()
    metadata: Mapping[str, Any] = Field(default_factory=dict)

    @field_validator("evidence", "metadata", mode="after")
    @classmethod
    def _freeze_mapping_fields(cls, value: Mapping[str, Any]) -> Mapping[str, Any]:
        return _freeze_mapping(value)

    @field_serializer("evidence", "metadata")
    def _serialize_mapping_fields(self, value: Mapping[str, Any]) -> dict[str, Any]:
        return dict(value)


def _freeze_mapping(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(value))
