import pytest

from app.modules.examinations.services.subject_capability_registry import (
    SubjectCapabilityRegistry,
    SubjectCapabilityRegistryError,
    normalize_registry_key,
)


def test_default_subject_capability_registry_loads():
    registry = SubjectCapabilityRegistry.load_default()

    assert registry.version == "aei-subject-capabilities-v1"
    assert "mathematics" in registry.subjects()
    assert "hindi" in registry.subjects()
    assert "telugu" in registry.subjects()
    assert "sanskrit" in registry.subjects()


def test_registry_resolves_supported_math_capability():
    registry = SubjectCapabilityRegistry.load_default()

    capability = registry.resolve("Mathematics", "numeric equivalence")

    assert capability.subject == "mathematics"
    assert capability.capability == "numeric_equivalence"
    assert capability.mode == "supported"
    assert capability.teacher_review_required is False
    assert capability.supported_for_final_suggestion is True


def test_registry_resolves_assist_and_checklist_modes_as_teacher_review_required():
    registry = SubjectCapabilityRegistry.load_default()

    chemistry = registry.resolve("Chemistry", "reaction balancing")
    biology = registry.resolve("Biology", "diagrams")
    hindi = registry.resolve("Hindi", "handwriting OCR")

    assert chemistry.mode == "assist"
    assert biology.mode == "checklist"
    assert hindi.mode == "assist"
    assert chemistry.teacher_review_required is True
    assert biology.teacher_review_required is True
    assert hindi.teacher_review_required is True


def test_registry_unknown_capability_fails_closed_to_unsupported_review():
    registry = SubjectCapabilityRegistry.load_default()

    capability = registry.resolve("Commerce", "ledger balancing")

    assert capability.mode == "unsupported"
    assert capability.teacher_review_required is True
    assert capability.supported_for_final_suggestion is False


def test_registry_lists_subject_capabilities():
    registry = SubjectCapabilityRegistry.load_default()

    capabilities = registry.capabilities_for("Physics")

    assert set(capabilities) >= {"units", "formula_recognition", "diagrams", "graphs"}


def test_registry_rejects_invalid_mode():
    with pytest.raises(SubjectCapabilityRegistryError, match="invalid mode"):
        SubjectCapabilityRegistry(
            {
                "version": "bad",
                "subjects": {
                    "mathematics": {
                        "evaluation": {
                            "numeric_equivalence": {"mode": "magic"}
                        }
                    }
                },
            }
        )


def test_normalize_registry_key():
    assert normalize_registry_key("Handwriting OCR") == "handwriting_ocr"
    assert normalize_registry_key("Numeric-Equivalence") == "numeric_equivalence"
    assert normalize_registry_key("  Scientific notation  ") == "scientific_notation"
