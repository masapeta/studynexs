"""EUI Phase 1 Sprint 3 — Platform Capability Registry contracts."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.modules.eui.schemas.platform_capability import (
    PlatformCapabilityDeclaration,
    PlatformCapabilityRegistryPayload,
    PlatformCapabilityScope,
)
from app.modules.eui.services.platform_capability_registry import (
    PlatformCapabilityRegistry,
    PlatformCapabilityRegistryError,
    normalize_capability_value,
)


def test_platform_capability_registry_loads_default_data():
    registry = PlatformCapabilityRegistry.load_default()

    assert registry.version == "eui-platform-capability-registry-v1"
    assert registry.authorization == "EUI-PH1-SP3-AUTH-001"
    assert registry.require("pc://eui/mathematics/numeric_normalization/cbse/ncf2023/g10")
    assert isinstance(registry.declarations(), tuple)


def test_platform_capability_registry_rejects_invalid_mode():
    with pytest.raises(ValidationError):
        PlatformCapabilityDeclaration.model_validate(
            {
                "id": "pc://eui/bad/mode",
                "domain": "mathematics",
                "capability_key": "numeric_normalization",
                "mode": "magic",
                "scope": {},
                "review_required": False,
            }
        )


def test_platform_capability_registry_rejects_duplicate_ids():
    declaration = PlatformCapabilityDeclaration(
        id="pc://eui/test/duplicate",
        domain="test",
        capability_key="duplicate",
        mode="supported",
        scope=PlatformCapabilityScope(),
        review_required=False,
    )
    payload = PlatformCapabilityRegistryPayload(
        version="duplicate-test",
        authorization="EUI-PH1-SP3-AUTH-001",
        declarations=(declaration, declaration),
    )

    with pytest.raises(PlatformCapabilityRegistryError, match="unique"):
        PlatformCapabilityRegistry.from_payload(payload)


def test_platform_capability_registry_unknown_id_requires_explicit_failure():
    registry = PlatformCapabilityRegistry.load_default()

    with pytest.raises(PlatformCapabilityRegistryError, match="not found"):
        registry.require("pc://eui/missing")


def test_normalize_capability_value_is_deterministic():
    assert normalize_capability_value(" Numeric Normalization ") == "numeric_normalization"
    assert normalize_capability_value("NCF-2023") == "ncf_2023"
    assert normalize_capability_value(None) == ""
