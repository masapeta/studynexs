from app.core.config import Settings
from app.modules.examinations.services.aei_v1_language_ocr_assist import (
    ANSWER_SOURCE_OCR_IMAGE,
    ANSWER_SOURCE_PRINTED_OCR,
    ANSWER_SOURCE_TEACHER_TEXT,
    apply_language_ocr_assist_metadata,
    language_ocr_manual_review_required,
)


def test_language_ocr_assist_feature_flag_defaults_off():
    assert Settings().AEI_V1_LANGUAGE_OCR_ASSIST_ENABLED is False


def test_hindi_language_subject_manual_text_requires_teacher_review():
    enriched = apply_language_ocr_assist_metadata(
        {
            "1": {
                "marks_suggested": 1,
                "max_marks": 1,
                "student_answer": "उत्तर",
                "confidence": 0.95,
                "method": "objective",
            }
        },
        subject="Hindi",
        answer_sources={"1": ANSWER_SOURCE_TEACHER_TEXT},
    )

    q1 = enriched["1"]
    assist = q1["aei_v1_language_ocr_assist"]
    assert q1["answer_language"] == "Hindi"
    assert q1["detected_script"] == "Devanagari"
    assert q1["manual_review_required"] is True
    assert q1["requires_language_teacher_review"] is True
    assert assist["autonomous_language_grading"] is False
    assert language_ocr_manual_review_required(q1) is True


def test_hindi_handwriting_ocr_is_assistive_with_teacher_correction():
    enriched = apply_language_ocr_assist_metadata(
        {
            "1": {
                "marks_suggested": 1,
                "max_marks": 1,
                "student_answer": "उत्तर",
                "confidence": 0.95,
                "method": "objective",
            }
        },
        subject="Hindi",
        answer_sources={"1": ANSWER_SOURCE_OCR_IMAGE},
    )

    q1 = enriched["1"]
    assist = q1["aei_v1_language_ocr_assist"]
    assert q1["ocr_input_type"] == "handwriting"
    assert q1["ocr_confidence"] is None
    assert q1["language_ocr_capability_mode"] == "assist"
    assert q1["teacher_correction_required"] is True
    assert assist["ocr_confidence_missing"] is True
    assert "teacher correction" in q1["manual_review_reason"].lower()


def test_printed_hindi_ocr_supported_but_low_confidence_routes_to_review():
    enriched = apply_language_ocr_assist_metadata(
        {
            "1": {
                "marks_suggested": 1,
                "max_marks": 1,
                "student_answer": "उत्तर",
                "confidence": 0.95,
                "method": "objective",
            }
        },
        subject="Hindi",
        answer_sources={"1": ANSWER_SOURCE_PRINTED_OCR},
        ocr_confidence_by_question={"1": 0.58},
    )

    q1 = enriched["1"]
    assist = q1["aei_v1_language_ocr_assist"]
    assert q1["ocr_input_type"] == "printed_text"
    assert q1["language_ocr_capability_mode"] == "supported"
    assert q1["teacher_correction_required"] is True
    assert assist["low_ocr_confidence"] is True
    assert "below the teacher-review threshold" in q1["manual_review_reason"]


def test_telugu_handwriting_ocr_uses_assist_posture():
    enriched = apply_language_ocr_assist_metadata(
        {
            "1": {
                "marks_suggested": 1,
                "max_marks": 1,
                "student_answer": "ధన్యవాదాలు",
                "confidence": 0.95,
                "method": "objective",
            }
        },
        subject="Telugu",
        answer_sources={"1": ANSWER_SOURCE_OCR_IMAGE},
        ocr_confidence_by_question={"1": 0.82},
    )

    q1 = enriched["1"]
    assert q1["answer_language"] == "Telugu"
    assert q1["detected_script"] == "Telugu"
    assert q1["language_ocr_capability_mode"] == "assist"
    assert q1["manual_review_required"] is True
    assert q1["aei_v1_language_ocr_assist"]["capability_id"] == (
        "pc://eui/language/handwriting_ocr/telugu"
    )


def test_sanskrit_handwriting_ocr_uses_manual_review_posture():
    enriched = apply_language_ocr_assist_metadata(
        {
            "1": {
                "marks_suggested": 1,
                "max_marks": 1,
                "student_answer": "रामः गच्छति",
                "confidence": 0.95,
                "method": "objective",
            }
        },
        subject="Sanskrit",
        answer_sources={"1": ANSWER_SOURCE_OCR_IMAGE},
        ocr_confidence_by_question={"1": 0.82},
    )

    q1 = enriched["1"]
    assert q1["answer_language"] == "Sanskrit"
    assert q1["detected_script"] == "Devanagari"
    assert q1["language_ocr_capability_mode"] == "manual_review"
    assert q1["manual_review_required"] is True


def test_tinglish_manual_text_adds_context_without_forcing_review():
    enriched = apply_language_ocr_assist_metadata(
        {
            "1": {
                "marks_suggested": 0,
                "max_marks": 2,
                "student_answer": "idi ela solve cheyali?",
                "confidence": 0.8,
                "method": "heuristic_fallback",
            }
        },
        subject="Mathematics",
        answer_sources={"1": ANSWER_SOURCE_TEACHER_TEXT},
    )

    q1 = enriched["1"]
    assist = q1["aei_v1_language_ocr_assist"]
    assert q1["answer_language"] == "Telugu-English"
    assert q1["detected_script"] == "Latin"
    assert q1["code_mixed"] is True
    assert q1.get("manual_review_required") is not True
    assert q1["teacher_correction_required"] is False
    assert assist["assist_only"] is True
