import pytest
from pydantic import ValidationError

from app.modules.examinations.schemas.academic_reasoning_result import (
    AcademicReasoningResult,
    ReasonerTraceEntry,
)


def test_reasoning_result_is_assignment_protected():
    result = AcademicReasoningResult(
        reasoning_type="numeric_equivalence",
        result="equivalent",
        interpreted_value="5.5",
    )

    with pytest.raises(ValidationError):
        result.result = "not_equivalent"

    assert result.result == "equivalent"


def test_reasoning_result_nested_maps_are_read_only():
    result = AcademicReasoningResult(
        reasoning_type="numeric_equivalence",
        result="equivalent",
        evidence={"parsed_answer": "5.5"},
        metadata={"source": "test"},
    )

    with pytest.raises(TypeError):
        result.evidence["parsed_answer"] = "6"

    with pytest.raises(TypeError):
        result.metadata["source"] = "mutated"

    assert result.evidence["parsed_answer"] == "5.5"
    assert result.metadata["source"] == "test"


def test_reasoning_result_rejects_unknown_top_level_fields():
    with pytest.raises(ValidationError):
        AcademicReasoningResult(
            reasoning_type="numeric_equivalence",
            result="equivalent",
            marks=1,
        )


def test_reasoning_result_serializes_trace_stably():
    original = AcademicReasoningResult(
        reasoning_type="numeric_equivalence",
        result="equivalent",
        reasoner_trace=(
            ReasonerTraceEntry(
                reasoner="numeric_equivalence",
                status="executed",
                supported=True,
                result="equivalent",
                metadata={"reasoning_type": "numeric_equivalence"},
            ),
        ),
    )

    restored = AcademicReasoningResult.model_validate_json(original.model_dump_json())

    assert restored == original
    assert restored.reasoner_trace[0].status == "executed"
    assert restored.reasoner_trace[0].result == "equivalent"
    assert restored.reasoner_trace[0].metadata["reasoning_type"] == "numeric_equivalence"


def test_reasoner_trace_entry_rejects_invalid_status():
    with pytest.raises(ValidationError):
        ReasonerTraceEntry(reasoner="x", status="available", supported=True)
