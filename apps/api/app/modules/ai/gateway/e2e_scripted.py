"""Deterministic planner provider for browser acceptance on disposable e2e tenants.

It answers ONLY the assistant routing-planner prompt, mapping fixed phrases to a planner JSON
decision. Everything downstream is unchanged and real: decision schema validation, the
per-role tool guard, capabilities, object authorization, role-denial rewrite, persistence and
the UI. It never fabricates data or success; a phrase it doesn't know yields an unparseable
reply, which the planner turns into its normal "clarify" path. Development tier only.
"""
from __future__ import annotations

import json
import re

from app.core.config import get_settings
from app.modules.ai.gateway.base import LLMMessage, LLMProvider, LLMResult
from app.modules.ai.gateway.stub import StubProvider

_PLANNER_MARKER = "You are the routing planner for StudyNexs"

# (pattern on the user's text, planner decision). First match wins.
_SCRIPT: list[tuple[re.Pattern[str], dict]] = [
    (re.compile(r"\btimetable\b", re.I),
     {"route": "NAVIGATE", "action": "navigate", "navigate_to": "timetable"}),
    (re.compile(r"\bschool overview\b", re.I),
     {"route": "STRUCTURED", "action": "tool", "tool": "school_overview", "params": {}}),
    (re.compile(r"\bstaff directory\b", re.I),
     {"route": "STRUCTURED", "action": "tool", "tool": "staff_directory", "params": {}}),
    (re.compile(r"\bfee collection\b", re.I),
     {"route": "STRUCTURED", "action": "tool", "tool": "fee_collection", "params": {}}),
    (re.compile(r"\bstudents in (?:class )?(?P<cls>[0-9]+\s*-?\s*[A-Z])\b", re.I),
     {"route": "STRUCTURED", "action": "tool", "tool": "class_roster",
      "params": {"class_label": "{cls}"}}),
    (re.compile(r"\battendance today in (?:class )?(?P<cls>[0-9]+\s*-?\s*[A-Z])\b", re.I),
     {"route": "STRUCTURED", "action": "tool", "tool": "class_attendance_today",
      "params": {"class_label": "{cls}"}}),
    (re.compile(r"\bprofile of (?P<who>[A-Za-z0-9]+)\b", re.I),
     {"route": "STRUCTURED", "action": "tool", "tool": "student_profile",
      "params": {"student": "{who}"}}),
    (re.compile(r"\battendance of (?P<who>[A-Za-z0-9]+)\b", re.I),
     {"route": "STRUCTURED", "action": "tool", "tool": "student_attendance",
      "params": {"student": "{who}"}}),
    # Elliptical follow-up: names no student, so the real merge must inherit it.
    (re.compile(r"\b(?:and |what about )?(?:his|her) marks\b", re.I),
     {"route": "STRUCTURED", "action": "tool", "tool": "student_marks", "params": {}}),
    (re.compile(r"\bclass results (?:for |of )?(?P<cls>[0-9]+\s*-?\s*[A-Z])\b", re.I),
     {"route": "STRUCTURED", "action": "tool", "tool": "class_results",
      "params": {"class_label": "{cls}"}}),
    (re.compile(r"\blow attendance\b", re.I),
     {"route": "STRUCTURED", "action": "tool", "tool": "low_attendance_students",
      "params": {"below_percent": 75}}),
    (re.compile(r"\bmy children\b", re.I),
     {"route": "STRUCTURED", "action": "tool", "tool": "my_children_overview", "params": {}}),
    (re.compile(r"\bchild'?s? attendance\b", re.I),
     {"route": "STRUCTURED", "action": "tool", "tool": "my_child_attendance", "params": {}}),
    (re.compile(r"\bchild'?s? progress\b", re.I),
     {"route": "STRUCTURED", "action": "tool", "tool": "my_child_progress", "params": {}}),
    (re.compile(r"\bmy daily plan\b", re.I),
     {"route": "STRUCTURED", "action": "tool", "tool": "my_daily_plan", "params": {}}),
    (re.compile(r"\bmy weak topics\b", re.I),
     {"route": "STRUCTURED", "action": "tool", "tool": "my_weak_topics", "params": {}}),
    (re.compile(r"\bmy lesson\b", re.I),
     {"route": "STRUCTURED", "action": "tool", "tool": "my_lesson", "params": {}}),
]


def _user_text(messages: list[LLMMessage]) -> str:
    return next((m.content for m in reversed(messages) if m.role == "user"), "")


def scripted_decision(text: str) -> dict | None:
    for pattern, decision in _SCRIPT:
        m = pattern.search(text)
        if not m:
            continue
        params = {
            k: (v.format(**{g: (m.group(g) or "").replace(" ", "") for g in m.groupdict()})
                if isinstance(v, str) else v)
            for k, v in decision.get("params", {}).items()
        }
        return {**decision, "params": params}
    return None


class E2EScriptedProvider(LLMProvider):
    name = "e2e_scripted"

    def __init__(self) -> None:
        s = get_settings()
        if not s.is_development or s.deployment_tier != "development":
            raise RuntimeError("e2e_scripted provider is limited to the development tier")
        self._fallback = StubProvider()

    async def generate(
        self,
        messages: list[LLMMessage],
        *,
        model: str,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        json_mode: bool = False,
    ) -> LLMResult:
        is_planner = bool(messages) and messages[0].content.startswith(_PLANNER_MARKER)
        if not is_planner:
            return await self._fallback.generate(
                messages, model=model, temperature=temperature,
                max_tokens=max_tokens, json_mode=json_mode,
            )
        decision = scripted_decision(_user_text(messages))
        text = json.dumps(decision) if decision else "unrecognised"
        return LLMResult(
            text=text, provider=self.name, model=model or "e2e-scripted",
            tokens_in=0, tokens_out=0, latency_ms=1,
        )
