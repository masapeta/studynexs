"""Academic Reasoning Layer for AEI v1.

Batch 3 converts deterministic understanding metadata into deterministic academic
meaning. It does not assign marks, invoke evaluation policy, route teacher review,
or integrate with the runtime Evaluation Service.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Protocol

from app.modules.examinations.schemas.academic_answer import AcademicAnswer
from app.modules.examinations.schemas.academic_reasoning_result import (
    AcademicReasoningResult,
    ReasonerTraceEntry,
)


class AcademicReasoner(Protocol):
    """Minimal reasoner contract for AEI Batch 3."""

    name: str

    def supports(self, answer: AcademicAnswer) -> bool:
        """Return whether this reasoner can interpret academic meaning."""
        ...

    def reason(self, answer: AcademicAnswer) -> AcademicReasoningResult:
        """Return deterministic academic meaning without marks or policy."""
        ...


@dataclass(frozen=True)
class ReasonerExecution:
    """A single reasoner execution decision."""

    reasoner: str
    supported: bool
    executed: bool
    result: str | None = None
    metadata: dict[str, Any] | None = None

    @property
    def status(self) -> str:
        return "executed" if self.executed else "skipped"


class AcademicReasoningEngine:
    """Orchestrates deterministic Academic Reasoners.

    The engine itself contains no subject-specific reasoning. It selects the first
    supported reasoner from the configured deterministic order and records a trace
    for all reasoners.
    """

    def __init__(self, reasoners: list[AcademicReasoner] | None = None) -> None:
        self.reasoners = reasoners if reasoners is not None else default_reasoners()

    def reason(self, answer: AcademicAnswer) -> AcademicReasoningResult:
        selected_result: AcademicReasoningResult | None = None
        executions: list[ReasonerExecution] = []
        for reasoner in self.reasoners:
            supported = reasoner.supports(answer)
            should_execute = supported and selected_result is None
            trace_result: str | None = None
            trace_metadata: dict[str, Any] | None = None
            if should_execute:
                selected_result = reasoner.reason(answer)
                trace_result = selected_result.result
                trace_metadata = {
                    "reasoning_type": selected_result.reasoning_type,
                    "capability": selected_result.capability,
                }
            executions.append(
                ReasonerExecution(
                    reasoner=reasoner.name,
                    supported=supported,
                    executed=should_execute,
                    result=trace_result,
                    metadata=trace_metadata,
                )
            )

        result = selected_result or AcademicReasoningResult(
            reasoning_type="none",
            result="not_applicable",
            subject=answer.subject,
            explanation="No deterministic AEI reasoner supported this answer.",
        )
        return result.model_copy(update={"reasoner_trace": _trace_entries(executions)})


class UnitInterpretationReasoner:
    """Deterministically interprets number-with-unit answers."""

    name = "unit_interpretation"

    def supports(self, answer: AcademicAnswer) -> bool:
        raw = _answer_text(answer)
        context = _reasoning_context(answer)
        return _parse_unit_value(raw) is not None or bool(context.get("units"))

    def reason(self, answer: AcademicAnswer) -> AcademicReasoningResult:
        raw = _answer_text(answer)
        parsed = _parse_unit_value(raw)
        context = _reasoning_context(answer)
        candidates = _candidate_answers(context)
        allowed_units = _allowed_units(context)

        evidence: dict[str, Any] = {
            "raw_answer": raw,
            "parsed_answer": parsed,
            "allowed_units": allowed_units,
        }
        if parsed is None:
            return AcademicReasoningResult(
                reasoning_type="unit_interpretation",
                result="not_applicable",
                subject=answer.subject,
                capability="units",
                explanation="The answer could not be interpreted as a deterministic unit value.",
                evidence=evidence,
                review_signals=("unit_parse_failed",),
            )

        candidate_matches = [_parse_unit_value(candidate) for candidate in candidates]
        candidate_matches = [candidate for candidate in candidate_matches if candidate is not None]
        evidence["candidate_values"] = candidate_matches

        unit_allowed = not allowed_units or parsed["unit"] in allowed_units
        matched = any(
            candidate["value"] == parsed["value"] and candidate["unit"] == parsed["unit"]
            for candidate in candidate_matches
        )

        if matched and unit_allowed:
            result = "matched"
            explanation = "The answer value and unit match the deterministic unit context."
        elif not unit_allowed:
            result = "not_matched"
            explanation = "The answer unit is not in the allowed unit set."
        elif candidate_matches:
            result = "not_matched"
            explanation = "The answer did not match the deterministic unit context."
        else:
            result = "interpreted"
            explanation = "The answer was interpreted as a unit value."

        return AcademicReasoningResult(
            reasoning_type="unit_interpretation",
            result=result,
            subject=answer.subject,
            capability="units",
            explanation=explanation,
            interpreted_value=f"{parsed['value']} {parsed['unit']}",
            matched_value=_first_matching_unit_value(parsed, candidate_matches),
            evidence=evidence,
        )


class ScientificNotationReasoner:
    """Deterministically interprets scientific notation equivalence."""

    name = "scientific_notation"

    def supports(self, answer: AcademicAnswer) -> bool:
        raw = _answer_text(answer)
        return _looks_like_scientific_notation(raw)

    def reason(self, answer: AcademicAnswer) -> AcademicReasoningResult:
        raw = _answer_text(answer)
        parsed = _parse_number(raw)
        context = _reasoning_context(answer)
        candidates = _candidate_answers(context)
        candidate_values = [_parse_number(candidate) for candidate in candidates]
        candidate_values = [value for value in candidate_values if value is not None]

        evidence = {
            "raw_answer": raw,
            "parsed_answer": str(parsed) if parsed is not None else None,
            "candidate_values": [str(value) for value in candidate_values],
        }
        if parsed is None:
            return AcademicReasoningResult(
                reasoning_type="scientific_notation",
                result="not_applicable",
                subject=answer.subject,
                capability="scientific_notation",
                explanation="The answer could not be interpreted as scientific notation.",
                evidence=evidence,
                review_signals=("scientific_notation_parse_failed",),
            )

        matched = _decimal_match(parsed, candidate_values)
        if matched:
            result = "equivalent"
            explanation = "The scientific notation is equivalent to the deterministic context."
        elif candidate_values:
            result = "not_equivalent"
            explanation = "The scientific notation is not equivalent to the deterministic context."
        else:
            result = "interpreted"
            explanation = "The scientific notation was interpreted deterministically."

        return AcademicReasoningResult(
            reasoning_type="scientific_notation",
            result=result,
            subject=answer.subject,
            capability="scientific_notation",
            explanation=explanation,
            interpreted_value=str(parsed.normalize()),
            matched_value=_first_matching_decimal(parsed, candidate_values),
            evidence=evidence,
        )


class NumericEquivalenceReasoner:
    """Deterministically interprets numeric equivalence."""

    name = "numeric_equivalence"

    def supports(self, answer: AcademicAnswer) -> bool:
        raw = _answer_text(answer)
        return _parse_number(raw) is not None

    def reason(self, answer: AcademicAnswer) -> AcademicReasoningResult:
        raw = _answer_text(answer)
        parsed = _parse_number(raw)
        context = _reasoning_context(answer)
        candidates = _candidate_answers(context)
        candidate_values = [_parse_number(candidate) for candidate in candidates]
        candidate_values = [value for value in candidate_values if value is not None]

        evidence = {
            "raw_answer": raw,
            "parsed_answer": str(parsed) if parsed is not None else None,
            "candidate_values": [str(value) for value in candidate_values],
        }
        if parsed is None:
            return AcademicReasoningResult(
                reasoning_type="numeric_equivalence",
                result="not_applicable",
                subject=answer.subject,
                capability="numeric_equivalence",
                explanation="The answer could not be interpreted as a deterministic number.",
                evidence=evidence,
                review_signals=("numeric_parse_failed",),
            )

        matched = _decimal_match(parsed, candidate_values)
        if matched:
            result = "equivalent"
            explanation = "The numeric answer is equivalent to the deterministic context."
        elif candidate_values:
            result = "not_equivalent"
            explanation = "The numeric answer is not equivalent to the deterministic context."
        else:
            result = "interpreted"
            explanation = "The numeric answer was interpreted deterministically."

        return AcademicReasoningResult(
            reasoning_type="numeric_equivalence",
            result=result,
            subject=answer.subject,
            capability="numeric_equivalence",
            explanation=explanation,
            interpreted_value=str(parsed.normalize()),
            matched_value=_first_matching_decimal(parsed, candidate_values),
            evidence=evidence,
        )


class ChemicalEquationReasoner:
    """Deterministically interprets simple chemical equation balance."""

    name = "chemical_equation"

    def supports(self, answer: AcademicAnswer) -> bool:
        raw = _answer_text(answer)
        return _contains_reaction_arrow(raw)

    def reason(self, answer: AcademicAnswer) -> AcademicReasoningResult:
        raw = _answer_text(answer)
        balance = _chemical_balance(raw)
        if balance is None:
            return AcademicReasoningResult(
                reasoning_type="reaction_balancing",
                result="not_applicable",
                subject=answer.subject,
                capability="reaction_balancing",
                explanation="The equation could not be parsed deterministically.",
                evidence={"raw_answer": raw},
                review_signals=("chemical_equation_parse_failed",),
            )

        left, right = balance
        balanced = left == right
        return AcademicReasoningResult(
            reasoning_type="reaction_balancing",
            result="balanced" if balanced else "unbalanced",
            subject=answer.subject,
            capability="reaction_balancing",
            explanation=(
                "The chemical equation is balanced."
                if balanced
                else "The chemical equation is not balanced."
            ),
            evidence={
                "raw_answer": raw,
                "left_counts": dict(left),
                "right_counts": dict(right),
            },
        )


class VisualChecklistReasoner:
    """Deterministically interprets visual checklist observations."""

    name = "visual_checklist"

    def supports(self, answer: AcademicAnswer) -> bool:
        context = _reasoning_context(answer)
        return bool(answer.visual_type and isinstance(context.get("checklist"), list))

    def reason(self, answer: AcademicAnswer) -> AcademicReasoningResult:
        context = _reasoning_context(answer)
        expected = [str(item) for item in context.get("checklist", [])]
        observed = [str(item) for item in context.get("visual_observations", [])]
        observed_normalized = {_normalize_text(item) for item in observed}
        present = [item for item in expected if _normalize_text(item) in observed_normalized]
        missing = [item for item in expected if _normalize_text(item) not in observed_normalized]

        return AcademicReasoningResult(
            reasoning_type="visual_checklist",
            result="checklist",
            subject=answer.subject,
            capability=answer.visual_type or "visual",
            explanation="Visual checklist observations were interpreted deterministically.",
            evidence={
                "expected": expected,
                "observed": observed,
                "present": present,
                "missing": missing,
            },
        )


def default_reasoners() -> list[AcademicReasoner]:
    """Return the default AEI Batch 3 deterministic reasoner order."""

    return [
        UnitInterpretationReasoner(),
        ScientificNotationReasoner(),
        NumericEquivalenceReasoner(),
        ChemicalEquationReasoner(),
        VisualChecklistReasoner(),
    ]


def _trace_entries(executions: list[ReasonerExecution]) -> tuple[ReasonerTraceEntry, ...]:
    return tuple(
        ReasonerTraceEntry(
            reasoner=execution.reasoner,
            status=execution.status,
            supported=execution.supported,
            result=execution.result,
            metadata=execution.metadata or {},
        )
        for execution in executions
    )


def _answer_text(answer: AcademicAnswer) -> str:
    if answer.normalized_input is not None:
        return answer.normalized_input
    return answer.raw_input or ""


def _reasoning_context(answer: AcademicAnswer) -> dict[str, Any]:
    context = answer.metadata.get("reasoning_context", {})
    return context if isinstance(context, dict) else {}


def _candidate_answers(context: dict[str, Any]) -> list[str]:
    candidates: list[str] = []
    answer_key = context.get("answer_key")
    if answer_key is not None:
        candidates.append(str(answer_key))
    acceptable = context.get("acceptable_answers", [])
    if isinstance(acceptable, list):
        candidates.extend(str(value) for value in acceptable if value is not None)
    return candidates


def _allowed_units(context: dict[str, Any]) -> set[str]:
    units = context.get("units", {})
    if not isinstance(units, dict):
        return set()
    allowed = units.get("allowed", [])
    if not isinstance(allowed, list):
        return set()
    return {_normalize_unit(str(unit)) for unit in allowed if unit}


def _parse_unit_value(value: str) -> dict[str, Any] | None:
    match = re.fullmatch(
        r"\s*(?P<number>[-+]?(?:\d+(?:\.\d+)?|\d+/\d+))\s*(?P<unit>[A-Za-z]+)\s*",
        value,
    )
    if not match:
        return None
    number = _parse_number(match.group("number"))
    if number is None:
        return None
    return {"value": str(number.normalize()), "unit": _normalize_unit(match.group("unit"))}


def _parse_number(value: str) -> Decimal | None:
    stripped = value.strip().replace(",", "")
    if not stripped:
        return None

    mixed_fraction = _parse_mixed_fraction(stripped)
    if mixed_fraction is not None:
        return mixed_fraction

    scientific = _parse_scientific_notation(stripped)
    if scientific is not None:
        return scientific

    if "/" in stripped:
        parts = stripped.split("/")
        if len(parts) == 2:
            numerator = _decimal(parts[0])
            denominator = _decimal(parts[1])
            if numerator is not None and denominator not in {None, Decimal("0")}:
                return numerator / denominator
        return None

    return _decimal(stripped)


def _parse_mixed_fraction(value: str) -> Decimal | None:
    unicode_fraction = _parse_unicode_fraction(value)
    if unicode_fraction is not None:
        return unicode_fraction

    match = re.fullmatch(r"(?P<whole>[-+]?\d+)\s+(?P<num>\d+)/(?P<den>\d+)", value)
    if not match:
        return None
    whole = _decimal(match.group("whole"))
    numerator = _decimal(match.group("num"))
    denominator = _decimal(match.group("den"))
    if whole is None or numerator is None or denominator in {None, Decimal("0")}:
        return None
    sign = Decimal("-1") if whole < 0 else Decimal("1")
    return whole + (sign * numerator / denominator)


def _parse_unicode_fraction(value: str) -> Decimal | None:
    if not value:
        return None
    fraction = _UNICODE_FRACTIONS.get(value[-1])
    if fraction is None:
        return None
    prefix = value[:-1].strip()
    if not prefix:
        return fraction
    whole = _decimal(prefix)
    if whole is None:
        return None
    sign = Decimal("-1") if whole < 0 else Decimal("1")
    return whole + (sign * fraction)


def _parse_scientific_notation(value: str) -> Decimal | None:
    normalized = value.lower().replace("×", "x").replace(" ", "")
    match = re.fullmatch(
        r"(?P<mantissa>[-+]?\d+(?:\.\d+)?)(?:x10\^|e)(?P<exp>[-+]?\d+)",
        normalized,
    )
    if not match:
        return None
    mantissa = _decimal(match.group("mantissa"))
    exponent = _decimal(match.group("exp"))
    if mantissa is None or exponent is None:
        return None
    return mantissa * (Decimal(10) ** int(exponent))


def _decimal(value: str) -> Decimal | None:
    try:
        return Decimal(value.strip())
    except (InvalidOperation, ValueError):
        return None


def _decimal_match(value: Decimal, candidates: list[Decimal]) -> bool:
    return any(value == candidate for candidate in candidates)


def _first_matching_decimal(value: Decimal, candidates: list[Decimal]) -> str | None:
    for candidate in candidates:
        if value == candidate:
            return str(candidate.normalize())
    return None


def _first_matching_unit_value(
    value: dict[str, Any],
    candidates: list[dict[str, Any]],
) -> str | None:
    for candidate in candidates:
        if candidate["value"] == value["value"] and candidate["unit"] == value["unit"]:
            return f"{candidate['value']} {candidate['unit']}"
    return None


def _looks_like_scientific_notation(value: str) -> bool:
    normalized = value.lower().replace("×", "x").replace(" ", "")
    return bool(re.fullmatch(r"[-+]?\d+(?:\.\d+)?(?:x10\^|e)[-+]?\d+", normalized))


def _contains_reaction_arrow(value: str) -> bool:
    return "->" in value or "\u2192" in value


def _chemical_balance(value: str) -> tuple[Counter[str], Counter[str]] | None:
    if "\u2192" in value:
        left_text, right_text = value.split("\u2192", 1)
    elif "->" in value:
        left_text, right_text = value.split("->", 1)
    else:
        return None

    left = _side_counts(left_text)
    right = _side_counts(right_text)
    if left is None or right is None:
        return None
    return left, right


def _side_counts(side: str) -> Counter[str] | None:
    counts: Counter[str] = Counter()
    terms = [term.strip() for term in side.split("+") if term.strip()]
    if not terms:
        return None
    for term in terms:
        parsed = _formula_counts(term)
        if parsed is None:
            return None
        counts.update(parsed)
    return counts


def _formula_counts(term: str) -> Counter[str] | None:
    match = re.fullmatch(r"(?P<coef>\d*)\s*(?P<formula>(?:[A-Z][a-z]?\d*)+)", term)
    if not match:
        return None
    coefficient = int(match.group("coef") or "1")
    formula = match.group("formula")
    counts: Counter[str] = Counter()
    for element, count_text in re.findall(r"([A-Z][a-z]?)(\d*)", formula):
        counts[element] += coefficient * int(count_text or "1")
    return counts if counts else None


def _normalize_unit(value: str) -> str:
    return value.strip().lower()


def _normalize_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.strip().lower()).strip()


_UNICODE_FRACTIONS: dict[str, Decimal] = {
    "\u00bc": Decimal(1) / Decimal(4),
    "\u00bd": Decimal(1) / Decimal(2),
    "\u00be": Decimal(3) / Decimal(4),
    "\u2153": Decimal(1) / Decimal(3),
    "\u2154": Decimal(2) / Decimal(3),
    "\u215b": Decimal(1) / Decimal(8),
    "\u215c": Decimal(3) / Decimal(8),
    "\u215d": Decimal(5) / Decimal(8),
    "\u215e": Decimal(7) / Decimal(8),
}
