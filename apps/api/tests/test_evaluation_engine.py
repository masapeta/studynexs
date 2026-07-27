"""Assessment Intelligence — grounded, rubric-per-criterion subjective marking (Batch 13).

Proves the shared marking engine and its wiring into answer-sheet evaluation, without live
providers (a monkeypatched gateway; stub embedder path not needed since the seeded paper has no
pack, so grounding is a no-op):

- the engine decomposes a model answer into weighted criteria and awards partial credit, and the
  suggested mark reconciles with the criteria (sum of awarded, clamped to max) — the model's own
  ``marks_suggested`` never overrides the breakdown;
- over-generous or garbage model output is clamped: a mark can never exceed max_marks, and a
  confidence is bounded to [0, 1];
- objective questions stay deterministic (key-match); only subjective ones reach the LLM;
- a provider failure degrades to the token-overlap heuristic per question instead of failing the
  whole sheet;
- HITL + metering hold: marks are DRAFT suggestions and one evaluation charges exactly one credit.
"""
import json
import uuid

import pytest
from sqlalchemy import select

from app.modules.ai.gateway import LLMResult
from app.modules.ai.services.evaluation_engine import (
    SubjectiveItem,
    evaluate_subjective,
    sanitize_evaluation,
)
from tests.conftest import access_token_for, auth_headers
from tests.test_answer_sheet_eval import _seed_eval_fixture

_ENGINE_LLM = "app.modules.ai.services.evaluation_engine.generate_llm"


def _fake_llm(payload: dict, flag: dict | None = None):
    async def _gen(*_args, **_kwargs):
        if flag is not None:
            flag["called"] = True
        return LLMResult(
            text=json.dumps(payload), provider="stub", model="stub-model",
            tokens_in=12, tokens_out=34, latency_ms=1,
        )

    return _gen


def _raising_llm():
    async def _gen(*_args, **_kwargs):
        raise RuntimeError("provider unavailable")

    return _gen


# ── Engine unit tests (no DB) ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_engine_awards_partial_credit_per_criterion(monkeypatch):
    """Criteria are authoritative: the mark is the sum of awarded points, not the model's number."""
    payload = {"evaluations": [{
        "number": "3",
        "criteria": [
            {"criterion": "plants make food", "max_points": 1.5, "awarded_points": 1.5,
             "met": True, "comment": "correct"},
            {"criterion": "uses sunlight / light energy", "max_points": 1.5, "awarded_points": 1.0,
             "met": False, "comment": "partial"},
        ],
        "marks_suggested": 99,  # deliberately bogus — the breakdown must win
        "missing_concepts": ["chlorophyll", "carbon dioxide"],
        "feedback": "Good start; mention chlorophyll.",
        "confidence": 0.8,
    }]}
    monkeypatch.setattr(_ENGINE_LLM, _fake_llm(payload))

    item = SubjectiveItem(
        number="3", question_text="Define photosynthesis.",
        answer_key="Plants make food using sunlight and chlorophyll.",
        max_marks=3, student_answer="plants make food with sunlight",
    )
    out, result = await evaluate_subjective([item], board="SSC", grade="10", subject="Science")

    assert result.provider == "stub"
    s = out["3"]
    assert s["method"] == "llm_rubric"
    assert s["marks_suggested"] == 2.5          # 1.5 + 1.0, NOT the bogus 99
    assert len(s["criteria"]) == 2
    assert s["missing_concepts"] == ["chlorophyll", "carbon dioxide"]
    assert s["confidence"] == 0.8


@pytest.mark.asyncio
async def test_engine_clamps_overaward_to_max(monkeypatch):
    payload = {"evaluations": [{
        "number": "1",
        "criteria": [
            {"criterion": "c1", "max_points": 5, "awarded_points": 5, "met": True},
            {"criterion": "c2", "max_points": 5, "awarded_points": 5, "met": True},
        ],
        "marks_suggested": 10, "feedback": "x", "confidence": 2.0,
    }]}
    monkeypatch.setattr(_ENGINE_LLM, _fake_llm(payload))

    item = SubjectiveItem(
        number="1", question_text="q", answer_key="k", max_marks=3, student_answer="a"
    )
    out, _ = await evaluate_subjective([item], board="SSC", grade="10", subject="Maths")

    s = out["1"]
    assert s["marks_suggested"] == 3.0
    assert s["confidence"] == 1.0
    assert all(c["max_points"] <= 3 for c in s["criteria"])


@pytest.mark.asyncio
async def test_engine_raises_on_unreadable_reply(monkeypatch):
    async def _bad(*_args, **_kwargs):
        return LLMResult(text="not json at all", provider="stub", model="m")

    monkeypatch.setattr(_ENGINE_LLM, _bad)
    item = SubjectiveItem(
        number="1", question_text="q", answer_key="k", max_marks=2, student_answer="a"
    )
    with pytest.raises(ValueError):
        await evaluate_subjective([item], board="SSC", grade="10", subject="Maths")


@pytest.mark.asyncio
async def test_engine_returns_only_covered_questions(monkeypatch):
    """A question the model skipped is omitted so the caller can heuristic-fill it."""
    payload = {"evaluations": [
        {"number": "1", "criteria": [], "marks_suggested": 1, "feedback": "ok", "confidence": 0.5},
    ]}
    monkeypatch.setattr(_ENGINE_LLM, _fake_llm(payload))
    items = [
        SubjectiveItem(
            number="1",
            question_text="q1",
            answer_key="k",
            max_marks=2,
            student_answer="a",
        ),
        SubjectiveItem(
            number="2",
            question_text="q2",
            answer_key="k",
            max_marks=2,
            student_answer="b",
        ),
    ]
    out, _ = await evaluate_subjective(items, board="SSC", grade="10", subject="Maths")
    assert set(out) == {"1"}


def test_sanitize_evaluation_bounds_everything():
    raw = {
        "criteria": [{"criterion": "c", "max_points": 99, "awarded_points": 99, "met": True}],
        "marks_suggested": 99,
        "missing_concepts": ["x"] * 50,
        "feedback": "f" * 5000,
        "confidence": -3,
        "citations": [1, "2", "junk", 0, -1, 3],
    }
    s = sanitize_evaluation(raw, max_marks=4)
    assert s["marks_suggested"] == 4.0
    assert s["confidence"] == 0.0
    assert len(s["missing_concepts"]) <= 10
    assert len(s["feedback"]) <= 1000
    assert s["citations"] == [1, 2, 3]


# ── Service integration (DB) ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_subjective_uses_engine_objective_stays_deterministic(
    client, db_session, monkeypatch
):
    fx = await _seed_eval_fixture(db_session)
    payload = {"evaluations": [{
        "number": "3",
        "criteria": [{"criterion": "photosynthesis basics", "max_points": 3,
                      "awarded_points": 2, "met": False, "comment": "partial"}],
        "marks_suggested": 2, "missing_concepts": ["chlorophyll"],
        "feedback": "Add chlorophyll.", "confidence": 0.7,
    }]}
    flag = {"called": False}
    monkeypatch.setattr(_ENGINE_LLM, _fake_llm(payload, flag))

    token = access_token_for(fx["incharge"])
    resp = await client.post(
        f"/api/v1/exams/{fx['exam'].id}/evaluations",
        headers=auth_headers(token),
        json={"student_id": str(fx["student"].id),
              "student_answers": {"1": "4", "2": "B", "3": "plants make food using sunlight"}},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()["data"]
    sug = data["ai_suggestions"]

    assert flag["called"] is True
    # Objective questions never touch the LLM.
    assert sug["1"]["method"] == "objective" and float(sug["1"]["marks_suggested"]) == 2
    assert sug["2"]["method"] == "objective" and float(sug["2"]["marks_suggested"]) == 1
    # Subjective marked by the engine, with a rubric breakdown and named gaps.
    assert sug["3"]["method"] == "llm_rubric"
    assert float(sug["3"]["marks_suggested"]) == 2
    assert sug["3"]["criteria"]
    assert "chlorophyll" in sug["3"]["missing_concepts"]
    # HITL — AI suggests, never publishes.
    assert data["status"] == "suggested"


@pytest.mark.asyncio
async def test_subjective_falls_back_to_heuristic_on_provider_failure(
    client, db_session, monkeypatch
):
    fx = await _seed_eval_fixture(db_session)
    monkeypatch.setattr(_ENGINE_LLM, _raising_llm())

    token = access_token_for(fx["incharge"])
    resp = await client.post(
        f"/api/v1/exams/{fx['exam'].id}/evaluations",
        headers=auth_headers(token),
        json={"student_id": str(fx["student"].id),
              "student_answers": {"1": "4", "2": "B", "3": "plants make food using sunlight"}},
    )
    assert resp.status_code == 201, resp.text
    sug = resp.json()["data"]["ai_suggestions"]
    assert sug["3"]["method"] == "heuristic_fallback"
    assert "marks_suggested" in sug["3"]
    # Objective grading is unaffected by the provider outage.
    assert sug["1"]["method"] == "objective"


@pytest.mark.asyncio
async def test_llm_eval_charges_exactly_one_credit(client, db_session, monkeypatch):
    from app.db.models.ai_usage import AIUsage
    from app.modules.examinations.services.answer_sheet_eval_service import AnswerSheetEvalService

    fx = await _seed_eval_fixture(db_session)
    payload = {"evaluations": [{"number": "3", "criteria": [], "marks_suggested": 2,
                                "feedback": "ok", "confidence": 0.7}]}
    monkeypatch.setattr(_ENGINE_LLM, _fake_llm(payload))

    token = access_token_for(fx["incharge"])
    resp = await client.post(
        f"/api/v1/exams/{fx['exam'].id}/evaluations",
        headers=auth_headers(token),
        json={"student_id": str(fx["student"].id),
              "student_answers": {"1": "4", "2": "B", "3": "answer"}},
    )
    assert resp.status_code == 201, resp.text
    eval_id = resp.json()["data"]["id"]

    # Re-running the evaluation must not charge a second credit.
    await AnswerSheetEvalService(db_session).execute_evaluation(
        uuid.UUID(eval_id), role="class_incharge"
    )
    charged = (
        await db_session.execute(
            select(AIUsage).where(
                AIUsage.ref_type == "answer_sheet_evaluation",
                AIUsage.ref_id == uuid.UUID(eval_id),
                AIUsage.credits_charged > 0,
            )
        )
    ).scalars().all()
    assert len(charged) == 1
