"""EUI Phase 1 Sprint 3 — deterministic Platform Capability lookups."""

from __future__ import annotations

import uuid

from app.modules.eui.schemas.educational_context import (
    EducationalContext,
    EducationalContextProvenance,
)
from app.modules.eui.schemas.platform_capability import (
    PlatformCapabilityDeclaration,
    PlatformCapabilityLookupRequest,
    PlatformCapabilityRegistryPayload,
    PlatformCapabilityScope,
)
from app.modules.eui.services.platform_capability_lookup import PlatformCapabilityLookupService
from app.modules.eui.services.platform_capability_registry import PlatformCapabilityRegistry


def test_lookup_resolves_supported_math_numeric_normalization():
    service = PlatformCapabilityLookupService()

    result = service.lookup(
        PlatformCapabilityLookupRequest(
            domain="Mathematics",
            capability_key="Numeric Normalization",
            board="CBSE",
            curriculum="NCF2023",
            grade="10",
            subject="Mathematics",
        )
    )

    assert result.mode == "supported"
    assert result.matched is True
    assert result.conflict is False
    assert result.supported_for_declared_scope is True
    assert result.review_required is False


def test_lookup_missing_capability_fails_closed_to_unsupported():
    service = PlatformCapabilityLookupService()

    result = service.lookup(
        PlatformCapabilityLookupRequest(
            domain="commerce",
            capability_key="ledger_auto_grading",
            subject="Commerce",
        )
    )

    assert result.mode == "unsupported"
    assert result.matched is False
    assert result.authoritative is False
    assert result.fallback_reason == "missing_capability"
    assert result.supported_for_declared_scope is False
    assert result.review_required is True


def test_lookup_specific_entry_refines_broad_entry_without_upgrade():
    registry = PlatformCapabilityRegistry.from_payload(
        PlatformCapabilityRegistryPayload(
            version="specificity-test",
            authorization="EUI-PH1-SP3-AUTH-001",
            declarations=(
                PlatformCapabilityDeclaration(
                    id="pc://eui/test/graph_grading/broad",
                    domain="visual",
                    capability_key="graph_grading",
                    mode="supported",
                    scope=PlatformCapabilityScope(subject="Mathematics"),
                    review_required=False,
                ),
                PlatformCapabilityDeclaration(
                    id="pc://eui/test/graph_grading/specific",
                    domain="visual",
                    capability_key="graph_grading",
                    mode="checklist",
                    scope=PlatformCapabilityScope(subject="Mathematics", grade="10"),
                    review_required=True,
                ),
            ),
        )
    )
    service = PlatformCapabilityLookupService(registry)

    result = service.lookup(
        PlatformCapabilityLookupRequest(
            domain="visual",
            capability_key="graph_grading",
            grade="10",
            subject="Mathematics",
        )
    )

    assert result.mode == "checklist"
    assert result.declaration is not None
    assert result.declaration.id == "pc://eui/test/graph_grading/specific"
    assert result.supported_for_declared_scope is False


def test_lookup_conflict_resolves_to_lower_claim_and_non_authoritative():
    service = PlatformCapabilityLookupService()

    result = service.lookup(
        PlatformCapabilityLookupRequest(
            domain="test",
            capability_key="conflict_resolution_probe",
            board="CBSE",
            grade="8",
            subject="Science",
        )
    )

    assert result.mode == "manual_review"
    assert result.conflict is True
    assert result.authoritative is False
    assert result.fallback_reason == "conflicting_capability_entries"
    assert result.supported_for_declared_scope is False


def test_lookup_for_context_uses_educational_context_without_migrating_consumers():
    service = PlatformCapabilityLookupService()
    context = EducationalContext(
        tenant_id=uuid.uuid4(),
        resolution_status="resolved",
        board="CBSE",
        curriculum="NCF2023",
        curriculum_version="2024",
        grade="10",
        subject="Mathematics",
        provenance=EducationalContextProvenance(
            source="test",
            resolved_from="metadata",
        ),
    )

    result = service.lookup_for_context(
        context=context,
        domain="mathematics",
        capability_key="unit_conversion",
    )

    assert result.mode == "supported"
    assert result.matched is True


def test_aei_compatibility_entries_do_not_require_aei_registry_changes():
    service = PlatformCapabilityLookupService()

    numeric = service.lookup(
        PlatformCapabilityLookupRequest(
            domain="evaluation",
            capability_key="numeric_equivalence",
            subject="Mathematics",
        )
    )
    diagrams = service.lookup(
        PlatformCapabilityLookupRequest(
            domain="evaluation",
            capability_key="diagrams",
            subject="Mathematics",
        )
    )

    assert numeric.mode == "supported"
    assert diagrams.mode == "checklist"
    assert diagrams.declaration is not None
    assert diagrams.declaration.metadata["aei_mode"] == "partial"
