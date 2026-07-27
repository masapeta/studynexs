"""Read-only Educational Identity registry."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from app.modules.eui.schemas.educational_identity import EducationalIdentity


class EducationalIdentityRegistryError(LookupError):
    """Registry lookup failed."""


@dataclass(frozen=True)
class EducationalIdentityRegistry:
    """Read-only registry of identities and aliases.

    Think of this as a DNS-like map for canonical educational identities. It is
    built from existing curriculum structures in Phase 1 and does not persist
    anything.
    """

    version: str
    identities: tuple[EducationalIdentity, ...]
    _by_id: Mapping[str, EducationalIdentity]
    _aliases: Mapping[str, str]

    @classmethod
    def from_identities(
        cls,
        identities: list[EducationalIdentity],
        *,
        aliases: dict[str, str] | None = None,
        version: str = "eui-identity-registry-v1",
    ) -> "EducationalIdentityRegistry":
        by_id = {identity.id: identity for identity in identities}
        alias_map = dict(aliases or {})
        return cls(
            version=version,
            identities=tuple(identities),
            _by_id=MappingProxyType(by_id),
            _aliases=MappingProxyType(alias_map),
        )

    def get(self, identity_id: str) -> EducationalIdentity | None:
        return self._by_id.get(identity_id)

    def require(self, identity_id: str) -> EducationalIdentity:
        identity = self.get(identity_id)
        if identity is None:
            raise EducationalIdentityRegistryError(f"Educational identity not found: {identity_id}")
        return identity

    def resolve_alias(self, alias: str) -> EducationalIdentity | None:
        identity_id = self._aliases.get(alias)
        if identity_id is None:
            return None
        return self.get(identity_id)

    def aliases(self) -> dict[str, str]:
        return dict(self._aliases)
