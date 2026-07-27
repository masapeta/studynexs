from app.modules.examinations.services.aei_v1_math_normalization import (
    AEI_MATH_EVALUATION_METHOD,
    evaluate_math_normalization,
)


def test_math_normalization_matches_fraction_decimal_and_percent_variants():
    result = evaluate_math_normalization(
        subject="Maths",
        q_type="short",
        student_answer="1/2",
        answer_key="0.5",
        max_marks=2,
        rubric={"acceptable_answers": ["50%", "½"]},
    )

    assert result is not None
    assert result.marks == 2
    assert result.method == AEI_MATH_EVALUATION_METHOD
    assert result.metadata["normalized_answer"] == "0.5"
    assert result.metadata["manual_review_required"] is False


def test_math_normalization_applies_explicit_numeric_tolerance():
    result = evaluate_math_normalization(
        subject="Mathematics",
        q_type="short",
        student_answer="9.81",
        answer_key="9.8",
        max_marks=1,
        rubric={"numeric_tolerance": "0.02"},
    )

    assert result is not None
    assert result.marks == 1
    assert result.metadata["matched_acceptable_answer"] == "9.8"


def test_math_normalization_matches_simple_unit_equivalence():
    result = evaluate_math_normalization(
        subject="Maths",
        q_type="short",
        student_answer="1 m",
        answer_key="100 cm",
        max_marks=1,
        rubric={},
    )

    assert result is not None
    assert result.marks == 1
    assert result.metadata["normalized_answer"] == "1 m"
    assert result.metadata["matched_acceptable_answer"] == "100 cm"


def test_math_normalization_routes_missing_required_unit_to_manual_review_metadata():
    result = evaluate_math_normalization(
        subject="Maths",
        q_type="short",
        student_answer="5",
        answer_key="5 m",
        max_marks=1,
        rubric={},
    )

    assert result is not None
    assert result.marks == 0
    assert result.metadata["manual_review_required"] is True
    assert result.metadata["manual_review_reason"]


def test_math_normalization_routes_blank_math_answer_to_manual_review_metadata():
    result = evaluate_math_normalization(
        subject="Maths",
        q_type="short",
        student_answer=" ",
        answer_key="0.5",
        max_marks=1,
        rubric={},
    )

    assert result is not None
    assert result.marks == 0
    assert result.metadata["manual_review_required"] is True
    assert "Teacher review required" in result.feedback


def test_math_normalization_ignores_non_math_subjects():
    result = evaluate_math_normalization(
        subject="English",
        q_type="short",
        student_answer="Delhi",
        answer_key="Delhi",
        max_marks=1,
        rubric={},
    )

    assert result is None


def test_math_normalization_ignores_textual_math_short_answers():
    result = evaluate_math_normalization(
        subject="Maths",
        q_type="short",
        student_answer="commutative property",
        answer_key="commutative property",
        max_marks=1,
        rubric={},
    )

    assert result is None


def test_math_normalization_ignores_mcq_answers():
    result = evaluate_math_normalization(
        subject="Maths",
        q_type="mcq",
        student_answer="B",
        answer_key="B",
        max_marks=1,
        rubric={"options": ["A", "B", "C"]},
    )

    assert result is None
