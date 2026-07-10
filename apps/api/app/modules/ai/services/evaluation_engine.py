"""Assessment Intelligence — the shared marking engine (rubric-per-criterion).

The marking counterpart to ``question_paper_service``'s grounded generation. Given a batch of
subjective questions (model answer + student answer + max marks) and optional cited curriculum
context, it asks the LLM — through the shared, provider-agnostic gateway ONLY (never a provider
SDK) — to decompose each model answer into weighted criteria, award partial credit per criterion,
name the concepts the student missed, and write short constructive feedback with a confidence
score and citations.

It returns *suggestions*: it NEVER finalizes or publishes marks. The teacher is the final
authority and reviews/overrides every result (CLAUDE.md §40.3–§40.5, §109). Objective grading is
deterministic key-matching and never comes here (DECISION_LOG §3.6).

# SECURITY-REVIEW: the prompt embeds student answers (external input, already sanitized at the
# EvaluationCreate boundary) and the LLM's JSON response is parsed and then defensively clamped —
# every numeric field is bounded to [0, max] and strings are length-capped before it reaches a
# mark. A malicious/garbled model reply cannot award out-of-range marks or inject unbounded data.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

import structlog

from app.modules.ai.gateway import LLMMessage, LLMResult, generate_llm

logger = structlog.get_logger()

_MAX_CRITERIA = 8
_MAX_MISSING = 10
_MAX_CITATIONS = 8
_DEFAULT_CONFIDENCE = 0.6
_EVAL_MAX_TOKENS = 4000
# Low temperature: marking must be consistent across students, not creative.
_EVAL_TEMPERATURE = 0.1


@dataclass
class GroundingContext:
    """Optional curriculum context for grounded marking.

    Deliberately self-contained: when a shared retrieval/RAG layer lands it can emit this same
    shape (or a thin adapter can convert to it), so the engine takes on no dependency it does not
    yet need. Until then callers pass ``None`` and marking runs on the answer key alone — curriculum
    grounding only ever *improves* a suggestion, it never gates whether a paper can be marked.
    """

    context_text: str = ""
    chunk_count: int = 0

    @property
    def is_empty(self) -> bool:
        return self.chunk_count <= 0 or not self.context_text.strip()


@dataclass
class SubjectiveItem:
    """One subjective question to mark."""

    number: str
    question_text: str
    answer_key: str
    max_marks: float
    student_answer: str
    topic: str | None = None
    acceptable_answers: list[str] | None = None


def _round2(value: float) -> float:
    return round(float(value), 2)


def _clamp(value: object, lo: float, hi: float) -> float:
    try:
        v = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return lo
    if v != v:  # NaN
        return lo
    return max(lo, min(hi, v))


def _sanitize_criteria(raw: object, *, max_marks: float) -> list[dict]:
    """Bound each criterion: awarded ∈ [0, its max_points], max_points ∈ [0, question max]."""
    out: list[dict] = []
    if not isinstance(raw, list):
        return out
    for c in raw[:_MAX_CRITERIA]:
        if not isinstance(c, dict):
            continue
        name = str(c.get("criterion") or c.get("name") or "").strip()[:200]
        if not name:
            continue
        max_points = _clamp(c.get("max_points", 0), 0, max_marks)
        ceiling = max_points if max_points > 0 else max_marks
        awarded = _clamp(c.get("awarded_points", 0), 0, ceiling)
        met = bool(c.get("met", max_points > 0 and awarded >= max_points))
        out.append(
            {
                "criterion": name,
                "max_points": _round2(max_points),
                "awarded_points": _round2(awarded),
                "met": met,
                "comment": str(c.get("comment") or "").strip()[:300],
            }
        )
    return out


def _sanitize_citations(raw: object) -> list[int]:
    out: list[int] = []
    seen: set[int] = set()
    if not isinstance(raw, list):
        return out
    for n in raw[: _MAX_CITATIONS * 2]:
        try:
            i = int(n)
        except (TypeError, ValueError):
            continue
        if i >= 1 and i not in seen:
            seen.add(i)
            out.append(i)
        if len(out) >= _MAX_CITATIONS:
            break
    return out


def sanitize_evaluation(raw: dict, *, max_marks: float) -> dict:
    """Turn one raw LLM evaluation into a bounded, trustworthy suggestion.

    The rubric criteria are authoritative: when present, the suggested mark is the sum of the
    awarded criterion points (clamped to the question maximum), so the number always reconciles
    with the shown breakdown. Missing criteria fall back to the model's own ``marks_suggested``.
    """
    criteria = _sanitize_criteria(raw.get("criteria"), max_marks=max_marks)
    if criteria:
        marks = _clamp(sum(c["awarded_points"] for c in criteria), 0, max_marks)
    else:
        marks = _clamp(raw.get("marks_suggested", 0), 0, max_marks)

    missing: list[str] = []
    for m in (raw.get("missing_concepts") or [])[:_MAX_MISSING]:
        s = str(m).strip()[:120]
        if s:
            missing.append(s)

    return {
        "marks_suggested": _round2(marks),
        "feedback": str(raw.get("feedback") or "").strip()[:1000]
        or "Reviewed against the model answer.",
        "confidence": _round2(_clamp(raw.get("confidence", _DEFAULT_CONFIDENCE), 0, 1)),
        "criteria": criteria,
        "missing_concepts": missing,
        "citations": _sanitize_citations(raw.get("citations")),
        "method": "llm_rubric",
    }


def _build_messages(
    *,
    items: list[SubjectiveItem],
    grounding: GroundingContext | None,
    board: str,
    grade: str,
    subject: str,
) -> list[LLMMessage]:
    grounded = bool(grounding and not grounding.is_empty)
    context_block = ""
    cite_field = ""
    cite_instruction = ""
    if grounded:
        context_block = (
            f"CURRICULUM CONTEXT (numbered sources 1..{grounding.chunk_count} — cite the source "
            f"number(s) when a mark depends on a syllabus concept):\n{grounding.context_text}\n\n"
        )
        cite_field = ', "citations": [int]'
        cite_instruction = (
            " Add a \"citations\" array with the curriculum source numbers you relied on."
        )

    question_blocks: list[str] = []
    for it in items:
        accept = ""
        if it.acceptable_answers:
            accept = " Acceptable variations: " + "; ".join(
                str(a) for a in it.acceptable_answers
            ) + "."
        question_blocks.append(
            f"Question {it.number} (max_marks={_round2(it.max_marks)}, "
            f"topic={it.topic or 'n/a'}):\n"
            f"  Question: {it.question_text or '(text unavailable)'}\n"
            f"  Model answer / key: {it.answer_key or '(none provided)'}.{accept}\n"
            f"  Student answer: {it.student_answer or '(blank)'}"
        )
    questions_block = "\n\n".join(question_blocks)

    system = (
        f"You are an experienced, fair {board} board examiner marking {grade} {subject} answers. "
        f"For EACH question: break the model answer into 2-5 weighted marking criteria, then award "
        f"partial credit per criterion based ONLY on what the student's answer actually "
        f"demonstrates. Sum the awarded points into a suggested mark that never exceeds max_marks. "
        f"Be consistent and evidence-based; do not reward correct-sounding but irrelevant content, "
        f"and do not penalise a valid alternative method. Explain every awarded mark, list the key "
        f"concepts the student missed, and give brief constructive feedback. You are ASSISTING a "
        f"teacher who reviews and can override every mark — never inflate. Return JSON only."
    )
    user = (
        f"{context_block}"
        f"Mark these answers:\n\n{questions_block}\n\n"
        "Return JSON of EXACTLY this shape:\n"
        '{"evaluations": [{"number": str, "criteria": [{"criterion": str, "max_points": number, '
        '"awarded_points": number, "met": bool, "comment": str}], "marks_suggested": number, '
        '"missing_concepts": [str], "feedback": str, "confidence": number'
        f"{cite_field}"
        "}]}\n"
        "Rules: awarded_points is between 0 and that criterion's max_points; the sum of "
        "awarded_points must not exceed the question's max_marks; confidence is between 0 and 1; "
        "include one object per question, keyed by its number." + cite_instruction
    )
    return [LLMMessage("system", system), LLMMessage("user", user)]


async def evaluate_subjective(
    items: list[SubjectiveItem],
    *,
    board: str,
    grade: str,
    subject: str,
    grounding: GroundingContext | None = None,
    model: str | None = None,
) -> tuple[dict[str, dict], LLMResult]:
    """Mark a batch of subjective answers in ONE grounded gateway call.

    Returns ``({question_number: suggestion}, llm_result)``. Only questions the model actually
    returned are included — the caller heuristic-fills any it skipped. Raises ``ValueError`` when
    the reply is unreadable or covers nothing, so the caller can fall back rather than persist a
    bad mark. The ``llm_result`` is handed back for metering (cost is real even though the
    school-facing credit charge is per-evaluation, not per-question).
    """
    if not items:
        raise ValueError("No subjective questions to evaluate")

    messages = _build_messages(
        items=items, grounding=grounding, board=board, grade=grade, subject=subject
    )
    result = await generate_llm(
        messages,
        json_mode=True,
        max_tokens=_EVAL_MAX_TOKENS,
        temperature=_EVAL_TEMPERATURE,
        model=model,
        feature="answer_sheet_eval",
        caller="evaluate_subjective",
    )

    try:
        data = json.loads(result.text)
    except (json.JSONDecodeError, TypeError) as exc:
        logger.error("evaluation_parse_failed", raw=(result.text or "")[:400])
        raise ValueError("The AI returned an unreadable evaluation.") from exc

    by_number: dict[str, dict] = {}
    for ev in data.get("evaluations") or []:
        if not isinstance(ev, dict):
            continue
        num = str(ev.get("number") or "").strip()
        if num:
            by_number[num] = ev

    out: dict[str, dict] = {}
    for it in items:
        raw = by_number.get(it.number)
        if raw is not None:
            out[it.number] = sanitize_evaluation(raw, max_marks=it.max_marks)

    if not out:
        raise ValueError("The AI evaluation did not cover any question.")
    return out, result
