"""Deterministic e2e planner: dev-tier only, planner prompt only, real downstream governance."""
from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from app.core.config import Environment, Settings
from app.modules.ai.gateway import e2e_scripted
from app.modules.ai.gateway.base import LLMMessage
from app.modules.ai.gateway.e2e_scripted import E2EScriptedProvider, scripted_decision
from app.modules.workspace.assistant.planner import plan
from app.modules.workspace.assistant.tools import tools_for_role


def _dev(monkeypatch, *, env=Environment.DEVELOPMENT, tier="development"):
    if env == Environment.PRODUCTION:
        # Real production Settings refuse to boot without prod secrets; mirror its flags.
        from types import SimpleNamespace

        s = SimpleNamespace(is_development=False, deployment_tier=tier)
    else:
        s = Settings(ENVIRONMENT=env, DEPLOYMENT_TIER=tier)
    monkeypatch.setattr(e2e_scripted, "get_settings", lambda: s)


@pytest.mark.parametrize(
    "env,tier",
    [
        (Environment.DEVELOPMENT, "staging"),
        (Environment.DEVELOPMENT, "demo"),
        (Environment.DEVELOPMENT, "internal"),
        (Environment.DEVELOPMENT, "production"),
        (Environment.TESTING, "development"),
        (Environment.PRODUCTION, "development"),
    ],
)
def test_refused_outside_development(monkeypatch, env, tier):
    _dev(monkeypatch, env=env, tier=tier)
    with pytest.raises(RuntimeError, match="development tier"):
        E2EScriptedProvider()


@pytest.mark.parametrize("tier", ["staging", "demo", "production"])
def test_factory_refuses_scripted_on_non_dev_tiers(monkeypatch, tier):
    from app.modules.ai.gateway import factory

    _dev(monkeypatch, tier=tier)
    with pytest.raises(RuntimeError, match="development tier"):
        factory.get_provider("e2e_scripted")


def test_provider_selection_has_no_request_input():
    """Provider names come only from Settings; no request schema or endpoint carries one."""
    import inspect
    import pathlib

    from app.main import app

    for route in app.routes:
        body = getattr(route, "body_field", None)
        params = getattr(route, "dependant", None)
        names = set()
        if params is not None:
            names |= {p.name for p in params.query_params + params.header_params}
        if body is not None:
            ann = getattr(body.field_info, "annotation", None) or body.type_
            names |= set(getattr(ann, "model_fields", {}) or {})
        assert not names & {"provider", "provider_name", "ai_provider", "llm_provider"}, route.path
    app_dir = pathlib.Path(inspect.getfile(E2EScriptedProvider)).parents[3]
    callers = [
        p for p in app_dir.rglob("*.py")
        if "e2e_scripted" in p.read_text(encoding="utf-8") and p.name != "e2e_scripted.py"
    ]
    assert {p.name for p in callers} <= {"factory.py", "config.py"}, callers


def test_production_config_rejects_scripted_provider():
    with pytest.raises(ValidationError, match="e2e_scripted"):
        Settings(
            ENVIRONMENT=Environment.PRODUCTION, DEPLOYMENT_TIER="production", DEBUG=False,
            JWT_SECRET_KEY="production-jwt-secret-with-more-than-32-characters",
            WEBHOOK_SECRET="production-webhook-secret",
            ALLOWED_ORIGINS=["https://app.studynexs.com"], COOKIE_SECURE=True,
            REDIS_URL="rediss://redis.internal:6379/0", AI_DEFAULT_PROVIDER="e2e_scripted",
            AADHAAR_ENCRYPTION_KEYS=["k"],
        )


def test_script_maps_phrases():
    assert scripted_decision("Show my timetable")["navigate_to"] == "timetable"
    d = scripted_decision("students in 7-A please")
    assert d["tool"] == "class_roster" and d["params"] == {"class_label": "7-A"}
    assert scripted_decision("tell me a joke") is None


@pytest.mark.asyncio
async def test_only_planner_prompt_is_scripted(monkeypatch):
    _dev(monkeypatch)
    p = E2EScriptedProvider()
    r = await p.generate([LLMMessage("system", "You write remarks."),
                          LLMMessage("user", "Student: Ravi")], model="")
    assert r.provider == "stub"
    r = await p.generate([LLMMessage("system", "You are the routing planner for StudyNexs, x"),
                          LLMMessage("user", "show my timetable")], model="", json_mode=True)
    assert json.loads(r.text)["action"] == "navigate"


@pytest.mark.asyncio
async def test_role_tool_guard_still_applies(monkeypatch):
    """A scripted admin-only tool requested by a teacher is dropped to clarify by the real guard."""
    _dev(monkeypatch)
    provider = E2EScriptedProvider()

    async def _llm(messages, **_kw):
        return await provider.generate(messages, model="", json_mode=True)

    monkeypatch.setattr("app.modules.workspace.assistant.planner.generate_llm", _llm)
    teacher = await plan("what is the fee collection", tools=tools_for_role("teacher"))
    assert teacher.action == "clarify"
    admin = await plan("what is the fee collection", tools=tools_for_role("admin"))
    assert admin.action == "tool" and admin.tool == "fee_collection"
    unknown = await plan("tell me a joke", tools=tools_for_role("admin"))
    assert unknown.action == "clarify"
