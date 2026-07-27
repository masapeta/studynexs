"""Platform Capability Registry contracts for EUI Phase 1 Sprint 3.

The registry declares what StudyNexs may internally treat as supported,
assistive, checklist-only, manual-review, unsupported, or expansion posture for
an educational scope. It does not implement capabilities and it does not create
public product claims.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

CapabilityMode = Literal[
    "supported",
    "assist",
    "checklist",
    "manual_review",
    "unsupported",
    "expansion",
]

CertificationStatus = Literal[
    "certified",
    "foundation",
    "planned",
    "uncertified",
]

SUPPORTED_CAPABILITY_MODES: set[str] = {
    "supported",
    "assist",
    "checklist",
    "manual_review",
    "unsupported",
    "expansion",
}

REVIEW_REQUIRED_CAPABILITY_MODES: set[str] = {
    "assist",
    "checklist",
    "manual_review",
    "unsupported",
    "expansion",
}

# Lower rank means lower product claim. Same-specificity conflicts resolve to
# the lowest rank so the platform under-claims rather than over-claims.
CAPABILITY_MODE_CLAIM_RANK: dict[str, int] = {
    "unsupported": 0,
    "expansion": 1,
    "manual_review": 2,
    "assist": 3,
    "checklist": 3,
    "supported": 4,
}


class PlatformCapabilityScope(BaseModel):
    """Educational scope where a capability declaration applies.

    Empty fields act as wildcards during lookup. Keep this sparse and
    declarative; do not encode business logic in scope values.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    board: str | None = None
    curriculum: str | None = None
    curriculum_version: str | None = None
    grade: str | None = None
    subject: str | None = None
    language: str | None = None
    script: str | None = None
    input_type: str | None = None
    artifact_type: str | None = None
    assessment_mode: str | None = None

    def specificity(self) -> int:
        """Number of concrete dimensions declared by this scope."""

        return sum(1 for value in self.model_dump().values() if _present(value))


class PlatformCapabilityDeclaration(BaseModel):
    """One declarative platform capability posture entry."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(pattern=r"^pc://")
    domain: str
    capability_key: str
    mode: CapabilityMode
    scope: PlatformCapabilityScope = Field(default_factory=PlatformCapabilityScope)
    review_required: bool
    certification_status: CertificationStatus = "foundation"
    scope_statement: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def supported_for_declared_scope(self) -> bool:
        """Whether this entry is supported inside its internal declared scope.

        This is still internal in Sprint 3. Public claim generation remains
        unauthorized.
        """

        return self.mode == "supported"


class PlatformCapabilityRegistryPayload(BaseModel):
    """Versioned declarative registry payload."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    version: str
    authorization: str
    declarations: tuple[PlatformCapabilityDeclaration, ...]


class PlatformCapabilityLookupRequest(BaseModel):
    """Read-only lookup input derived from Educational Context-like fields."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    domain: str
    capability_key: str
    board: str | None = None
    curriculum: str | None = None
    curriculum_version: str | None = None
    grade: str | None = None
    subject: str | None = None
    language: str | None = None
    script: str | None = None
    input_type: str | None = None
    artifact_type: str | None = None
    assessment_mode: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class PlatformCapabilityLookupResult(BaseModel):
    """Passive lookup result.

    The result is internal evidence only in Sprint 3. No consumer may use it for
    product behavior until a later migration is explicitly authorized.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    registry_version: str
    request: PlatformCapabilityLookupRequest
    mode: CapabilityMode
    matched: bool
    authoritative: bool
    declaration: PlatformCapabilityDeclaration | None = None
    candidate_ids: tuple[str, ...] = ()
    conflict: bool = False
    fallback_reason: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def review_required(self) -> bool:
        return self.mode in REVIEW_REQUIRED_CAPABILITY_MODES

    @property
    def supported_for_declared_scope(self) -> bool:
        return self.mode == "supported" and self.authoritative and self.matched


def _present(value: Any) -> bool:
    return value is not None and value != ""
