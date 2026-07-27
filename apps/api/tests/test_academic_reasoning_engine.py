from app.modules.examinations.schemas.academic_answer import AcademicAnswer
from app.modules.examinations.services.academic_reasoning_engine import (
    AcademicReasoningEngine,
    ChemicalEquationReasoner,
    NumericEquivalenceReasoner,
    ScientificNotationReasoner,
    UnitInterpretationReasoner,
    VisualChecklistReasoner,
    default_reasoners,
)
from app.modules.examinations.services.academic_understanding_engine import (
    AcademicUnderstandingEngine,
)


def _understood_answer(
    raw_input: str,
    *,
    subject: str = "mathematics",
    question_type: str = "short",
    reasoning_context: dict | None = None,
) -> AcademicAnswer:
    answer = AcademicAnswer(
        raw_input=raw_input,
        subject=subject,
        question_type=question_type,
        metadata={"reasoning_context": reasoning_context or {}},
    )
    return AcademicUnderstandingEngine().understand(answer)


def test_default_reasoner_order_is_stable():
    reasoners = default_reasoners()

    assert [reasoner.name for reasoner in reasoners] == [
        "unit_interpretation",
        "scientific_notation",
        "numeric_equivalence",
        "chemical_equation",
        "visual_checklist",
    ]
    assert isinstance(reasoners[0], UnitInterpretationReasoner)
    assert isinstance(reasoners[1], ScientificNotationReasoner)
    assert isinstance(reasoners[2], NumericEquivalenceReasoner)
    assert isinstance(reasoners[3], ChemicalEquationReasoner)
    assert isinstance(reasoners[4], VisualChecklistReasoner)


def test_reasoning_engine_returns_not_applicable_when_no_reasoner_supports():
    answer = AcademicAnswer(raw_input="plain text answer", subject="english")

    result = AcademicReasoningEngine().reason(answer)

    assert result.result == "not_applicable"
    assert result.reasoning_type == "none"
    assert all(entry.status == "skipped" for entry in result.reasoner_trace)


def test_numeric_equivalence_reasoner_matches_fraction_decimal_and_mixed_number():
    answer = _understood_answer(
        "5\u00bd",
        reasoning_context={
            "answer_key": "5.5",
            "acceptable_answers": ["11/2", "5\u00bd"],
        },
    )

    result = AcademicReasoningEngine().reason(answer)

    assert result.reasoning_type == "numeric_equivalence"
    assert result.result == "equivalent"
    assert result.interpreted_value == "5.5"
    assert result.matched_value == "5.5"
    assert result.evidence["candidate_values"] == ["5.5", "5.5", "5.5"]


def test_numeric_equivalence_reasoner_reports_not_equivalent_without_scoring():
    answer = _understood_answer(
        "5",
        reasoning_context={"answer_key": "4"},
    )

    result = AcademicReasoningEngine().reason(answer)

    assert result.reasoning_type == "numeric_equivalence"
    assert result.result == "not_equivalent"
    assert "marks" not in result.model_dump()


def test_numeric_equivalence_reasoner_matches_percent_and_tolerance():
    answer = _understood_answer(
        "50%",
        reasoning_context={"answer_key": "0.5", "numeric_tolerance": "0"},
    )

    result = AcademicReasoningEngine().reason(answer)

    assert result.reasoning_type == "numeric_equivalence"
    assert result.result == "equivalent"
    assert result.interpreted_value == "0.5"


def test_scientific_notation_reasoner_matches_equivalent_value():
    answer = _understood_answer(
        "1.2 x 10^3",
        reasoning_context={"answer_key": "1200"},
    )

    result = AcademicReasoningEngine().reason(answer)

    assert result.reasoning_type == "scientific_notation"
    assert result.result == "equivalent"
    assert result.interpreted_value == "1.2E+3"


def test_unit_interpretation_reasoner_matches_value_and_unit():
    answer = _understood_answer(
        "12 cm",
        reasoning_context={
            "answer_key": "12 cm",
            "units": {"required": True, "allowed": ["cm"]},
        },
    )

    result = AcademicReasoningEngine().reason(answer)

    assert result.reasoning_type == "unit_interpretation"
    assert result.result == "matched"
    assert result.interpreted_value == "12 cm"
    assert result.matched_value == "12 cm"


def test_unit_interpretation_reasoner_matches_equivalent_supported_units():
    answer = _understood_answer(
        "1 m",
        reasoning_context={"answer_key": "100 cm"},
    )

    result = AcademicReasoningEngine().reason(answer)

    assert result.reasoning_type == "unit_interpretation"
    assert result.result == "matched"
    assert result.matched_value == "100 cm"


def test_unit_interpretation_reasoner_reports_unit_mismatch():
    answer = _understood_answer(
        "12 m",
        reasoning_context={
            "answer_key": "12 cm",
            "units": {"required": True, "allowed": ["cm"]},
        },
    )

    result = AcademicReasoningEngine().reason(answer)

    assert result.reasoning_type == "unit_interpretation"
    assert result.result == "not_matched"
    assert "not in the allowed unit set" in (result.explanation or "")


def test_chemical_equation_reasoner_interprets_unbalanced_equation():
    answer = _understood_answer("H2 + O2 -> H2O", subject="chemistry")

    result = AcademicReasoningEngine().reason(answer)

    assert result.reasoning_type == "reaction_balancing"
    assert result.result == "unbalanced"
    assert result.evidence["left_counts"] == {"H": 2, "O": 2}
    assert result.evidence["right_counts"] == {"H": 2, "O": 1}


def test_chemical_equation_reasoner_interprets_balanced_equation():
    answer = _understood_answer("2H2 + O2 -> 2H2O", subject="chemistry")

    result = AcademicReasoningEngine().reason(answer)

    assert result.reasoning_type == "reaction_balancing"
    assert result.result == "balanced"


def test_visual_checklist_reasoner_interprets_present_and_missing_items():
    answer = _understood_answer(
        "[answer-sheet image region]",
        subject="biology",
        question_type="diagram",
        reasoning_context={
            "checklist": ["cell wall", "nucleus", "cytoplasm"],
            "visual_observations": ["nucleus", "cell wall"],
        },
    )

    result = AcademicReasoningEngine().reason(answer)

    assert result.reasoning_type == "visual_checklist"
    assert result.result == "checklist"
    assert result.evidence["present"] == ["cell wall", "nucleus"]
    assert result.evidence["missing"] == ["cytoplasm"]


def test_reasoning_engine_trace_records_executed_and_skipped_reasoners():
    answer = _understood_answer("5\u00bd", reasoning_context={"answer_key": "5.5"})

    result = AcademicReasoningEngine().reason(answer)

    trace = [entry.model_dump() for entry in result.reasoner_trace]
    assert {
        "reasoner": "numeric_equivalence",
        "status": "executed",
        "supported": True,
        "result": "equivalent",
        "metadata": {
            "reasoning_type": "numeric_equivalence",
            "capability": "numeric_equivalence",
        },
    } in trace
    assert {
        "reasoner": "visual_checklist",
        "status": "skipped",
        "supported": False,
        "result": None,
        "metadata": {},
    } in trace
