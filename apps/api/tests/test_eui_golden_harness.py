"""EUI Golden Harness — Educational Identity deterministic ID cases."""

from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest

from app.modules.eui.schemas.educational_context import EducationalContextReference
from app.modules.eui.schemas.educational_identity import (
    EducationalIdentity,
    EducationalIdentityProvenance,
)
from app.modules.eui.schemas.platform_capability import PlatformCapabilityLookupRequest
from app.modules.eui.services.educational_context_resolver import EducationalContextResolver
from app.modules.eui.services.educational_identity_id import stable_identity_id
from app.modules.eui.services.platform_capability_lookup import PlatformCapabilityLookupService

GOLDEN_DIR = Path(__file__).parent / "golden" / "eui_v1"


def test_eui_identity_golden_harness_cases_are_deterministic_and_unique():
    payload = json.loads((GOLDEN_DIR / "educational_identity_cases.json").read_text())

    assert payload["version"] == "eui-identity-golden-v1"
    assert payload["authorization"] == "EUI-PH1-AUTH-001"
    case_ids = [case["id"] for case in payload["cases"]]
    assert len(case_ids) == len(set(case_ids))

    expected_ids: set[str] = set()
    for case in payload["cases"]:
        actual = stable_identity_id(**case["input"])
        assert actual == case["expected_id"], case["id"]
        expected_ids.add(case["expected_id"])

    assert len(expected_ids) == len(payload["cases"])


@pytest.mark.asyncio
async def test_eui_context_golden_harness_cases_are_deterministic():
    payload = json.loads((GOLDEN_DIR / "educational_context_cases.json").read_text())

    assert payload["version"] == "eui-context-golden-v1"
    assert payload["authorization"] == "EUI-PH1-SP2-AUTH-001"
    case_ids = [case["id"] for case in payload["cases"]]
    assert len(case_ids) == len(set(case_ids))

    resolver = EducationalContextResolver()
    for case in payload["cases"]:
        school_id = uuid.UUID(case["school_id"])
        identity = _identity_from_case(school_id, case.get("identity"))
        reference = EducationalContextReference(
            school_id=school_id,
            educational_identity=identity,
            **case.get("reference", {}),
        )
        context = await resolver.resolve(reference)
        expected = case["expected"]

        assert context.resolution_status == expected["resolution_status"], case["id"]
        assert len(context.conflicts) == expected["conflict_count"], case["id"]
        assert len(context.ambiguities) == expected["ambiguity_count"], case["id"]
        for field in (
            "grade",
            "subject",
            "assessment_mode",
            "language_medium",
            "evidence_posture",
        ):
            if field in expected:
                assert getattr(context, field) == expected[field], case["id"]


def test_eui_platform_capability_golden_harness_cases_are_deterministic():
    payload = json.loads((GOLDEN_DIR / "platform_capability_registry_cases.json").read_text())

    assert payload["version"] == "eui-platform-capability-golden-v1"
    assert payload["authorization"] == "EUI-PH1-SP3-AUTH-001"
    case_ids = [case["id"] for case in payload["cases"]]
    assert len(case_ids) == len(set(case_ids))

    service = PlatformCapabilityLookupService()
    for case in payload["cases"]:
        result = service.lookup(PlatformCapabilityLookupRequest(**case["request"]))
        expected = case["expected"]

        assert result.mode == expected["mode"], case["id"]
        assert result.matched is expected["matched"], case["id"]
        assert result.conflict is expected["conflict"], case["id"]


def _identity_from_case(
    school_id: uuid.UUID,
    payload: dict | None,
) -> EducationalIdentity | None:
    if payload is None:
        return None
    return EducationalIdentity(
        id=payload["id"],
        tenant_id=school_id,
        board=payload["board"],
        curriculum=payload["curriculum"],
        curriculum_version=payload["curriculum_version"],
        grade=payload["grade"],
        subject=payload["subject"],
        chapter=payload.get("chapter"),
        topic=payload.get("topic"),
        concepts=tuple(payload.get("concepts", ())),
        competencies=tuple(payload.get("competencies", ())),
        learning_objectives=tuple(payload.get("learning_objectives", ())),
        language=payload.get("language"),
        metadata=payload.get("metadata", {}),
        provenance=EducationalIdentityProvenance(
            source="golden_harness",
            source_id=payload["id"],
            source_version=payload["curriculum_version"],
            resolved_from="golden_case",
        ),
    )
