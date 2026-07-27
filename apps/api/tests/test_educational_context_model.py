"""EUI Phase 1 Sprint 2 — EducationalContext domain model."""

from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.modules.eui.schemas.educational_context import (
    EducationalContext,
    EducationalContextConflict,
    EducationalContextProvenance,
    EducationalContextReference,
)
from app.modules.eui.schemas.educational_identity import (
    EducationalIdentity,
    EducationalIdentityProvenance,
)


def test_eui_context_feature_flag_defaults_off():
    assert Settings().EUI_CONTEXT_PASSIVE_ENABLED is False


def test_educational_context_is_strict_immutable_and_serializable():
    school_id = uuid.uuid4()
    context = EducationalContext(
        tenant_id=school_id,
        resolution_status="resolved_with_conflicts",
        board="CBSE",
        grade="Grade 6",
        subject="Science",
        field_sources={"grade": "educational_identity"},
        conflicts=(
            EducationalContextConflict(
                field="grade",
                chosen_source="educational_identity",
                rejected_source="runtime_metadata",
                chosen_value="Grade 6",
                rejected_value="Grade 7",
            ),
        ),
        provenance=EducationalContextProvenance(
            source="passive_context_resolver",
            resolved_from="educational_identity",
        ),
    )

    dumped = context.model_dump(mode="json")
    assert dumped["tenant_id"] == str(school_id)
    assert dumped["conflicts"][0]["field"] == "grade"

    with pytest.raises(ValidationError):
        context.subject = "Changed"  # type: ignore[misc]

    with pytest.raises(ValidationError):
        EducationalContext(
            tenant_id=school_id,
            resolution_status="resolved",
            provenance=EducationalContextProvenance(
                source="passive_context_resolver",
                resolved_from="educational_identity",
            ),
            unexpected=True,  # type: ignore[call-arg]
        )


def test_educational_context_reference_resolution_kind_priority():
    school_id = uuid.uuid4()
    identity = _identity(school_id)

    assert EducationalContextReference(school_id=school_id).resolution_kind == "metadata"
    assert (
        EducationalContextReference(
            school_id=school_id,
            candidate_context_ids=("ctx-a", "ctx-b"),
        ).resolution_kind
        == "candidate_context"
    )
    assert (
        EducationalContextReference(
            school_id=school_id,
            artifact_type="question_paper",
        ).resolution_kind
        == "artifact"
    )
    assert (
        EducationalContextReference(
            school_id=school_id,
            educational_identity=identity,
            artifact_type="question_paper",
        ).resolution_kind
        == "educational_identity"
    )


def _identity(school_id: uuid.UUID) -> EducationalIdentity:
    return EducationalIdentity(
        id="ei://cbse/ncf2023/2024/g6/science/ch05/topic-measuring-length",
        tenant_id=school_id,
        board="CBSE",
        curriculum="NCF2023",
        curriculum_version="2024",
        grade="Grade 6",
        subject="Science",
        chapter="Motion and Measurement of Distances",
        topic="Measuring Length",
        concepts=("Standard Units", "SI Units"),
        metadata={"pack_id": str(uuid.uuid4()), "entity_type": "topic"},
        provenance=EducationalIdentityProvenance(
            source="curriculum_pack",
            source_id="topic-1",
            source_version="2024",
            resolved_from="topic",
        ),
    )
