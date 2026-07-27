"""Canonical AcademicAnswer model for Academic Evaluation Intelligence v1.

Batch 1 intentionally defines only the shared data object. It does not normalize,
reason about, score, route, or evaluate answers. Later AEI batches enrich this
object through providers, reasoning, and policy.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AcademicAnswer(BaseModel):
    """Canonical internal answer object carried through the AEI pipeline.

    The model preserves raw input for auditability while giving later AEI layers a
    stable place to add normalized input, language/script detection, visual/science
    classification, confidence, and provider metadata.
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    raw_input: str | None = Field(frozen=True)
    normalized_input: str | None = None
    subject: str | None = None
    question_type: str | None = None
    detected_language: str | None = None
    detected_script: str | None = None
    code_mixed: bool = False
    visual_type: str | None = None
    scientific_type: str | None = None
    math_type: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    confidence_reason: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
