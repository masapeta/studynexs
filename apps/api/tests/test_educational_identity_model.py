"""EUI Phase 1 Sprint 1 — EducationalIdentity domain model and IDs."""

from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from app.modules.eui.schemas.educational_identity import (
    EducationalIdentity,
    EducationalIdentityProvenance,
    EducationalIdentityReference,
)
from app.modules.eui.services.educational_identity_id import (
    identity_alias,
    stable_identity_id,
)


def test_stable_identity_id_is_deterministic_and_name_normalized():
    identity_id = stable_identity_id(
        board="CBSE",
        curriculum="NCF2023",
        curriculum_version="2024",
        grade="Grade 6",
        subject="Science",
        chapter_number="5",
        chapter="Motion and Measurement of Distances",
        topic="Measuring Length",
        concept="SI Units",
    )

    assert (
        identity_id
        == "ei://cbse/ncf2023/2024/g6/science/ch05/topic-measuring-length/concept-si-units"
    )
    assert identity_id == stable_identity_id(
        board=" cbse ",
        curriculum="NCF2023",
        curriculum_version="2024",
        grade="Class 6",
        subject="Science",
        chapter_number="05",
        topic="Measuring   Length",
        concept="SI Units!",
    )


def test_identity_alias_is_stable_for_lookup_keys():
    assert identity_alias("Chapter", "Motion and Measurement!") == "chapter:motion-and-measurement"


def test_educational_identity_is_strict_immutable_and_serializable():
    identity = EducationalIdentity(
        id="ei://cbse/ncf2023/2024/g6/science/ch05",
        tenant_id=uuid.uuid4(),
        board="CBSE",
        curriculum="NCF2023",
        curriculum_version="2024",
        grade="Grade 6",
        subject="Science",
        chapter="Motion and Measurement of Distances",
        concepts=("SI Units",),
        provenance=EducationalIdentityProvenance(
            source="curriculum_pack",
            source_id="pack-1",
            source_version="2024",
            resolved_from="chapter",
        ),
    )

    dumped = identity.model_dump(mode="json")
    assert dumped["id"] == "ei://cbse/ncf2023/2024/g6/science/ch05"
    assert dumped["tenant_id"]

    with pytest.raises(ValidationError):
        identity.subject = "Changed"  # type: ignore[misc]

    with pytest.raises(ValidationError):
        EducationalIdentity(
            id="not-an-ei-id",
            tenant_id=uuid.uuid4(),
            board="CBSE",
            curriculum="NCF2023",
            curriculum_version="2024",
            grade="Grade 6",
            subject="Science",
            provenance=EducationalIdentityProvenance(
                source="curriculum_pack",
                resolved_from="pack",
            ),
        )


def test_educational_identity_reference_resolution_kind_priority():
    school_id = uuid.uuid4()

    assert EducationalIdentityReference(school_id=school_id).resolution_kind == "empty"
    assert (
        EducationalIdentityReference(school_id=school_id, raw_label="Motion").resolution_kind
        == "label"
    )
    assert (
        EducationalIdentityReference(
            school_id=school_id,
            raw_label="Motion",
            chapter_id=uuid.uuid4(),
        ).resolution_kind
        == "chapter"
    )
