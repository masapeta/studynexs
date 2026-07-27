"""Read-only Platform Capability Registry lookup service."""

from __future__ import annotations

from app.modules.eui.schemas.educational_context import EducationalContext
from app.modules.eui.schemas.platform_capability import (
    PlatformCapabilityLookupRequest,
    PlatformCapabilityLookupResult,
)
from app.modules.eui.services.platform_capability_registry import PlatformCapabilityRegistry


class PlatformCapabilityLookupService:
    """Deterministic lookup facade over the read-only registry."""

    def __init__(self, registry: PlatformCapabilityRegistry | None = None) -> None:
        self.registry = registry or PlatformCapabilityRegistry.load_default()

    def lookup(self, request: PlatformCapabilityLookupRequest) -> PlatformCapabilityLookupResult:
        return self.registry.lookup(request)

    def lookup_for_context(
        self,
        *,
        context: EducationalContext,
        domain: str,
        capability_key: str,
        language: str | None = None,
        script: str | None = None,
        input_type: str | None = None,
        artifact_type: str | None = None,
    ) -> PlatformCapabilityLookupResult:
        """Resolve a capability using Educational Context-like fields.

        This does not migrate Educational Context consumers. It is a passive
        helper for Sprint 3 tests and future explicitly authorized integrations.
        """

        return self.lookup(
            PlatformCapabilityLookupRequest(
                domain=domain,
                capability_key=capability_key,
                board=context.board,
                curriculum=context.curriculum,
                curriculum_version=context.curriculum_version,
                grade=context.grade,
                subject=context.subject,
                language=language or context.language_medium,
                script=script,
                input_type=input_type,
                artifact_type=artifact_type,
                assessment_mode=context.assessment_mode,
                metadata={
                    "source": "educational_context",
                    "context_status": context.resolution_status,
                },
            )
        )
