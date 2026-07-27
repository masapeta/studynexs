"""AEI v1.0 Batch E visual/science assist metadata helpers.

Batch E makes visual and science uncertainty explicit without adding a visual
grader, changing marks, or certifying checklist-only evidence. The output is
suggestion metadata only; teachers remain the final authority.
"""

from __future__ import annotations

import re
from typing import Any, Mapping

from app.modules.eui.schemas.platform_capability import PlatformCapabilityLookupRequest
from app.modules.eui.services.platform_capability_lookup import PlatformCapabilityLookupService
from app.modules.examinations.schemas.academic_answer import AcademicAnswer
from app.modules.examinations.services.academic_reasoning_engine import (
    AcademicReasoningEngine,
)
from app.modules.examinations.services.academic_understanding_engine import (
    AcademicUnderstandingEngine,
)
from app.modules.examinations.services.subject_capability_registry import (
    CapabilityDescriptor,
    SubjectCapabilityRegistry,
)

AEI_VISUAL_SCIENCE_ASSIST_METHOD = "aei_v1_visual_science_assist"
AEI_VISUAL_SCIENCE_ASSIST_BATCH = "E"

_REVIEW_MODES = frozenset(
    {"partial", "assist", "checklist", "manual_review", "unsupported", "expansion"}
)
_MODE_CLAIM_RANK = {
    "unsupported": 0,
    "expansion": 1,
    "manual_review": 2,
    "partial": 3,
    "assist": 3,
    "checklist": 3,
    "supported": 4,
}
_VISUAL_QUESTION_TYPES = frozenset({"diagram", "graph", "map", "circuit", "flowchart", "visual"})
_SCIENCE_SUBJECTS = frozenset({"science", "physics", "chemistry", "biology"})
_VISUAL_SUBJECTS = frozenset({"biology", "geography", "physics", "mathematics", "maths", "math"})
_KNOWN_ELEMENTS = frozenset(
    {
        "H",
        "He",
        "Li",
        "Be",
        "B",
        "C",
        "N",
        "O",
        "F",
        "Ne",
        "Na",
        "Mg",
        "Al",
        "Si",
        "P",
        "S",
        "Cl",
        "Ar",
        "K",
        "Ca",
        "Fe",
        "Cu",
        "Zn",
        "Ag",
        "Au",
        "Hg",
        "Pb",
        "I",
    }
)
_DEFAULT_CHECKLISTS = {
    "graph": ("title", "axis labels", "scale", "plotted points"),
    "map": ("title", "legend", "labels", "direction"),
    "circuit": ("power source", "wires", "components", "labels"),
}


def apply_visual_science_assist_metadata(
    suggestions: Mapping[str, Mapping[str, Any]],
    *,
    subject: str | None = None,
    question_contexts: Mapping[str, Mapping[str, Any]] | None = None,
    subject_registry: SubjectCapabilityRegistry | None = None,
    lookup_service: PlatformCapabilityLookupService | None = None,
) -> dict[str, dict[str, Any]]:
    """Return suggestions enriched with Batch E visual/science assist metadata."""

    registry = subject_registry or SubjectCapabilityRegistry.load_default()
    platform_lookup = lookup_service or PlatformCapabilityLookupService()
    enriched: dict[str, dict[str, Any]] = {}
    for qno, suggestion in suggestions.items():
        context = (question_contexts or {}).get(str(qno), {})
        enriched[str(qno)] = _enrich_suggestion(
            qno=str(qno),
            suggestion=suggestion,
            subject=subject,
            context=context,
            subject_registry=registry,
            lookup_service=platform_lookup,
        )
    return enriched


def visual_science_manual_review_required(metadata: Mapping[str, Any]) -> bool:
    """Return whether Batch E metadata says visual/science needs review."""

    assist = metadata.get("aei_v1_visual_science_assist")
    if not isinstance(assist, Mapping):
        return False
    return bool(
        assist.get("manual_review_required")
        or assist.get("checklist_only")
        or assist.get("assist_only")
    )


def _enrich_suggestion(
    *,
    qno: str,
    suggestion: Mapping[str, Any],
    subject: str | None,
    context: Mapping[str, Any],
    subject_registry: SubjectCapabilityRegistry,
    lookup_service: PlatformCapabilityLookupService,
) -> dict[str, Any]:
    updated = dict(suggestion)
    raw_answer = str(updated.get("student_answer") or "")
    classification = _classify_question(
        subject=subject,
        raw_answer=raw_answer,
        context=context,
    )
    if classification is None:
        return updated

    checklist = _checklist_for_context(classification=classification, context=context)
    visual_observations = _visual_observations(
        raw_answer=raw_answer,
        checklist=checklist,
        context=context,
    )
    reasoning_context = {
        "answer_key": context.get("answer_key"),
        "checklist": list(checklist),
        "visual_observations": list(visual_observations),
    }
    understood = AcademicUnderstandingEngine().understand(
        AcademicAnswer(
            raw_input=raw_answer,
            subject=subject,
            question_type=classification["question_type"],
            metadata={"reasoning_context": reasoning_context},
        )
    )
    reasoning = AcademicReasoningEngine().reason(understood)
    descriptor = subject_registry.resolve(
        _registry_subject(subject),
        classification["capability"],
    )
    platform_capability = _lookup_platform_capability(
        lookup_service=lookup_service,
        subject=subject,
        classification=classification,
    )
    evidence_summary = _evidence_summary(
        classification=classification,
        reasoning=reasoning.model_dump(mode="json"),
        raw_answer=raw_answer,
        checklist=checklist,
    )
    review_reasons = _review_reasons(
        descriptor=descriptor,
        classification=classification,
        reasoning_result=reasoning.result,
    )
    capability_mode = descriptor.mode

    updated["manual_review_required"] = True
    updated["manual_review_reason"] = updated.get("manual_review_reason") or review_reasons[0]
    updated["capability_mode"] = _lowest_claim_mode(
        updated.get("capability_mode"),
        capability_mode,
    )
    updated["visual_science_capability_mode"] = capability_mode
    updated["visual_science_reasoning_type"] = classification["reasoning_type"]
    updated["visual_science_review_required"] = True
    updated["assist_only"] = True
    updated["checklist_only"] = classification["domain"] == "visual"

    if classification.get("visual_type"):
        updated["visual_type"] = classification["visual_type"]
    if understood.scientific_type:
        updated["scientific_type"] = understood.scientific_type

    updated["aei_v1_visual_science_assist"] = {
        "batch": AEI_VISUAL_SCIENCE_ASSIST_BATCH,
        "method": AEI_VISUAL_SCIENCE_ASSIST_METHOD,
        "question_no": qno,
        "subject": subject,
        "domain": classification["domain"],
        "capability": classification["capability"],
        "question_type": classification["question_type"],
        "visual_type": classification.get("visual_type"),
        "scientific_type": understood.scientific_type,
        "reasoning_type": classification["reasoning_type"],
        "reasoning_result": reasoning.result,
        "reasoning_explanation": reasoning.explanation,
        "evidence_summary": evidence_summary,
        "checklist_expected": tuple(checklist),
        "checklist_observed": tuple(visual_observations),
        "capability_mode": capability_mode,
        "subject_capability": descriptor.as_dict(),
        "platform_capability_id": (
            platform_capability.declaration.id
            if platform_capability is not None and platform_capability.declaration is not None
            else None
        ),
        "platform_registry_version": (
            platform_capability.registry_version if platform_capability is not None else None
        ),
        "review_reasons": tuple(review_reasons),
        "manual_review_required": True,
        "assist_only": True,
        "checklist_only": classification["domain"] == "visual",
        "autonomous_visual_grading": False,
        "autonomous_science_grading": False,
        "autonomous_marks_from_checklist": False,
    }
    return updated


def _classify_question(
    *,
    subject: str | None,
    raw_answer: str,
    context: Mapping[str, Any],
) -> dict[str, str] | None:
    subject_key = _normalize(subject)
    question_type = _question_type(context)
    text = " ".join(
        str(value or "")
        for value in (
            raw_answer,
            context.get("question_text"),
            context.get("topic"),
            context.get("answer_key"),
        )
    )

    if subject_key == "chemistry":
        if _looks_like_chemical_structure(text, question_type):
            return _classification(
                domain="science",
                capability="structures",
                reasoning_type="chemical_structure_manual_review",
                question_type=question_type,
            )
        if _contains_reaction_arrow(text):
            return _classification(
                domain="science",
                capability="reaction_balancing",
                reasoning_type="reaction_balancing",
                question_type=question_type,
            )
        if _chemical_symbols(text):
            return _classification(
                domain="science",
                capability="chemical_symbols",
                reasoning_type="chemical_symbol_assist",
                question_type=question_type,
            )

    if subject_key == "physics" and _looks_like_formula(text):
        return _classification(
            domain="science",
            capability="formula_recognition",
            reasoning_type="formula_recognition",
            question_type=question_type,
        )

    if question_type in _VISUAL_QUESTION_TYPES or _has_checklist(context):
        if question_type == "map":
            capability = "maps"
            reasoning_type = "map_checklist"
        elif question_type == "graph":
            capability = "graphs"
            reasoning_type = "graph_checklist"
        else:
            capability = "diagrams"
            reasoning_type = "visual_checklist"

        if subject_key in _VISUAL_SUBJECTS or question_type in _VISUAL_QUESTION_TYPES:
            return _classification(
                domain="visual",
                capability=capability,
                reasoning_type=reasoning_type,
                question_type=question_type,
                visual_type=question_type,
            )

    if subject_key in _SCIENCE_SUBJECTS and _looks_like_formula(text):
        return _classification(
            domain="science",
            capability="formula_recognition",
            reasoning_type="formula_recognition",
            question_type=question_type,
        )

    return None


def _classification(
    *,
    domain: str,
    capability: str,
    reasoning_type: str,
    question_type: str,
    visual_type: str | None = None,
) -> dict[str, str]:
    data = {
        "domain": domain,
        "capability": capability,
        "reasoning_type": reasoning_type,
        "question_type": question_type,
    }
    if visual_type:
        data["visual_type"] = visual_type
    return data


def _lookup_platform_capability(
    *,
    lookup_service: PlatformCapabilityLookupService,
    subject: str | None,
    classification: Mapping[str, str],
):
    capability_key = _platform_capability_key(classification, subject=subject)
    if capability_key is None:
        return None
    return lookup_service.lookup(
        PlatformCapabilityLookupRequest(
            domain=classification["domain"],
            capability_key=capability_key,
            subject=_display_subject(subject),
            input_type="image" if classification["domain"] == "visual" else None,
            artifact_type=(
                "answer_sheet" if classification["domain"] == "visual" else None
            ),
            metadata={"source": "aei_v1_batch_e"},
        )
    )


def _platform_capability_key(
    classification: Mapping[str, str],
    *,
    subject: str | None,
) -> str | None:
    if (
        classification["domain"] == "science"
        and classification["capability"] == "reaction_balancing"
    ):
        return "reaction_balancing"
    if classification["domain"] == "visual" and _normalize(subject) == "biology":
        return "biology_diagrams"
    return None


def _evidence_summary(
    *,
    classification: Mapping[str, str],
    reasoning: Mapping[str, Any],
    raw_answer: str,
    checklist: tuple[str, ...],
) -> dict[str, Any]:
    evidence = reasoning.get("evidence") if isinstance(reasoning, Mapping) else {}
    evidence = evidence if isinstance(evidence, Mapping) else {}
    summary: dict[str, Any] = {
        "capability": classification["capability"],
        "reasoning_type": classification["reasoning_type"],
        "reasoning_result": reasoning.get("result"),
        "review_required": True,
    }
    if classification["capability"] == "reaction_balancing":
        summary["chemical_balance_status"] = reasoning.get("result")
        summary["left_counts"] = evidence.get("left_counts")
        summary["right_counts"] = evidence.get("right_counts")
    if classification["capability"] == "chemical_symbols":
        summary["chemical_symbols"] = sorted(_chemical_symbols(raw_answer))
    if classification["capability"] == "formula_recognition":
        summary["formula_detected"] = _formula_signal(raw_answer)
    if classification["domain"] == "visual":
        summary["checklist_expected_count"] = len(checklist)
        summary["checklist_present"] = evidence.get("present", [])
        summary["checklist_missing"] = evidence.get("missing", list(checklist))
    if classification["capability"] == "structures":
        summary["structure_review_required"] = True
    return summary


def _review_reasons(
    *,
    descriptor: CapabilityDescriptor,
    classification: Mapping[str, str],
    reasoning_result: str,
) -> list[str]:
    reasons: list[str] = []
    if descriptor.teacher_review_required:
        reasons.append(
            descriptor.description
            or "Visual/science capability requires teacher review."
        )
    if classification["domain"] == "visual":
        reasons.append("Visual outputs are checklist-only and require teacher confirmation.")
    if classification["capability"] == "structures":
        reasons.append("Chemical structures remain manual-review in AEI v1.")
    if reasoning_result == "not_applicable":
        reasons.append("Deterministic visual/science reasoning was not applicable.")
    if not reasons:
        reasons.append("Visual/science assist evidence requires teacher confirmation.")
    return _dedupe(reasons)


def _checklist_for_context(
    *,
    classification: Mapping[str, str],
    context: Mapping[str, Any],
) -> tuple[str, ...]:
    checklist = _list_value(context.get("checklist"))
    if not checklist and isinstance(context.get("rubric"), Mapping):
        checklist = _list_value(context["rubric"].get("checklist"))
    if not checklist and isinstance(context.get("evaluation_config"), Mapping):
        checklist = _list_value(context["evaluation_config"].get("checklist"))
    if not checklist and classification.get("visual_type") in _DEFAULT_CHECKLISTS:
        checklist = list(_DEFAULT_CHECKLISTS[classification["visual_type"]])
    return tuple(str(item) for item in checklist if str(item).strip())


def _visual_observations(
    *,
    raw_answer: str,
    checklist: tuple[str, ...],
    context: Mapping[str, Any],
) -> tuple[str, ...]:
    explicit = _list_value(context.get("visual_observations"))
    if explicit:
        return tuple(str(item) for item in explicit if str(item).strip())
    normalized_answer = _normalize_text(raw_answer)
    return tuple(
        item
        for item in checklist
        if _normalize_text(item) and _normalize_text(item) in normalized_answer
    )


def _question_type(context: Mapping[str, Any]) -> str:
    for key in ("question_type", "type"):
        value = context.get(key)
        if value:
            return _normalize(str(value))
    rubric = context.get("rubric")
    if isinstance(rubric, Mapping):
        value = rubric.get("question_type") or rubric.get("type")
        if value:
            return _normalize(str(value))
    question = context.get("question")
    if isinstance(question, Mapping):
        value = question.get("question_type") or question.get("type")
        if value:
            return _normalize(str(value))
    return "short"


def _has_checklist(context: Mapping[str, Any]) -> bool:
    return bool(_checklist_for_context(classification={"visual_type": ""}, context=context))


def _contains_reaction_arrow(value: str) -> bool:
    return "->" in value or "\u2192" in value


def _looks_like_chemical_structure(value: str, question_type: str) -> bool:
    normalized = _normalize(value)
    return question_type in {"structure", "chemical_structure"} or any(
        signal in normalized
        for signal in (
            "draw_structure",
            "chemical_structure",
            "organic_structure",
            "benzene",
            "structural_formula",
        )
    )


def _chemical_symbols(value: str) -> set[str]:
    symbols = set(re.findall(r"\b([A-Z][a-z]?)\d*\b", value))
    return {symbol for symbol in symbols if symbol in _KNOWN_ELEMENTS}


def _looks_like_formula(value: str) -> bool:
    return _formula_signal(value) is not None


def _formula_signal(value: str) -> str | None:
    match = re.search(
        r"\b[A-Za-z][A-Za-z0-9_]*\s*=\s*[-+*/^A-Za-z0-9()\s]+",
        value,
    )
    return match.group(0).strip() if match else None


def _list_value(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return []


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


def _registry_subject(subject: str | None) -> str:
    normalized = _normalize(subject)
    if normalized in {"math", "maths"}:
        return "mathematics"
    return normalized


def _display_subject(subject: str | None) -> str | None:
    if not subject:
        return None
    return str(subject).strip()


def _normalize(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"[^a-z0-9]+", "_", value.strip().casefold()).strip("_")


def _normalize_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.strip().casefold()).strip()


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            deduped.append(value)
    return deduped
