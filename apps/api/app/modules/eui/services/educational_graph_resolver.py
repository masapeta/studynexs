"""Passive Educational Knowledge Graph relationship proposal resolver."""

from __future__ import annotations

from typing import Any

from app.modules.eui.schemas.educational_graph import (
    EducationalGraphAmbiguity,
    EducationalGraphAuthorityPosture,
    EducationalGraphProposalStatus,
    EducationalGraphProvenance,
    EducationalGraphReference,
    EducationalGraphRelationshipCategory,
    EducationalGraphRelationshipProposal,
    EducationalGraphRelationshipReference,
    EducationalGraphTrustPlaceholders,
)
from app.modules.eui.schemas.educational_identity import EducationalIdentity
from app.modules.eui.schemas.knowledge_acquisition import EducationalArtifactCandidate
from app.modules.eui.services.educational_graph_proposal_id import (
    stable_educational_graph_proposal_id,
)


class EducationalGraphProposalResolver:
    """Build non-authoritative EKG relationship proposals.

    This resolver is deliberately proposal-only. It does not persist graph
    edges, expand database enums, migrate consumers, or write to existing KG
    tables.
    """

    def propose(
        self,
        reference: EducationalGraphRelationshipReference,
    ) -> EducationalGraphRelationshipProposal:
        if reference.educational_identity is not None:
            if reference.educational_identity.tenant_id != reference.tenant_id:
                return self._unsupported_proposal(reference, reason="identity_tenant_mismatch")
        if reference.educational_context is not None:
            if reference.educational_context.tenant_id != reference.tenant_id:
                return self._unsupported_proposal(reference, reason="context_tenant_mismatch")
        if reference.kai_candidate is not None:
            return self._candidate_proposal(reference)
        if reference.educational_identity is not None or reference.educational_identity_id:
            return self._identity_proposal(reference)
        return self._unsupported_proposal(reference, reason="unsupported_reference_kind")

    def _identity_proposal(
        self,
        reference: EducationalGraphRelationshipReference,
    ) -> EducationalGraphRelationshipProposal:
        identity_id = _identity_id(reference)
        from_reference = EducationalGraphReference(
            reference_type="educational_identity",
            id=identity_id,
            label=_identity_label(reference.educational_identity),
            metadata={"source": "educational_identity"},
        )
        category = reference.relationship_category or "identity_link"
        target, status, authority, ambiguities = self._target_for_identity(reference)
        return self._proposal(
            reference=reference,
            relationship_category=category,
            status=status,
            authority_posture=authority,
            from_reference=from_reference,
            to_reference=target,
            educational_identity_id=identity_id,
            source_candidate_id=None,
            provenance=EducationalGraphProvenance(
                source="educational_graph_proposal_resolver",
                source_id=identity_id,
                relationship_source="educational_identity",
                metadata={
                    "authorization": "EUI-PH5-EKG-AUTH-001",
                    "passive": True,
                    "proposal_only": True,
                },
            ),
            ambiguities=ambiguities,
        )

    def _candidate_proposal(
        self,
        reference: EducationalGraphRelationshipReference,
    ) -> EducationalGraphRelationshipProposal:
        candidate = reference.kai_candidate
        assert candidate is not None

        from_reference = EducationalGraphReference(
            reference_type="kai_candidate",
            id=candidate.id,
            node_type=candidate.artifact_type,
            label=candidate.source_type,
            metadata={
                "review_status": candidate.review_status,
                "source_admission_status": candidate.source_admission_status,
            },
        )
        category = reference.relationship_category or "candidate_evidence"
        target, status, authority, ambiguities = self._target_for_candidate(reference, candidate)
        return self._proposal(
            reference=reference,
            relationship_category=category,
            status=status,
            authority_posture=authority,
            from_reference=from_reference,
            to_reference=target,
            educational_identity_id=candidate.educational_identity_id
            or reference.educational_identity_id,
            source_candidate_id=candidate.id,
            provenance=EducationalGraphProvenance(
                source="educational_graph_proposal_resolver",
                source_id=candidate.id,
                source_version=candidate.provenance.source_version,
                relationship_source="kai_candidate",
                metadata={
                    "authorization": "EUI-PH5-EKG-AUTH-001",
                    "passive": True,
                    "proposal_only": True,
                    "candidate_provenance_source": candidate.provenance.source,
                },
            ),
            ambiguities=ambiguities,
        )

    def _target_for_identity(
        self,
        reference: EducationalGraphRelationshipReference,
    ) -> tuple[
        EducationalGraphReference,
        EducationalGraphProposalStatus,
        EducationalGraphAuthorityPosture,
        tuple[EducationalGraphAmbiguity, ...],
    ]:
        if len(reference.candidate_target_references) > 1:
            ambiguity = EducationalGraphAmbiguity(
                reason="multiple_graph_targets",
                candidates=reference.candidate_target_references,
            )
            return _unknown_target(), "ambiguous", "ambiguous", (ambiguity,)
        if len(reference.candidate_target_references) == 1:
            return reference.candidate_target_references[0], "proposed", "candidate", ()
        explicit = _explicit_target(reference)
        if explicit is not None:
            return explicit, "proposed", "candidate", ()
        identity_target = _target_from_identity_metadata(reference.educational_identity)
        if identity_target is not None:
            return identity_target, "proposed", "candidate", ()
        ambiguity = EducationalGraphAmbiguity(
            reason="identity_has_no_graph_target",
            metadata={"identity_id": _identity_id(reference)},
        )
        return _unknown_target(), "missing_target", "needs_review", (ambiguity,)

    def _target_for_candidate(
        self,
        reference: EducationalGraphRelationshipReference,
        candidate: EducationalArtifactCandidate,
    ) -> tuple[
        EducationalGraphReference,
        EducationalGraphProposalStatus,
        EducationalGraphAuthorityPosture,
        tuple[EducationalGraphAmbiguity, ...],
    ]:
        if candidate.tenant_id != reference.tenant_id:
            ambiguity = EducationalGraphAmbiguity(
                reason="tenant_mismatch",
                metadata={
                    "candidate_tenant_id": str(candidate.tenant_id),
                    "reference_tenant_id": str(reference.tenant_id),
                },
            )
            return _unknown_target(), "unsupported", "unsupported", (ambiguity,)
        if candidate.review_status == "unsupported":
            return _unknown_target(), "unsupported", "unsupported", ()
        if len(reference.candidate_target_references) > 1:
            ambiguity = EducationalGraphAmbiguity(
                reason="multiple_graph_targets",
                candidates=reference.candidate_target_references,
            )
            return _unknown_target(), "ambiguous", "ambiguous", (ambiguity,)
        if len(reference.candidate_target_references) == 1:
            return reference.candidate_target_references[0], "proposed", "candidate", ()
        explicit = _explicit_target(reference)
        if explicit is not None:
            return explicit, "proposed", _candidate_authority(candidate), ()
        identity_id = candidate.educational_identity_id or reference.educational_identity_id
        if identity_id:
            return (
                EducationalGraphReference(
                    reference_type="educational_identity",
                    id=identity_id,
                    metadata={"source": "kai_candidate_identity"},
                ),
                "proposed",
                _candidate_authority(candidate),
                (),
            )
        ambiguity = EducationalGraphAmbiguity(
            reason="candidate_has_no_graph_target",
            metadata={"candidate_review_status": candidate.review_status},
        )
        return _unknown_target(), "ambiguous", "ambiguous", (ambiguity,)

    def _unsupported_proposal(
        self,
        reference: EducationalGraphRelationshipReference,
        *,
        reason: str,
    ) -> EducationalGraphRelationshipProposal:
        return self._proposal(
            reference=reference,
            relationship_category=reference.relationship_category or "unsupported",
            status="unsupported",
            authority_posture="unsupported",
            from_reference=EducationalGraphReference(
                reference_type="unknown",
                metadata={"reason": reason},
            ),
            to_reference=_unknown_target(),
            educational_identity_id=reference.educational_identity_id,
            source_candidate_id=None,
            provenance=EducationalGraphProvenance(
                source="educational_graph_proposal_resolver",
                relationship_source="unsupported",
                metadata={
                    "authorization": "EUI-PH5-EKG-AUTH-001",
                    "passive": True,
                    "proposal_only": True,
                    "reason": reason,
                },
            ),
            ambiguities=(
                EducationalGraphAmbiguity(
                    reason=reason,
                ),
            ),
        )

    def _proposal(
        self,
        *,
        reference: EducationalGraphRelationshipReference,
        relationship_category: EducationalGraphRelationshipCategory,
        status: EducationalGraphProposalStatus,
        authority_posture: EducationalGraphAuthorityPosture,
        from_reference: EducationalGraphReference,
        to_reference: EducationalGraphReference,
        educational_identity_id: str | None,
        source_candidate_id: str | None,
        provenance: EducationalGraphProvenance,
        ambiguities: tuple[EducationalGraphAmbiguity, ...],
    ) -> EducationalGraphRelationshipProposal:
        proposal_id = stable_educational_graph_proposal_id(
            reference,
            relationship_category=relationship_category,
            status=status,
            target_reference_id=to_reference.id,
        )
        return EducationalGraphRelationshipProposal(
            id=proposal_id,
            tenant_id=reference.tenant_id,
            relationship_category=relationship_category,
            status=status,
            from_reference=from_reference,
            to_reference=to_reference,
            educational_identity_id=educational_identity_id,
            educational_context_summary=_context_summary(reference),
            source_candidate_id=source_candidate_id,
            capability_mode=_capability_mode(reference),
            authority_posture=authority_posture,
            provenance=provenance,
            trust_placeholders=EducationalGraphTrustPlaceholders(
                capability_mode=_capability_mode(reference),
                review_required=True,
                ambiguity_count=len(ambiguities),
                metadata={
                    "status": status,
                    "proposal_only": True,
                },
            ),
            ambiguities=ambiguities,
            metadata={
                "authorization": "EUI-PH5-EKG-AUTH-001",
                "passive": True,
                "proposal_only": True,
                "runtime_authoritative": False,
            },
        )


def _identity_id(reference: EducationalGraphRelationshipReference) -> str | None:
    if reference.educational_identity is not None:
        return reference.educational_identity.id
    return reference.educational_identity_id


def _identity_label(identity: EducationalIdentity | None) -> str | None:
    if identity is None:
        return None
    for value in (
        identity.concepts[0] if identity.concepts else None,
        identity.topic,
        identity.chapter,
        identity.subject,
    ):
        if value:
            return value
    return identity.id


def _explicit_target(
    reference: EducationalGraphRelationshipReference,
) -> EducationalGraphReference | None:
    if not reference.target_node_id:
        return None
    return EducationalGraphReference(
        reference_type="kg_node",
        id=reference.target_node_id,
        node_type=reference.target_node_type,
        label=reference.target_label,
        metadata={"source": "explicit_target"},
    )


def _target_from_identity_metadata(
    identity: EducationalIdentity | None,
) -> EducationalGraphReference | None:
    if identity is None:
        return None
    metadata = identity.metadata
    for key, node_type, label in (
        ("concept_id", "concept", identity.concepts[0] if identity.concepts else None),
        ("topic_id", "topic", identity.topic),
        ("chapter_id", "chapter", identity.chapter),
        ("pack_id", "pack", identity.subject),
        ("learning_outcome_id", "learning_objective", _first(identity.learning_objectives)),
    ):
        value = metadata.get(key)
        if value:
            return EducationalGraphReference(
                reference_type="kg_node",
                id=str(value),
                node_type=node_type,
                label=label,
                metadata={"source": "educational_identity_metadata", "metadata_key": key},
            )
    return None


def _candidate_authority(
    candidate: EducationalArtifactCandidate,
) -> EducationalGraphAuthorityPosture:
    if candidate.review_status == "needs_review":
        return "needs_review"
    if candidate.review_status == "ambiguous":
        return "ambiguous"
    if candidate.review_status == "unsupported":
        return "unsupported"
    return "candidate"


def _capability_mode(reference: EducationalGraphRelationshipReference):
    if reference.capability_mode:
        return reference.capability_mode
    if reference.kai_candidate is not None:
        return reference.kai_candidate.capability_mode
    return None


def _context_summary(reference: EducationalGraphRelationshipReference) -> dict[str, Any]:
    if reference.educational_context is not None:
        context = reference.educational_context
        return {
            "resolution_status": context.resolution_status,
            "board": context.board,
            "curriculum": context.curriculum,
            "curriculum_version": context.curriculum_version,
            "grade": context.grade,
            "subject": context.subject,
            "chapter": context.chapter,
            "topic": context.topic,
            "assessment_mode": context.assessment_mode,
            "language_medium": context.language_medium,
        }
    if reference.educational_context_summary:
        return dict(reference.educational_context_summary)
    if reference.kai_candidate is not None:
        return dict(reference.kai_candidate.educational_context_summary)
    return {}


def _unknown_target() -> EducationalGraphReference:
    return EducationalGraphReference(reference_type="unknown")


def _first(values: tuple[str, ...]) -> str | None:
    return values[0] if values else None
