import pytest
from pydantic import ValidationError

from app.modules.examinations.schemas.academic_answer import AcademicAnswer


def test_academic_answer_preserves_raw_input_without_normalizing():
    answer = AcademicAnswer(raw_input="  5½  ", subject="mathematics", question_type="short")

    assert answer.raw_input == "  5½  "
    assert answer.normalized_input is None
    assert answer.subject == "mathematics"
    assert answer.question_type == "short"


def test_academic_answer_raw_input_is_assignment_protected():
    answer = AcademicAnswer(raw_input="original")

    with pytest.raises(ValidationError):
        answer.raw_input = "mutated"

    assert answer.raw_input == "original"


def test_academic_answer_defaults_are_safe_and_independent():
    first = AcademicAnswer(raw_input="A")
    second = AcademicAnswer(raw_input="B")

    first.metadata["source"] = "vision"

    assert first.code_mixed is False
    assert second.metadata == {}


def test_academic_answer_accepts_future_provider_metadata():
    answer = AcademicAnswer(
        raw_input="[answer-sheet image region]",
        subject="biology",
        question_type="diagram",
        detected_language="en",
        detected_script="latin",
        visual_type="biology_diagram",
        confidence=0.72,
        confidence_reason="Diagram region detected with partial label confidence",
        metadata={
            "provider": "visual",
            "checklist": ["nucleus", "cell wall"],
            "source": "answer_sheet_image",
        },
    )

    assert answer.visual_type == "biology_diagram"
    assert answer.confidence == 0.72
    assert answer.metadata["provider"] == "visual"


def test_academic_answer_serializes_and_deserializes_stably():
    original = AcademicAnswer(
        raw_input="factorisation kaise karna?",
        normalized_input=None,
        subject="mathematics",
        question_type="tutor_prompt",
        detected_language="hi-en",
        detected_script="latin",
        code_mixed=True,
        metadata={"mode": "hinglish"},
    )

    restored = AcademicAnswer.model_validate_json(original.model_dump_json())

    assert restored == original
    assert restored.code_mixed is True
    assert restored.metadata == {"mode": "hinglish"}


def test_academic_answer_confidence_must_be_between_zero_and_one():
    with pytest.raises(ValidationError):
        AcademicAnswer(raw_input="answer", confidence=1.5)

    with pytest.raises(ValidationError):
        AcademicAnswer(raw_input="answer", confidence=-0.1)


def test_academic_answer_rejects_unknown_top_level_fields():
    with pytest.raises(ValidationError):
        AcademicAnswer(raw_input="answer", marks_suggested=1)
