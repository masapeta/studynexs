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


class PlannerDecision(BaseModel):
    # route classifies the execution domain (spec §2); action is what to do within it.
    route: Literal[
        "STRUCTURED", "DOCUMENT", "MIXED", "ACTION", "CLARIFICATION", "NAVIGATE"
    ] = "STRUCTURED"
    action: Literal["tool", "navigate", "clarify", "document", "mixed", "act", "compose"]
    tool: str | None = None
    params: dict[str, Any] = Field(default_factory=dict)
    navigate_to: str | None = None
    message: str | None = None
    # For MIXED: the document topic to retrieve after the structured step runs.
    document_query: str | None = None
    # For action='compose': a multi-operation plan (Phase 4). Validated before execution.
    plan: dict[str, Any] | None = None


def _catalog_text(tools: list[AssistantTool]) -> str:
    lines = []
    for t in tools:
        params = ", ".join(f"{k}: {v}" for k, v in t.params.items()) or "none"
        lines.append(f"- {t.name}: {t.description} | params: {params}")
    return "\n".join(lines)


def _system_prompt(tools: list[AssistantTool]) -> str:
    return (
        "You are the routing planner for StudyNexs, a school operations assistant.\n"
        "First CLASSIFY the request into a route, then decide the action. You do NOT\n"
        "answer with data yourself; you pick a governed tool, navigate, retrieve a\n"
        "document, or clarify.\n\n"
        "Routes:\n"
        "- STRUCTURED: live ERP data (students, attendance, fees, teachers, classes).\n"
        "- DOCUMENT: school policy / handbook / rules knowledge (unstructured docs).\n"
        "- MIXED: needs BOTH live data AND a policy document (e.g. 'is X below the\n"
        "  attendance policy threshold?'). Set tool+params for the data step AND\n"
        "  document_query for the policy step.\n"
        "- ACTION: the user asks to CHANGE data (mark absent, record payment, assign).\n"
        "- NAVIGATE: user just wants to open a section.\n"
        "- CLARIFICATION: unclear/unsupported.\n\n"
        "Available tools (STRUCTURED / the data step of MIXED):\n"
        f"{_catalog_text(tools)}\n\n"
        "Navigation targets (navigate_to = one key):\n"
        f"{', '.join(NAV_TARGETS)}\n\n"
        "Action field by route: STRUCTURED->'tool' for a SINGLE capability, or 'compose'\n"
        "for a question needing MULTIPLE capabilities combined; DOCUMENT->'document';\n"
        "MIXED->'mixed'; ACTION->'act'; NAVIGATE->'navigate'; CLARIFICATION->'clarify'.\n\n"
        "COMPOSITION (action='compose', route='STRUCTURED') — for questions that combine\n"
        "class/student metrics, e.g. 'classes below 75% attendance and their teachers',\n"
        "'students in 8A with attendance < 75% and fee dues > 10000', 'each class with\n"
        "student count, attendance and class teacher', 'top 5 students by fee due'.\n"
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
        "    'enrich_class_teacher' (adds subject_teachers to classes).\n"
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
        "Rules:\n"
        "- Extract numeric thresholds and class labels (e.g. 'class 10', '> 50%').\n"
        "- Extract a temporal token into the tool's 'time' param when the tool supports it\n"
        "  (today, this_month, last_month, current_academic_year, or {from,to}).\n"
        "- PRESERVE the user's actual relationship: 'all teachers and their classes' lists\n"
        "  everyone (omit class_label); do NOT narrow it to one class.\n"
        "- For DOCUMENT/MIXED set document_query to a SHORT topic phrase (e.g. "
        "'attendance policy'), NOT the full question. Keep message under 12 words.\n"
        "- Respond with ONLY a compact JSON object (no code fences, no prose) with keys:\n"
        "  route, action, tool, params, navigate_to, message, document_query. Keep it short.\n"
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


async def plan(
    text: str,
    *,
    tools: list[AssistantTool],
    history: list[dict[str, str]] | None = None,
) -> PlannerDecision:
    """Ask the LLM to choose a governed tool + params. Falls back to 'clarify'."""
    messages: list[LLMMessage] = [LLMMessage(role="system", content=_system_prompt(tools))]
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
