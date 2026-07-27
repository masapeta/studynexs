"""AEI v1.0 Batch D language/OCR assist metadata helpers.

Batch D makes language and OCR uncertainty explicit without expanding OCR
capabilities, changing marks, or making autonomous language-grading claims.
The output is suggestion metadata only; teachers remain the final authority.
"""

from __future__ import annotations

import re
from typing import Any, Mapping

from app.modules.eui.schemas.platform_capability import PlatformCapabilityLookupRequest
from app.modules.eui.services.platform_capability_lookup import PlatformCapabilityLookupService
from app.modules.examinations.schemas.academic_answer import AcademicAnswer
from app.modules.examinations.services.academic_understanding_engine import (
    AcademicUnderstandingEngine,
)

AEI_LANGUAGE_OCR_ASSIST_METHOD = "aei_v1_language_ocr_assist"
AEI_LANGUAGE_OCR_ASSIST_BATCH = "D"
OCR_CONFIDENCE_REVIEW_THRESHOLD = 0.75

ANSWER_SOURCE_TEACHER_TEXT = "teacher_text"
ANSWER_SOURCE_OCR_IMAGE = "ocr_image"
ANSWER_SOURCE_PRINTED_OCR = "printed_ocr"

_LANGUAGE_SUBJECTS = frozenset({"hindi", "telugu", "sanskrit"})
_REVIEW_MODES = frozenset({"assist", "checklist", "manual_review", "unsupported", "expansion"})
_MODE_CLAIM_RANK = {
    "unsupported": 0,
    "expansion": 1,
    "manual_review": 2,
    "assist": 3,
    "checklist": 3,
    "supported": 4,
}

_CODE_TO_LANGUAGE = {
    "hi": "Hindi",
    "te": "Telugu",
    "sa": "Sanskrit",
    "en": "English",
    "indic-devanagari": "Indic-Devanagari",
}
_SCRIPT_LABELS = {
    "devanagari": "Devanagari",
    "telugu": "Telugu",
    "latin": "Latin",
    "mixed": "Mixed",
}
_SUBJECT_TO_LANGUAGE = {
    "hindi": "Hindi",
    "telugu": "Telugu",
    "sanskrit": "Sanskrit",
}
_ROMANIZED_LANGUAGE_HINTS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    (
        "Hindi-English",
        "Hindi",
        ("kaise", "kya", "matlab", "karna", "hai", "nahi", "samjhao"),
    ),
    (
        "Telugu-English",
        "Telugu",
        ("ela", "cheyali", "cheppu", "idi", "enti", "nenu", "vellanu"),
    ),
)


def apply_language_ocr_assist_metadata(
    suggestions: Mapping[str, Mapping[str, Any]],
    *,
    subject: str | None = None,
    answer_sources: Mapping[str, str] | None = None,
    ocr_confidence_by_question: Mapping[str, float | None] | None = None,
    lookup_service: PlatformCapabilityLookupService | None = None,
) -> dict[str, dict[str, Any]]:
    """Return suggestions enriched with Batch D language/OCR assist metadata."""

    service = lookup_service or PlatformCapabilityLookupService()
    enriched: dict[str, dict[str, Any]] = {}
    for qno, suggestion in suggestions.items():
        enriched[str(qno)] = _enrich_suggestion(
            qno=str(qno),
            suggestion=suggestion,
            subject=subject,
            answer_source=(answer_sources or {}).get(str(qno), ANSWER_SOURCE_TEACHER_TEXT),
            ocr_confidence=(ocr_confidence_by_question or {}).get(str(qno)),
            lookup_service=service,
        )
    return enriched


def language_ocr_manual_review_required(metadata: Mapping[str, Any]) -> bool:
    """Return whether Batch D metadata says language/OCR needs review."""

    assist = metadata.get("aei_v1_language_ocr_assist")
    if not isinstance(assist, Mapping):
        return False
    return bool(
        assist.get("teacher_correction_required")
        or assist.get("requires_language_teacher_review")
        or assist.get("low_ocr_confidence")
        or assist.get("ocr_confidence_missing")
    )


def _enrich_suggestion(
    *,
    qno: str,
    suggestion: Mapping[str, Any],
    subject: str | None,
    answer_source: str,
    ocr_confidence: float | None,
    lookup_service: PlatformCapabilityLookupService,
) -> dict[str, Any]:
    updated = dict(suggestion)
    raw_answer = str(updated.get("student_answer") or "")
    understood = AcademicUnderstandingEngine().understand(
        AcademicAnswer(raw_input=raw_answer, subject=subject)
    )

    detected_language = _detected_language_label(
        subject=subject,
        detected_language=understood.detected_language,
        raw_answer=raw_answer,
    )
    detected_script = _script_label(understood.detected_script)
    code_mixed = bool(understood.code_mixed) or _romanized_code_mixed(raw_answer)
    if code_mixed and detected_script == "Latin":
        romanized_label, _ = _romanized_language(raw_answer)
        detected_language = romanized_label or detected_language

    input_type = _input_type(answer_source)
    capability_key = _capability_key(input_type)
    capability = _lookup_capability(
        lookup_service=lookup_service,
        language=detected_language,
        script=detected_script,
        input_type=input_type,
        capability_key=capability_key,
    )

    language_confidence = _language_confidence(
        subject=subject,
        detected_language=detected_language,
        detected_script=detected_script,
        code_mixed=code_mixed,
        raw_answer=raw_answer,
    )
    review_reasons = _review_reasons(
        subject=subject,
        answer_source=answer_source,
        input_type=input_type,
        detected_language=detected_language,
        ocr_confidence=ocr_confidence,
        capability=capability,
    )
    review_required = bool(review_reasons) or bool(updated.get("manual_review_required"))

    updated["answer_language"] = detected_language
    updated["detected_script"] = detected_script
    updated["code_mixed"] = code_mixed
    updated["language_confidence"] = language_confidence
    updated["answer_input_source"] = answer_source
    updated["ocr_input_type"] = (
        input_type if input_type in {"handwriting", "printed_text"} else None
    )
    updated["ocr_confidence"] = (
        ocr_confidence if input_type in {"handwriting", "printed_text"} else None
    )
    updated["teacher_correction_required"] = _teacher_correction_required(
        answer_source=answer_source,
        review_reasons=review_reasons,
    )
    updated["requires_language_teacher_review"] = _requires_language_review(
        subject=subject,
        review_reasons=review_reasons,
    )
    if review_required:
        updated["manual_review_required"] = True
        updated["manual_review_reason"] = updated.get("manual_review_reason") or review_reasons[0]

    capability_mode = _capability_mode(capability)
    if capability_mode:
        updated["language_ocr_capability_mode"] = capability_mode
        updated["capability_mode"] = _lowest_claim_mode(
            updated.get("capability_mode"),
            (
                "manual_review"
                if review_required and capability_mode == "supported"
                else capability_mode
            ),
        )

    updated["aei_v1_language_ocr_assist"] = {
        "batch": AEI_LANGUAGE_OCR_ASSIST_BATCH,
        "method": AEI_LANGUAGE_OCR_ASSIST_METHOD,
        "question_no": qno,
        "answer_input_source": answer_source,
        "ocr_input_type": input_type if input_type in {"handwriting", "printed_text"} else None,
        "detected_language": detected_language,
        "detected_script": detected_script,
        "code_mixed": code_mixed,
        "language_confidence": language_confidence,
        "ocr_confidence": updated["ocr_confidence"],
        "ocr_confidence_threshold": OCR_CONFIDENCE_REVIEW_THRESHOLD,
        "ocr_confidence_missing": _ocr_confidence_missing(
            input_type=input_type,
            ocr_confidence=ocr_confidence,
        ),
        "low_ocr_confidence": _low_ocr_confidence(
            input_type=input_type,
            ocr_confidence=ocr_confidence,
        ),
        "teacher_correction_required": updated["teacher_correction_required"],
        "requires_language_teacher_review": updated["requires_language_teacher_review"],
        "review_reasons": tuple(review_reasons),
        "capability_mode": capability_mode,
        "capability_review_required": (
            capability.review_required if capability is not None else None
        ),
        "capability_id": (
            capability.declaration.id
            if capability is not None and capability.declaration is not None
            else None
        ),
        "capability_registry_version": (
            capability.registry_version if capability is not None else None
        ),
        "assist_only": True,
        "autonomous_language_grading": False,
    }
    return updated


def _lookup_capability(
    *,
    lookup_service: PlatformCapabilityLookupService,
    language: str | None,
    script: str | None,
    input_type: str,
    capability_key: str | None,
):
    if not capability_key or not language:
        return None
    lookup_language = _registry_language(language)
    lookup_script = _registry_script(script)
    return lookup_service.lookup(
        PlatformCapabilityLookupRequest(
            domain="language",
            capability_key=capability_key,
            language=lookup_language,
            script=lookup_script,
            input_type=input_type,
            metadata={"source": "aei_v1_batch_d"},
        )
    )


def _review_reasons(
    *,
    subject: str | None,
    answer_source: str,
    input_type: str,
    detected_language: str | None,
    ocr_confidence: float | None,
    capability: Any | None,
) -> list[str]:
    reasons: list[str] = []
    if input_type in {"handwriting", "printed_text"}:
        if ocr_confidence is None:
            reasons.append("OCR confidence is unavailable; teacher correction is required.")
        elif ocr_confidence < OCR_CONFIDENCE_REVIEW_THRESHOLD:
            reasons.append("OCR confidence is below the teacher-review threshold.")

    if input_type == "handwriting" and _is_indic_language(detected_language):
        reasons.append("Indic handwriting OCR is assistive and requires teacher correction.")

    if capability is not None and capability.review_required:
        statement = (
            capability.declaration.scope_statement
            if capability.declaration is not None
            else None
        )
        reasons.append(statement or "Capability registry requires teacher review.")

    if _is_language_subject(subject):
        reasons.append("Language-subject grading remains teacher-review posture.")

    if answer_source == ANSWER_SOURCE_OCR_IMAGE and not reasons:
        reasons.append("Image-derived answer text requires teacher confirmation.")

    return _dedupe(reasons)


def _detected_language_label(
    *,
    subject: str | None,
    detected_language: str | None,
    raw_answer: str,
) -> str | None:
    subject_language = _SUBJECT_TO_LANGUAGE.get(_normalize(subject))
    if subject_language:
        return subject_language
    romanized_label, canonical_language = _romanized_language(raw_answer)
    if romanized_label:
        return romanized_label
    if canonical_language:
        return canonical_language
    return _CODE_TO_LANGUAGE.get(str(detected_language or "").casefold(), detected_language)


def _script_label(script: str | None) -> str | None:
    if not script:
        return None
    return _SCRIPT_LABELS.get(script.casefold(), script)


def _romanized_language(value: str) -> tuple[str | None, str | None]:
    words = set(re.findall(r"[a-z]+", value.casefold()))
    if not words:
        return None, None
    for mixed_label, canonical_language, hints in _ROMANIZED_LANGUAGE_HINTS:
        if words & set(hints):
            return mixed_label, canonical_language
    return None, None


def _romanized_code_mixed(value: str) -> bool:
    mixed_label, _ = _romanized_language(value)
    return mixed_label is not None


def _language_confidence(
    *,
    subject: str | None,
    detected_language: str | None,
    detected_script: str | None,
    code_mixed: bool,
    raw_answer: str,
) -> float | None:
    if not raw_answer.strip():
        return None
    if _is_language_subject(subject) and detected_language:
        return 0.9
    if code_mixed:
        return 0.65
    if detected_script in {"Devanagari", "Telugu", "Latin"} and detected_language:
        return 0.78
    if detected_language:
        return 0.7
    return None


def _input_type(answer_source: str) -> str:
    if answer_source == ANSWER_SOURCE_OCR_IMAGE:
        return "handwriting"
    if answer_source == ANSWER_SOURCE_PRINTED_OCR:
        return "printed_text"
    return "manual_text"


def _capability_key(input_type: str) -> str | None:
    if input_type == "handwriting":
        return "handwriting_ocr"
    if input_type == "printed_text":
        return "printed_ocr"
    return None


def _capability_mode(capability: Any | None) -> str | None:
    return capability.mode if capability is not None else None


def _teacher_correction_required(*, answer_source: str, review_reasons: list[str]) -> bool:
    return answer_source in {ANSWER_SOURCE_OCR_IMAGE, ANSWER_SOURCE_PRINTED_OCR} and bool(
        review_reasons
    )


def _requires_language_review(*, subject: str | None, review_reasons: list[str]) -> bool:
    return _is_language_subject(subject) or any(
        "language" in reason.lower() for reason in review_reasons
    )


def _ocr_confidence_missing(*, input_type: str, ocr_confidence: float | None) -> bool:
    return input_type in {"handwriting", "printed_text"} and ocr_confidence is None


def _low_ocr_confidence(*, input_type: str, ocr_confidence: float | None) -> bool:
    return (
        input_type in {"handwriting", "printed_text"}
        and ocr_confidence is not None
        and ocr_confidence < OCR_CONFIDENCE_REVIEW_THRESHOLD
    )


def _registry_language(language: str | None) -> str | None:
    if not language:
        return None
    if language in {"Hindi-English", "Telugu-English"}:
        return language.split("-", 1)[0]
    if language == "Indic-Devanagari":
        return "Hindi"
    return language


def _registry_script(script: str | None) -> str | None:
    if script == "Mixed":
        return None
    return script


def _is_language_subject(subject: str | None) -> bool:
    return _normalize(subject) in _LANGUAGE_SUBJECTS


def _is_indic_language(language: str | None) -> bool:
    return language in {"Hindi", "Telugu", "Sanskrit", "Hindi-English", "Telugu-English"}


def _lowest_claim_mode(existing: Any, candidate: str | None) -> str | None:
    if not candidate:
        return str(existing) if existing else None
    if not existing:
        return candidate
    existing_str = str(existing)
    if existing_str not in _MODE_CLAIM_RANK or candidate not in _MODE_CLAIM_RANK:
        return candidate
    return (
        existing_str
        if _MODE_CLAIM_RANK[existing_str] <= _MODE_CLAIM_RANK[candidate]
        else candidate
    )


def _normalize(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"[^a-z0-9]+", "_", value.strip().casefold()).strip("_")


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            deduped.append(value)
    return deduped
