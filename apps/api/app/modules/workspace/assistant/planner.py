"""LLM planner for the agentic assistant.

The planner ONLY decides *how to ask the system*: it picks one governed tool and
extracts its parameters as JSON, or chooses to navigate / clarify. It never
produces academic data — the chosen tool's deterministic service does. Output is
validated against a schema before use.
"""

from __future__ import annotations

import json
from typing import Any, Literal

import structlog
from pydantic import BaseModel, Field, ValidationError

from app.modules.ai.gateway.base import LLMMessage
from app.modules.ai.gateway.invoke import generate_llm
from app.modules.workspace.assistant.tools import AssistantTool

logger = structlog.get_logger()

# Navigation targets the planner may choose (label -> route), resolved client-side too.
NAV_TARGETS: dict[str, str] = {
    "students": "/dashboard/students",
    "staff": "/dashboard/staff",
    "attendance": "/dashboard/attendance",
    "finance": "/dashboard/finance",
    "classes": "/dashboard/classes",
    "timetable": "/dashboard/timetable",
    "assessments": "/dashboard/teaching",
    "notices": "/dashboard/notices",
}


class TemporalIntent(BaseModel):
    """The user's temporal meaning, extracted SEPARATELY from tool/param selection.

    This is the semantic-integrity anchor (spec P0.1 §2, §3): temporal meaning must
    survive independently of which tool the planner picks, so a tool-selection slip
    that forgets ``params.time`` cannot silently erase a historical request. ``presence``
    is the user's temporal concept; ``time`` is the canonical token/dict describing the
    window (same syntax as a tool's ``time`` param).
    """

    presence: Literal[
        "NONE", "CURRENT", "PAST", "FUTURE", "PERIOD", "DATE_SPECIFIC"
    ] = "NONE"
    time: Any | None = None


class PlannerDecision(BaseModel):
    # route classifies the execution domain (spec §2); action is what to do within it.
    route: Literal[
        "STRUCTURED", "DOCUMENT", "MIXED", "ACTION", "CLARIFICATION", "NAVIGATE", "WORKFLOW"
    ] = "STRUCTURED"
    action: Literal[
        "tool", "navigate", "clarify", "document", "mixed", "act", "compose", "workflow"
    ]
    tool: str | None = None
    params: dict[str, Any] = Field(default_factory=dict)
    navigate_to: str | None = None
    message: str | None = None
    # For action='workflow': the WorkflowRegistry id (e.g. "question_paper"). The one canonical
    # way to identify a first-class workflow — NOT overloaded onto `tool` (a workflow is not a
    # capability). Resolved through the single workflow-resolution path in the service.
    workflow_id: str | None = None
    # For MIXED: the document topic to retrieve after the structured step runs.
    document_query: str | None = None
    # For action='compose': a multi-operation plan (Phase 4). Validated before execution.
    plan: dict[str, Any] | None = None
    # Temporal meaning, understood independently of tool selection (P0.1). The integrity
    # guard compares this against the plan's resolved temporality to catch silent drops.
    temporal: TemporalIntent = Field(default_factory=TemporalIntent)
    # Semantic intent, independent of tool naming (P1.2a). operation = the broad action
    # (collection/lookup/ranking/list/comparison); metric = the measure requested
    # (amount/receipt_count/percentage/count/marks). Enables metric-only follow-ups
    # ("how many receipts?") to keep domain+operation+time and change only the metric.
    operation: str | None = None
    metric: str | None = None


def _catalog_text(tools: list[AssistantTool]) -> str:
    """Prose + machine-readable contract metadata (requires / derivable) per capability.

    The structured `requires`/`derivable` come from the Capability Contract Registry so the
    planner can reason over relationships (a class is derivable from a student) rather than
    guessing from prose — the P1.5 fix for "who teaches the class ARM0242 is in?".
    """
    from app.modules.workspace.assistant.contracts import get_contract

    lines = []
    for t in tools:
        params = ", ".join(f"{k}: {v}" for k, v in t.params.items()) or "none"
        line = f"- {t.name}: {t.description} | params: {params}"
        c = get_contract(t.name)
        if c is not None:
            required = ", ".join(c.required_params) or "none"
            derivable = ", ".join(
                f"{p.name}<-{'/'.join(p.derive_from)}" for p in c.derivable_params()
            )
            meta = f" | requires: {required}"
            if derivable:
                meta += f" | derivable: {derivable}"
            line += meta
        lines.append(line)
    return "\n".join(lines)


def _school_terms() -> str:
    """The ACTIVE school's own terminology, so the planner resolves that school's words to the
    universal concept without any globally-hardcoded synonym list (spec §4). Blind: the term
    comes from the tenant's SchoolPack, not from the user's message."""
    from app.modules.workspace.assistant.school_pack import get_school_pack

    pack = get_school_pack()
    return (
        "THIS SCHOOL'S TERMINOLOGY (resolve these words to the universal concept; other\n"
        "schools may use different words — do not assume synonyms beyond this list):\n"
        f"  the teacher responsible for a class (class incharge) is called "
        f'"{pack.class_incharge_term}".\n\n'
    )


def _system_prompt(tools: list[AssistantTool]) -> str:
    return (
        "You are the routing planner for StudyNexs, a school operations assistant.\n"
        "First CLASSIFY the request into a route, then decide the action. You do NOT\n"
        "answer with data yourself; you pick a governed tool, navigate, retrieve a\n"
        "document, or clarify.\n\n"
        f"{_school_terms()}"
        "Routes:\n"
        "- STRUCTURED: live ERP data (students, attendance, fees, teachers, classes).\n"
        "- DOCUMENT: school policy / handbook / rules knowledge (unstructured docs).\n"
        "- MIXED: needs BOTH live data AND a policy document (e.g. 'is X below the\n"
        "  attendance policy threshold?'). Set tool+params for the data step AND\n"
        "  document_query for the policy step.\n"
        "- ACTION: the user asks to CHANGE data (mark absent, record payment, assign).\n"
        "- WORKFLOW: the user asks to run a multi-step academic process. Two exist:\n"
        "  (a) QUESTION PAPER — 'create/generate/prepare/make a question paper (or test/exam\n"
        "  paper) for a class & subject'; (b) ANSWER SHEET EVALUATION — 'evaluate/grade/mark\n"
        "  <student>'s answer sheet / paper for <exam>'. Either is WORKFLOW, not a data lookup.\n"
        "  Set workflow_id + params (see WORKFLOWS).\n"
        "- NAVIGATE: user just wants to open a section.\n"
        "- CLARIFICATION: unclear/unsupported.\n\n"
        "Available tools (STRUCTURED / the data step of MIXED):\n"
        f"{_catalog_text(tools)}\n\n"
        "Navigation targets (navigate_to = one key):\n"
        f"{', '.join(NAV_TARGETS)}\n\n"
        "Action field by route: STRUCTURED->'tool' for a SINGLE capability, or 'compose'\n"
        "for a question needing MULTIPLE capabilities combined; DOCUMENT->'document';\n"
        "MIXED->'mixed'; ACTION->'act'; WORKFLOW->'workflow'; NAVIGATE->'navigate';\n"
        "CLARIFICATION->'clarify'.\n\n"
        "WORKFLOW (action='workflow', route='WORKFLOW'):\n"
        "  question_paper — produce a paper. params: class_label ('8','8A','Class 8'), subject\n"
        "    (verbatim e.g. 'Science','Mathematics'), total_marks (int if stated e.g. '50\n"
        "    marks'), topics (list if named). Paraphrases: 'create a test paper', 'prepare an\n"
        "    exam paper', 'generate a Class 8 Science paper', 'make a paper from the curriculum'.\n"
        "  evaluate_answer_sheet — grade/mark a student's answer sheet. params: student (name or\n"
        "    admission no, e.g. 'ARM0218'), and if named the exam (exam title). Paraphrases:\n"
        "    'evaluate Ravi's answer sheet', 'grade ARM0218's paper for the Science unit test',\n"
        "    'mark this answer sheet'. Do NOT treat these as a data lookup or a capability.\n\n"
        "COMPOSITION (action='compose', route='STRUCTURED') — for questions that combine\n"
        "class/student metrics, e.g. 'classes below 75% attendance and their teachers',\n"
        "'students in 8A with attendance < 75% and fee dues > 10000', 'each class with\n"
        "student count, attendance and class incharge', 'top 5 students by fee due'.\n"
        "Set plan = an object with 'operations' (each: id, capability, depends_on[], params,\n"
        "filters[]) and 'output' (columns[], sort_field, sort_desc, limit, type).\n"
        "Composition capabilities:\n"
        "  SOURCES (exactly one, first): 'classes_overview' (rows: class_id, class_label,\n"
        "    student_count, attendance_pct, class_teacher; params.time optional) |\n"
        "    'class_students' (rows: student_id, name, admission_no, class_label;\n"
        "    params.class_label REQUIRED) | 'students_overview' (ALL students school-wide:\n"
        "    student_id, name, admission_no, class_label — use for 'top N students by fee/\n"
        "    attendance across the school').\n"
        "  ENRICHERS (depends_on the prior op): 'enrich_attendance' (adds attendance_pct to\n"
        "    students; params.time optional) | 'enrich_fees' (adds fee_due to students) |\n"
        "    'enrich_exam_average' (adds exam_average % to students) | 'enrich_class_teacher'\n"
        "    (adds subject_teachers to classes).\n"
        "  'filter' (depends_on prior): filters[] each {field, op(<,<=,>,>=,==,!=), value}.\n"
        "Filters may also be attached to any op. Join is automatic by canonical id.\n"
        "Example: 'students in 8A below 75% attendance with dues > 10000' ->\n"
        '  operations: [{id:"s",capability:"class_students",params:{class_label:"8A"}},'
        '{id:"a",capability:"enrich_attendance",depends_on:["s"]},'
        '{id:"f",capability:"enrich_fees",depends_on:["a"]},'
        '{id:"flt",capability:"filter",depends_on:["f"],'
        'filters:[{field:"attendance_pct",op:"<",value:75},'
        '{field:"fee_due",op:">",value:10000}]}], '
        'output:{columns:["admission_no","name","attendance_pct","fee_due"]}.\n\n'
        "TEMPORAL MEANING (ALWAYS fill the 'temporal' object — this is separate from tool\n"
        "choice and MUST reflect the user's words even if the chosen tool has no time):\n"
        "  temporal.presence = one of NONE (no time mentioned), CURRENT (now/currently/\n"
        "    'is'/today's live state, AND an ongoing period that includes today: 'this\n"
        "    month'/'this week'/'this year'/'this term'/'so far'/'to date'/'this academic\n"
        "    year'), PAST (was/last month/last year/in August/previous year — a period that\n"
        "    ended before now), FUTURE (next term/upcoming), PERIOD (a span like\n"
        "    'between Aug 1 and Aug 31'), DATE_SPECIFIC (a single named date).\n"
        "  temporal.time = the SAME canonical token/dict you would put in a tool's 'time'\n"
        "    (today, this_month, this_year, current_academic_year, last_month, last_year,\n"
        "    previous_academic_year, {\"month\":\"august\"},\n"
        "    {\"from\":\"YYYY-MM-DD\",\"to\":\"YYYY-MM-DD\"}), or null when presence=NONE.\n"
        "  CRITICAL: if the user expressed a past/historical period ('was', 'last year',\n"
        "  'in August'), presence MUST be PAST (or PERIOD/DATE_SPECIFIC) — NEVER NONE and\n"
        "  NEVER CURRENT. A 'this <period>' that is still in progress is CURRENT, not PAST.\n"
        "  Do not drop the time just because you are unsure which tool fits.\n\n"
        "SEMANTIC INTENT (always set when action='tool'/'compose'): 'operation' = the broad\n"
        "action (collection, lookup, ranking, list, comparison, aggregation); 'metric' = the\n"
        "measure asked for (amount, receipt_count, percentage, count, marks, balance). E.g.\n"
        "'how much fee was collected' -> operation=collection, metric=amount; 'how many\n"
        "receipts' -> operation=collection, metric=receipt_count. On a follow-up that changes\n"
        "only the metric, keep the same tool and time and change 'metric'.\n\n"
        "RELATIONSHIP DERIVATION: a capability's 'requires' params may be 'derivable' from an\n"
        "entity the user names. If the user references a class INDIRECTLY through a student\n"
        "(e.g. 'the class <student> is in', '<student>'s class', 'his/her class'), pick the\n"
        "class capability and pass the STUDENT (student=<admission/name>) WITHOUT a class — the\n"
        "system derives the class from the student. Do NOT ask for the class and do NOT fall\n"
        "back to compose/guide when the class is derivable from a named student. Example: 'who\n"
        "teaches the class ARM0242 is in?' -> teachers_for_class, params {student:'ARM0242'}.\n\n"
        "Rules:\n"
        "- Extract numeric thresholds and class labels (e.g. 'class 10', '> 50%').\n"
        "- Exams/marks: 'marks of <student>' or 'how did X do in <subject>' -> student_marks;\n"
        "  'results / rank list / top N students in <class>' -> class_results (top/bottom+limit);\n"
        "  'top scorers in <subject> in <class>' -> subject_toppers. Extract subject names\n"
        "  verbatim (Mathematics, Science). NEVER claim pass/fail — the ERP has no pass mark.\n"
        "- Also copy temporal.time into the tool's 'time' param when the tool takes one; but\n"
        "  the 'temporal' object is authoritative and must always be set.\n"
        "- PRESERVE the user's actual relationship: 'all teachers and their classes' lists\n"
        "  everyone (omit class_label); do NOT narrow it to one class.\n"
        "- For DOCUMENT/MIXED set document_query to a SHORT topic phrase (e.g. "
        "'attendance policy'), NOT the full question. Keep message under 12 words.\n"
        "- Respond with ONLY a compact JSON object (no code fences, no prose) with keys:\n"
        "  route, action, tool, workflow_id, params, navigate_to, message, document_query,\n"
        "  temporal, operation, metric. Keep it short.\n"
        "- Never invent data or fields. Never include commentary outside the JSON."
    )


def _parse_decision(text: str) -> PlannerDecision | None:
    raw = text.strip()
    # Tolerate code fences or leading prose around the JSON object.
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        data = json.loads(raw[start : end + 1])
        return PlannerDecision.model_validate(data)
    except (json.JSONDecodeError, ValidationError):
        return None


def _prev_state_hint(prev_state: dict[str, Any] | None) -> str | None:
    """Tell the planner the previous turn's structured meaning so an elliptical follow-up
    can decide, per dimension, to keep or override it (spec §9). Deterministic merge is the
    backstop; this just improves the LLM's first proposal."""
    if not prev_state:
        return None
    ent = prev_state.get("entities") or {}
    ent_str = ", ".join(f"{k}={v}" for k, v in ent.items()) or "none"
    return (
        "CONVERSATION CONTEXT (previous turn's meaning — for elliptical follow-ups like "
        "'what about September?' / 'his fees' / 'what about 2B?'). If THIS turn does not "
        "restate a dimension, you MAY inherit it; if THIS turn changes a dimension, override "
        "it. Do NOT blindly copy everything.\n"
        f"  previous domain: {prev_state.get('domain')}\n"
        f"  previous capability: {prev_state.get('capability')}\n"
        f"  previous entities: {ent_str}\n"
        f"  previous subject: {prev_state.get('subject')}\n"
        f"  previous temporal: presence={prev_state.get('temporal_presence')} "
        f"time={prev_state.get('temporal_time')}\n"
        "IMPORTANT: if the previous temporal presence was PAST and this turn only names a "
        "new period (e.g. 'September'), keep presence=PAST with the new time. Never silently "
        "reset temporality to CURRENT/NONE on a follow-up."
    )


async def plan(
    text: str,
    *,
    tools: list[AssistantTool],
    history: list[dict[str, str]] | None = None,
    prev_state: dict[str, Any] | None = None,
) -> PlannerDecision:
    """Ask the LLM to choose a governed tool + params. Falls back to 'clarify'."""
    messages: list[LLMMessage] = [LLMMessage(role="system", content=_system_prompt(tools))]
    hint = _prev_state_hint(prev_state)
    if hint:
        messages.append(LLMMessage(role="system", content=hint))
    for turn in history or []:
        role = turn.get("role", "user")
        content = turn.get("text", "")
        if content:
            messages.append(LLMMessage(role=role, content=content))
    messages.append(LLMMessage(role="user", content=text))

    try:
        result = await generate_llm(
            messages,
            temperature=0.0,
            max_tokens=600,
            json_mode=True,
            feature="workspace_planner",
            caller="assistant.plan",
        )
    except Exception as exc:  # noqa: BLE001 — degrade to clarify, never crash the turn
        logger.warning("assistant_planner_llm_failed", error=str(exc))
        return PlannerDecision(action="clarify", message=None)

    decision = _parse_decision(result.text)
    if decision is None:
        logger.warning("assistant_planner_unparseable", text=result.text[:200])
        return PlannerDecision(action="clarify", message=None)

    # Guard: only allow tools the caller may use (structured + the data step of mixed).
    if decision.action in ("tool", "mixed"):
        allowed = {t.name for t in tools}
        if decision.tool not in allowed:
            if decision.action == "mixed":
                # No usable data tool → fall back to the document step alone.
                decision.action = "document"
            else:
                return PlannerDecision(action="clarify", message=None)
    return decision
