"""Read-only Platform Capability Registry for EUI Phase 1 Sprint 3."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from pydantic import ValidationError

from app.modules.eui.schemas.platform_capability import (
    CAPABILITY_MODE_CLAIM_RANK,
    PlatformCapabilityDeclaration,
    PlatformCapabilityLookupRequest,
    PlatformCapabilityLookupResult,
    PlatformCapabilityRegistryPayload,
)

DEFAULT_PLATFORM_CAPABILITY_REGISTRY_VERSION = "v1"
DEFAULT_PLATFORM_CAPABILITY_REGISTRY_PATH = (
    Path(__file__).resolve().parents[1]
    / "registry"
    / f"platform_capability_registry.{DEFAULT_PLATFORM_CAPABILITY_REGISTRY_VERSION}.json"
)


class PlatformCapabilityRegistryError(ValueError):
    """Raised when the Platform Capability Registry is malformed."""


@dataclass(frozen=True)
class PlatformCapabilityRegistry:
    """Static, read-only registry of internal platform capability posture."""

    payload: PlatformCapabilityRegistryPayload
    _by_id: Mapping[str, PlatformCapabilityDeclaration]

    @classmethod
    def load_default(cls) -> "PlatformCapabilityRegistry":
        return cls.load_from_path(DEFAULT_PLATFORM_CAPABILITY_REGISTRY_PATH)

    @classmethod
    def load_from_path(cls, path: Path) -> "PlatformCapabilityRegistry":
        try:
            with path.open("r", encoding="utf-8") as handle:
                raw_payload = json.load(handle)
            payload = PlatformCapabilityRegistryPayload.model_validate(raw_payload)
        except ValidationError as exc:
            raise PlatformCapabilityRegistryError(
                "Platform Capability Registry validation failed"
            ) from exc
        except json.JSONDecodeError as exc:
            raise PlatformCapabilityRegistryError(
                "Platform Capability Registry JSON is malformed"
            ) from exc
        return cls.from_payload(payload)

    @classmethod
    def from_payload(
        cls,
        payload: PlatformCapabilityRegistryPayload,
    ) -> "PlatformCapabilityRegistry":
        registry = cls(
            payload=payload,
            _by_id=MappingProxyType({entry.id: entry for entry in payload.declarations}),
        )
        registry._validate_unique_ids()
        return registry

    @property
    def version(self) -> str:
        return self.payload.version

    @property
    def authorization(self) -> str:
        return self.payload.authorization

    def declarations(self) -> tuple[PlatformCapabilityDeclaration, ...]:
        return self.payload.declarations

    def get(self, declaration_id: str) -> PlatformCapabilityDeclaration | None:
        return self._by_id.get(declaration_id)

    def require(self, declaration_id: str) -> PlatformCapabilityDeclaration:
        declaration = self.get(declaration_id)
        if declaration is None:
            raise PlatformCapabilityRegistryError(
                f"Platform capability declaration not found: {declaration_id}"
            )
        return declaration

    def lookup(self, request: PlatformCapabilityLookupRequest) -> PlatformCapabilityLookupResult:
        matches = [
            declaration
            for declaration in self.payload.declarations
            if _matches(declaration, request)
        ]
        if not matches:
            return PlatformCapabilityLookupResult(
                registry_version=self.version,
                request=request,
                mode="unsupported",
                matched=False,
                authoritative=False,
                fallback_reason="missing_capability",
                metadata={"authorization": self.authorization, "passive": True},
            )

        max_specificity = max(entry.scope.specificity() for entry in matches)
        candidates = tuple(
            entry for entry in matches if entry.scope.specificity() == max_specificity
        )
        chosen = min(candidates, key=lambda entry: CAPABILITY_MODE_CLAIM_RANK[entry.mode])
        conflict = len({entry.mode for entry in candidates}) > 1
        return PlatformCapabilityLookupResult(
            registry_version=self.version,
            request=request,
            mode=chosen.mode,
            matched=True,
            authoritative=not conflict,
            declaration=chosen,
            candidate_ids=tuple(entry.id for entry in candidates),
            conflict=conflict,
            fallback_reason="conflicting_capability_entries" if conflict else None,
            metadata={
                "authorization": self.authorization,
                "passive": True,
                "candidate_count": len(candidates),
                "specificity": max_specificity,
            },
        )

    def _validate_unique_ids(self) -> None:
        ids = [entry.id for entry in self.payload.declarations]
        if len(ids) != len(set(ids)):
            raise PlatformCapabilityRegistryError(
                "Platform Capability Registry declaration IDs must be unique"
            )


def normalize_capability_value(value: str | None) -> str:
    """Normalize registry values for deterministic matching."""

    if value is None:
        return ""
    normalized = value.strip().casefold()
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized)
    return normalized.strip("_")


def _matches(
    declaration: PlatformCapabilityDeclaration,
    request: PlatformCapabilityLookupRequest,
) -> bool:
    if normalize_capability_value(declaration.domain) != normalize_capability_value(
        request.domain
    ):
        return False
    if normalize_capability_value(declaration.capability_key) != normalize_capability_value(
        request.capability_key
    ):
        return False

    request_scope = request.model_dump(exclude={"domain", "capability_key", "metadata"})
    for field, declared_value in declaration.scope.model_dump().items():
        if declared_value is None or declared_value == "":
            continue
        if normalize_capability_value(str(declared_value)) != normalize_capability_value(
            _string_or_none(request_scope.get(field))
        ):
            return False
    return True


def _string_or_none(value: object) -> str | None:
    if value is None:
        return None
    return str(value)
