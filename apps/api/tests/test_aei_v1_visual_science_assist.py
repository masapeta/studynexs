from app.core.config import Settings
from app.modules.examinations.services.aei_v1_visual_science_assist import (
    apply_visual_science_assist_metadata,
    visual_science_manual_review_required,
)


def test_visual_science_assist_feature_flag_defaults_off():
    assert Settings().AEI_V1_VISUAL_SCIENCE_ASSIST_ENABLED is False


def test_chemistry_reaction_balancing_is_assistive_and_review_required():
    enriched = apply_visual_science_assist_metadata(
        {
            "1": {
                "marks_suggested": 0,
                "max_marks": 2,
                "student_answer": "H2 + O2 -> H2O",
                "confidence": 0.85,
                "method": "objective",
            }
        },
        subject="Chemistry",
        question_contexts={
            "1": {
                "question_type": "short",
                "answer_key": "2H2 + O2 -> 2H2O",
                "rubric": {},
            }
        },
    )

    q1 = enriched["1"]
    assist = q1["aei_v1_visual_science_assist"]
    assert q1["visual_science_capability_mode"] == "assist"
    assert q1["visual_science_reasoning_type"] == "reaction_balancing"
    assert q1["manual_review_required"] is True
    assert q1["assist_only"] is True
    assert q1["checklist_only"] is False
    assert assist["evidence_summary"]["chemical_balance_status"] == "unbalanced"
    assert assist["autonomous_science_grading"] is False
    assert visual_science_manual_review_required(q1) is True


def test_balanced_chemistry_reaction_still_requires_teacher_review():
    enriched = apply_visual_science_assist_metadata(
        {
            "1": {
                "marks_suggested": 2,
                "max_marks": 2,
                "student_answer": "2H2 + O2 -> 2H2O",
                "confidence": 0.9,
                "method": "objective",
            }
        },
        subject="Chemistry",
        question_contexts={"1": {"question_type": "short", "rubric": {}}},
    )

    assist = enriched["1"]["aei_v1_visual_science_assist"]
    assert assist["reasoning_result"] == "balanced"
    assert enriched["1"]["manual_review_required"] is True
    assert assist["autonomous_science_grading"] is False


def test_biology_diagram_checklist_is_checklist_only():
    enriched = apply_visual_science_assist_metadata(
        {
            "1": {
                "marks_suggested": 2,
                "max_marks": 3,
                "student_answer": "cell wall and nucleus labelled",
                "confidence": 0.7,
                "method": "heuristic_fallback",
            }
        },
        subject="Biology",
        question_contexts={
            "1": {
                "question_type": "diagram",
                "checklist": ["cell wall", "nucleus", "cytoplasm"],
                "rubric": {"checklist": ["cell wall", "nucleus", "cytoplasm"]},
            }
        },
    )

    q1 = enriched["1"]
    assist = q1["aei_v1_visual_science_assist"]
    assert q1["visual_science_capability_mode"] == "checklist"
    assert q1["visual_science_reasoning_type"] == "visual_checklist"
    assert q1["visual_type"] == "diagram"
    assert q1["manual_review_required"] is True
    assert q1["checklist_only"] is True
    assert assist["evidence_summary"]["checklist_present"] == ["cell wall", "nucleus"]
    assert assist["evidence_summary"]["checklist_missing"] == ["cytoplasm"]
    assert assist["autonomous_marks_from_checklist"] is False


def test_geography_map_checklist_is_not_automatic_marks():
    enriched = apply_visual_science_assist_metadata(
        {
            "1": {
                "marks_suggested": 1,
                "max_marks": 2,
                "student_answer": "legend and capital label present",
                "confidence": 0.72,
                "method": "heuristic_fallback",
            }
        },
        subject="Geography",
        question_contexts={
            "1": {
                "question_type": "map",
                "checklist": ["legend", "capital label", "scale"],
                "rubric": {"checklist": ["legend", "capital label", "scale"]},
            }
        },
    )

    q1 = enriched["1"]
    assist = q1["aei_v1_visual_science_assist"]
    assert q1["visual_science_capability_mode"] == "checklist"
    assert q1["visual_science_reasoning_type"] == "map_checklist"
    assert q1["manual_review_required"] is True
    assert assist["checklist_only"] is True
    assert assist["autonomous_visual_grading"] is False


def test_physics_formula_recognition_is_assistive():
    enriched = apply_visual_science_assist_metadata(
        {
            "1": {
                "marks_suggested": 1,
                "max_marks": 2,
                "student_answer": "F = ma",
                "confidence": 0.8,
                "method": "objective",
            }
        },
        subject="Physics",
        question_contexts={"1": {"question_type": "short", "answer_key": "F = ma"}},
    )

    q1 = enriched["1"]
    assist = q1["aei_v1_visual_science_assist"]
    assert q1["visual_science_capability_mode"] == "assist"
    assert q1["visual_science_reasoning_type"] == "formula_recognition"
    assert q1["manual_review_required"] is True
    assert assist["evidence_summary"]["formula_detected"] == "F = ma"
    assert assist["autonomous_science_grading"] is False


def test_chemistry_structures_remain_manual_review():
    enriched = apply_visual_science_assist_metadata(
        {
            "1": {
                "marks_suggested": 0,
                "max_marks": 3,
                "student_answer": "draw benzene structure",
                "confidence": 0.5,
                "method": "heuristic_fallback",
            }
        },
        subject="Chemistry",
        question_contexts={"1": {"question_type": "structure", "rubric": {}}},
    )

    q1 = enriched["1"]
    assist = q1["aei_v1_visual_science_assist"]
    assert q1["visual_science_capability_mode"] == "manual_review"
    assert q1["manual_review_required"] is True
    assert "structures" in q1["manual_review_reason"].lower()
    assert assist["autonomous_science_grading"] is False


def test_plain_math_answer_is_not_enriched():
    suggestions = {
        "1": {
            "marks_suggested": 2,
            "max_marks": 2,
            "student_answer": "4",
            "confidence": 0.98,
            "method": "objective",
        }
    }

    enriched = apply_visual_science_assist_metadata(
        suggestions,
        subject="Mathematics",
        question_contexts={"1": {"question_type": "short", "answer_key": "4"}},
    )

    assert enriched == suggestions
