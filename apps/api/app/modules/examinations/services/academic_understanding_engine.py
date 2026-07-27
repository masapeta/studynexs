"""Academic Understanding Engine for AEI v1.

Batch 2 establishes provider-based orchestration only. The engine enriches the
canonical ``AcademicAnswer`` with deterministic understanding metadata. It does
not reason against rubrics, assign marks, make policy decisions, or integrate
with the runtime Evaluation Service.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Protocol

from app.modules.examinations.schemas.academic_answer import AcademicAnswer


class AcademicProvider(Protocol):
    """Provider contract for AEI understanding providers."""

    name: str

    def supports(self, answer: AcademicAnswer) -> bool:
        """Return whether this provider can enrich the answer."""
        ...

    def process(self, answer: AcademicAnswer) -> AcademicAnswer:
        """Return an enriched answer without mutating raw input."""
        ...


@dataclass(frozen=True)
class ProviderExecution:
    """A single provider execution decision for observability in tests/future traces."""

    provider: str
    supported: bool

    @property
    def status(self) -> str:
        return "executed" if self.supported else "skipped"


class AcademicUnderstandingEngine:
    """Provider orchestrator for Academic Understanding.

    The default providers intentionally stop at understanding metadata. Later AEI
    batches add reasoning and policy on top of this enriched object.
    """

    def __init__(self, providers: list[AcademicProvider] | None = None) -> None:
        self.providers = providers if providers is not None else default_providers()

    def understand(self, answer: AcademicAnswer) -> AcademicAnswer:
        enriched = answer
        executions: list[ProviderExecution] = []
        for provider in self.providers:
            supported = provider.supports(enriched)
            executions.append(ProviderExecution(provider=provider.name, supported=supported))
            if supported:
                enriched = provider.process(enriched)
        return _record_provider_executions(enriched, executions)


class TextProvider:
    """Basic text understanding: blank detection and safe stripped representation."""

    name = "text"

    def supports(self, answer: AcademicAnswer) -> bool:
        return isinstance(answer.raw_input, str)

    def process(self, answer: AcademicAnswer) -> AcademicAnswer:
        raw = answer.raw_input or ""
        stripped = raw.strip()
        updates: dict[str, Any] = {}
        if answer.normalized_input is None:
            updates["normalized_input"] = stripped
        return _with_provider_metadata(
            answer,
            self.name,
            {
                "blank": stripped == "",
                "char_count": len(raw),
                "stripped_char_count": len(stripped),
            },
            updates=updates,
        )


class LanguageProvider:
    """Script/language signal provider for Indic and code-mixed answers."""

    name = "language"

    def supports(self, answer: AcademicAnswer) -> bool:
        return isinstance(answer.raw_input, str) and bool(answer.raw_input.strip())

    def process(self, answer: AcademicAnswer) -> AcademicAnswer:
        raw = answer.raw_input or ""
        scripts = _detect_scripts(raw)
        subject_language = _language_from_subject(answer.subject)
        detected_language = (
            answer.detected_language
            or subject_language
            or _language_from_scripts(scripts)
        )
        detected_script = answer.detected_script or _primary_script(scripts)
        code_mixed = answer.code_mixed or _is_code_mixed(scripts)
        return _with_provider_metadata(
            answer,
            self.name,
            {
                "scripts": sorted(scripts),
                "subject_language": subject_language,
                "detected_language": detected_language,
                "detected_script": detected_script,
                "code_mixed": code_mixed,
            },
            updates={
                "detected_language": detected_language,
                "detected_script": detected_script,
                "code_mixed": code_mixed,
            },
        )


class MathProvider:
    """Math signal provider.

    This detects numeric/expression-like shape only. Equivalence and tolerance are
    Batch 3+ reasoning/policy responsibilities.
    """

    name = "math"

    def supports(self, answer: AcademicAnswer) -> bool:
        raw = answer.raw_input or ""
        subject = _normalize_label(answer.subject)
        return subject in {"math", "maths", "mathematics"} or bool(_MATH_SIGNAL_RE.search(raw))

    def process(self, answer: AcademicAnswer) -> AcademicAnswer:
        raw = answer.raw_input or ""
        math_type = answer.math_type or _math_type(raw)
        return _with_provider_metadata(
            answer,
            self.name,
            {"math_type": math_type, "has_math_signal": bool(_MATH_SIGNAL_RE.search(raw))},
            updates={"math_type": math_type},
        )


class ScientificProvider:
    """Scientific-expression signal provider.

    This does not balance equations or judge formula correctness.
    """

    name = "scientific"

    def supports(self, answer: AcademicAnswer) -> bool:
        raw = answer.raw_input or ""
        subject = _normalize_label(answer.subject)
        return subject in {"physics", "chemistry", "science"} or bool(
            _SCIENCE_SIGNAL_RE.search(raw)
        )

    def process(self, answer: AcademicAnswer) -> AcademicAnswer:
        raw = answer.raw_input or ""
        scientific_type = answer.scientific_type or _scientific_type(raw)
        return _with_provider_metadata(
            answer,
            self.name,
            {
                "scientific_type": scientific_type,
                "has_science_signal": bool(_SCIENCE_SIGNAL_RE.search(raw)),
            },
            updates={"scientific_type": scientific_type},
        )


class VisualProvider:
    """Visual answer signal provider for diagram/map/graph style questions."""

    name = "visual"

    def supports(self, answer: AcademicAnswer) -> bool:
        question_type = _normalize_label(answer.question_type)
        raw = (answer.raw_input or "").lower()
        return question_type in _VISUAL_QUESTION_TYPES or "image region" in raw

    def process(self, answer: AcademicAnswer) -> AcademicAnswer:
        question_type = _normalize_label(answer.question_type)
        visual_type = answer.visual_type or (
            question_type
            if question_type in _VISUAL_QUESTION_TYPES
            else "answer_sheet_image_region"
        )
        return _with_provider_metadata(
            answer,
            self.name,
            {"visual_type": visual_type},
            updates={"visual_type": visual_type},
        )


class ConfidenceProvider:
    """Confidence placeholder provider.

    Batch 2 records that confidence has not been computed yet. Actual confidence
    consolidation belongs to later policy/reasoning batches.
    """

    name = "confidence"

    def supports(self, answer: AcademicAnswer) -> bool:
        return True

    def process(self, answer: AcademicAnswer) -> AcademicAnswer:
        return _with_provider_metadata(
            answer,
            self.name,
            {
                "computed": False,
                "reason": "Batch 2 AUE records provider traces but does not compute confidence.",
            },
        )


def default_providers() -> list[AcademicProvider]:
    """Return the default AEI Batch 2 provider order."""

    return [
        TextProvider(),
        LanguageProvider(),
        MathProvider(),
        ScientificProvider(),
        VisualProvider(),
        ConfidenceProvider(),
    ]


def _with_provider_metadata(
    answer: AcademicAnswer,
    provider_name: str,
    provider_metadata: dict[str, Any],
    *,
    updates: dict[str, Any] | None = None,
) -> AcademicAnswer:
    metadata = dict(answer.metadata)
    providers = dict(metadata.get("providers") or {})
    providers[provider_name] = provider_metadata
    metadata["providers"] = providers
    update_payload = {"metadata": metadata}
    if updates:
        update_payload.update(updates)
    return answer.model_copy(update=update_payload)


def _record_provider_executions(
    answer: AcademicAnswer,
    executions: list[ProviderExecution],
) -> AcademicAnswer:
    metadata = dict(answer.metadata)
    metadata["provider_trace"] = [
        {
            "provider": execution.provider,
            "status": execution.status,
            "supported": execution.supported,
        }
        for execution in executions
    ]
    return answer.model_copy(update={"metadata": metadata})


def _detect_scripts(value: str) -> set[str]:
    scripts: set[str] = set()
    if re.search(r"[A-Za-z]", value):
        scripts.add("latin")
    if re.search(r"[\u0900-\u097F]", value):
        scripts.add("devanagari")
    if re.search(r"[\u0C00-\u0C7F]", value):
        scripts.add("telugu")
    return scripts


def _language_from_subject(subject: str | None) -> str | None:
    normalized = _normalize_label(subject)
    if normalized == "hindi":
        return "hi"
    if normalized == "telugu":
        return "te"
    if normalized == "sanskrit":
        return "sa"
    return None


def _language_from_scripts(scripts: set[str]) -> str | None:
    if scripts == {"telugu"}:
        return "te"
    if scripts == {"latin"}:
        return "en"
    if scripts == {"devanagari"}:
        return "indic-devanagari"
    return None


def _primary_script(scripts: set[str]) -> str | None:
    if not scripts:
        return None
    if len(scripts) == 1:
        return next(iter(scripts))
    return "mixed"


def _is_code_mixed(scripts: set[str]) -> bool:
    return len(scripts) > 1 and "latin" in scripts


def _math_type(value: str) -> str | None:
    stripped = value.strip()
    if not stripped:
        return None
    if _NUMERIC_LIKE_RE.fullmatch(stripped):
        return "numeric_like"
    if _MATH_SIGNAL_RE.search(stripped):
        return "expression_like"
    return None


def _scientific_type(value: str) -> str | None:
    if re.search(r"(-+>|→)", value):
        return "chemical_equation_like"
    if re.search(r"\b[A-Za-z]\s*=", value):
        return "formula_like"
    if re.search(r"\b\d+(\.\d+)?\s*(cm|m|kg|g|s|ms|n|j|v|a)\b", value, re.IGNORECASE):
        return "unit_expression_like"
    return None


def _normalize_label(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


_MATH_SIGNAL_RE = re.compile(r"[\d½¼¾⅓⅔⅛⅜⅝⅞+\-*/=^√π%]")
_NUMERIC_LIKE_RE = re.compile(r"[-+]?(?:\d+(?:\.\d+)?|\d+/\d+|\d+[½¼¾⅓⅔⅛⅜⅝⅞])")
_SCIENCE_SIGNAL_RE = re.compile(
    r"(-+>|→|=|\b(?:cm|kg|mol|newton|joule|volt|ampere)\b)",
    re.IGNORECASE,
)
_VISUAL_QUESTION_TYPES = {"diagram", "graph", "map", "circuit", "flowchart", "visual"}
