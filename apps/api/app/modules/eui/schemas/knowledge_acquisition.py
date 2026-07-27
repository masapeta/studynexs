"""Knowledge Acquisition Intelligence contracts for EUI Phase 4.

Phase 4 represents educational inputs as governed candidates only. It does not
persist artifacts, update EKG, migrate consumers, call providers, or change
product behavior.
"""

from __future__ import annotations

import uuid
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.modules.eui.schemas.platform_capability import CapabilityMode

KnowledgeAcquisitionSourceType = Literal[
    "pdf",
    "worksheet",
    "ocr_text",
    "answer_key",
    "teacher_note",
    "lesson_plan",
    "student_work",
    "image",
    "voice",
    "unknown",
]

KnowledgeAcquisitionModality = Literal[
    "document",
    "text",
    "image",
    "audio",
    "mixed",
    "unknown",
]

SourceAdmissionStatus = Literal["admitted", "needs_review", "unsupported"]
ExtractionStatus = Literal[
    "not_attempted",
    "supplied",
    "partial",
    "unsupported",
    "failed",
    "ambiguous",
]
CandidateReviewStatus = Literal[
    "candidate",
    "needs_review",
    "unsupported",
    "ambiguous",
    "approved_source",
]


class KnowledgeAcquisitionProvenance(BaseModel):
    """Where the candidate came from.

    Provenance is deliberately separate from trust signals. Provenance answers
    source/version/checksum lineage; trust signals answer reliability and review
    posture.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    source: str
    source_reference: str | None = None
    source_version: str | None = None
    checksum: str | None = None
    page_number: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class KnowledgeAcquisitionTrustSignals(BaseModel):
    """Phase 4 trust-signal placeholders, not the full Trust Framework."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    input_quality: str | None = None
    extraction_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    language_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    capability_mode: CapabilityMode | None = None
    review_required: bool = True
    ambiguity_count: int = Field(default=0, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class KnowledgeAcquisitionInputReference(BaseModel):
    """Input reference for passive KAI candidate generation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    tenant_id: uuid.UUID
    source_type: KnowledgeAcquisitionSourceType
    artifact_type: str | None = None
    source_reference: str | None = None
    source_version: str | None = None
    checksum: str | None = None
    page_number: int | None = None
    modality: KnowledgeAcquisitionModality | None = None
    supplied_extracted_text: str | None = None
    detected_language: str | None = None
    detected_script: str | None = None
    educational_identity_id: str | None = None
    educational_context_summary: dict[str, Any] = Field(default_factory=dict)
    capability_domain: str | None = None
    capability_key: str | None = None
    input_quality: str | None = None
    extraction_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    language_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SourceAdmissionDecision(BaseModel):
    """Deterministic admission posture for a KAI input source."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    status: SourceAdmissionStatus
    reason: str
    review_required: bool


class EducationalArtifactCandidate(BaseModel):
    """Canonical passive KAI candidate object.

    This object is non-authoritative in Phase 4. No product consumer may depend
    on it until a later migration is explicitly authorized.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(pattern=r"^kai://")
    tenant_id: uuid.UUID
    source_type: KnowledgeAcquisitionSourceType
    artifact_type: str | None = None
    modality: KnowledgeAcquisitionModality
    source_admission_status: SourceAdmissionStatus
    extraction_status: ExtractionStatus
    review_status: CandidateReviewStatus
    extracted_text: str | None = None
    normalized_content: dict[str, Any] = Field(default_factory=dict)
    detected_language: str | None = None
    detected_script: str | None = None
    educational_identity_id: str | None = None
    educational_context_summary: dict[str, Any] = Field(default_factory=dict)
    capability_mode: CapabilityMode | None = None
    capability_matched: bool = False
    provenance: KnowledgeAcquisitionProvenance
    trust_signals: KnowledgeAcquisitionTrustSignals
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def authoritative(self) -> bool:
        return False
