"""Educational Knowledge Graph proposal contracts for EUI Phase 5.

Phase 5 represents graph relationship proposals only. It does not persist graph
edges, expand database enums, migrate consumers, or change product behavior.
"""

from __future__ import annotations

import uuid
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.modules.eui.schemas.educational_context import EducationalContext
from app.modules.eui.schemas.educational_identity import EducationalIdentity
from app.modules.eui.schemas.knowledge_acquisition import EducationalArtifactCandidate
from app.modules.eui.schemas.platform_capability import CapabilityMode

EducationalGraphRelationshipCategory = Literal[
    "identity_link",
    "learning_objective",
    "competency",
    "prerequisite",
    "candidate_evidence",
    "misconception",
    "intervention",
    "unsupported",
]

EducationalGraphProposalStatus = Literal[
    "proposed",
    "missing_target",
    "ambiguous",
    "unsupported",
]

EducationalGraphAuthorityPosture = Literal[
    "candidate",
    "needs_review",
    "unsupported",
    "ambiguous",
]

EducationalGraphReferenceType = Literal[
    "educational_identity",
    "kg_node",
    "kai_candidate",
    "unknown",
]


class EducationalGraphReference(BaseModel):
    """A non-persistent endpoint reference for a graph relationship proposal."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    reference_type: EducationalGraphReferenceType
    id: str | None = None
    node_type: str | None = None
    label: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class EducationalGraphAmbiguity(BaseModel):
    """Why a relationship proposal could not resolve to one graph target."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    reason: str
    candidates: tuple[EducationalGraphReference, ...] = ()
    metadata: dict[str, Any] = Field(default_factory=dict)


class EducationalGraphProvenance(BaseModel):
    """Where the relationship proposal came from.

    Provenance remains separate from trust placeholders. Provenance answers
    source lineage; trust placeholders answer whether this proposal is reliable
    enough for future authorized consumers.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    source: str
    source_id: str | None = None
    source_version: str | None = None
    relationship_source: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class EducationalGraphTrustPlaceholders(BaseModel):
    """Phase 5 trust placeholders, not the full Trust Framework."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    capability_mode: CapabilityMode | None = None
    review_required: bool = True
    ambiguity_count: int = Field(default=0, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EducationalGraphRelationshipReference(BaseModel):
    """Input reference for passive EKG relationship proposal generation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    tenant_id: uuid.UUID
    educational_identity: EducationalIdentity | None = None
    educational_identity_id: str | None = None
    educational_context: EducationalContext | None = None
    educational_context_summary: dict[str, Any] = Field(default_factory=dict)
    kai_candidate: EducationalArtifactCandidate | None = None
    relationship_category: EducationalGraphRelationshipCategory | None = None
    target_node_id: str | None = None
    target_node_type: str | None = None
    target_label: str | None = None
    candidate_target_references: tuple[EducationalGraphReference, ...] = ()
    capability_mode: CapabilityMode | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def proposal_kind(self) -> str:
        if self.kai_candidate is not None:
            return "kai_candidate"
        if self.educational_identity is not None or self.educational_identity_id:
            return "educational_identity"
        return "unsupported"


class EducationalGraphRelationshipProposal(BaseModel):
    """Canonical passive EKG relationship proposal object.

    This object is not a trusted graph edge. No consumer may depend on it until
    a later migration is explicitly authorized.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(pattern=r"^ekg-proposal://")
    tenant_id: uuid.UUID
    relationship_category: EducationalGraphRelationshipCategory
    status: EducationalGraphProposalStatus
    from_reference: EducationalGraphReference
    to_reference: EducationalGraphReference
    educational_identity_id: str | None = None
    educational_context_summary: dict[str, Any] = Field(default_factory=dict)
    source_candidate_id: str | None = None
    capability_mode: CapabilityMode | None = None
    authority_posture: EducationalGraphAuthorityPosture
    provenance: EducationalGraphProvenance
    trust_placeholders: EducationalGraphTrustPlaceholders
    ambiguities: tuple[EducationalGraphAmbiguity, ...] = ()
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def authoritative(self) -> bool:
        return False
