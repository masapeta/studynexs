import uuid

import pytest
from pydantic import ValidationError

from app.modules.mastery.schemas.mastery_spine import (
    MasterySpineProvenance,
    MasterySpineReference,
    MasterySpineResolutionReference,
)


def test_mastery_spine_reference_is_strict_and_immutable():
    ref = MasterySpineReference(
        tenant_id=uuid.uuid4(),
        school_id=uuid.uuid4(),
        spine_level="label",
        label="Linear Equations",
        resolution_status="legacy_fallback",
        authority_posture="legacy",
        provenance=MasterySpineProvenance(
            source="test",
            resolved_from="legacy_free_text_topic",
            precedence=6,
        ),
    )

    assert ref.label == "Linear Equations"
    with pytest.raises(ValidationError):
        MasterySpineReference(
            tenant_id=uuid.uuid4(),
            school_id=uuid.uuid4(),
            spine_level="label",
            label="Linear Equations",
            resolution_status="legacy_fallback",
            authority_posture="legacy",
            provenance=MasterySpineProvenance(
                source="test",
                resolved_from="legacy_free_text_topic",
                precedence=6,
            ),
            unexpected=True,
        )
    with pytest.raises(ValidationError):
        ref.label = "Changed"  # type: ignore[misc]


def test_mastery_spine_resolution_reference_rejects_tenant_mismatch():
    school_id = uuid.uuid4()

    with pytest.raises(ValidationError, match="tenant_id must match school_id"):
        MasterySpineResolutionReference(
            school_id=school_id,
            tenant_id=uuid.uuid4(),
        )
