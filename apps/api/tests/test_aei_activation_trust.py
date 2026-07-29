from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.examinations.services.aei_activation_trust import (
    build_activation_trust_evidence,
    observe_activation_trust_suggestions,
    validate_and_merge_manual_review_acknowledgements,
)
from tests.conftest import access_token_for, auth_headers
from tests.test_answer_sheet_eval import _seed_eval_fixture


def test_activation_trust_evidence_counts_supported_and_review_required_cases():
    suggestions = {
        "1": {
            "marks_suggested": 2,
            "max_marks": 2,
            "method": "aei_v1_math_normalization",
            "manual_review_required": False,
            "capability_mode": "supported",
        },
        "2": {
            "marks_suggested": 0,
            "max_marks": 2,
            "method": "heuristic_fallback",
            "manual_review_required": True,
            "manual_review_reason": "Low confidence.",
            "capability_mode": "manual_review",
            "aei_v1_review_policy": {"method": "aei_v1_review_policy"},
        },
    }

    evidence = build_activation_trust_evidence(
        suggestions=suggestions,
        teacher_overrides={
            "2": {
                "aei_v1_manual_review_acknowledgement": {
                    "acknowledged": True,
                    "action": "accepted",
                }
            }
        },
        manual_review_acknowledgement_required=True,
    )

    assert evidence["manual_review_required_count"] == 1
    assert evidence["manual_review_acknowledged_count"] == 1
    assert evidence["manual_review_required_questions"] == ["2"]
    assert evidence["manual_review_acknowledged_questions"] == ["2"]
    assert evidence["capability_counts"]["math_normalization"] == 1
    assert evidence["capability_counts"]["review_policy"] == 1
    assert evidence["autonomous_grading"] is False
    assert evidence["approved_evidence_source"] == "teacher_decision"


def test_manual_review_acknowledgement_missing_blocks_when_enforced():
    with pytest.raises(ValueError, match="Teacher review acknowledgement required for Q1"):
        validate_and_merge_manual_review_acknowledgements(
            suggestions={
                "1": {
                    "marks_suggested": 0,
                    "manual_review_required": True,
                    "manual_review_reason": "OCR confidence is low.",
                }
            },
            teacher_overrides={},
            manual_review_acknowledgements={},
            reviewer_identifier="teacher-1",
            review_timestamp=datetime(2026, 7, 29, tzinfo=UTC),
        )


def test_manual_review_acknowledgement_merges_into_existing_overrides():
    merged = validate_and_merge_manual_review_acknowledgements(
        suggestions={
            "1": {
                "marks_suggested": 0,
                "manual_review_required": True,
                "manual_review_reason": "Checklist-only.",
            }
        },
        teacher_overrides={"1": {"marks": 1, "reason": "Teacher confirmed one label."}},
        manual_review_acknowledgements={"1": {"acknowledged": True, "action": "adjusted"}},
        reviewer_identifier="teacher-1",
        review_timestamp=datetime(2026, 7, 29, tzinfo=UTC),
    )

    ack = merged["1"]["aei_v1_manual_review_acknowledgement"]
    assert ack["method"] == "aei_v1_manual_review_acknowledgement"
    assert ack["acknowledged"] is True
    assert ack["action"] == "adjusted"
    assert ack["manual_review_required"] is True
    assert ack["manual_review_reason"] == "Checklist-only."
    assert ack["override_applied"] is True


def test_activation_trust_observer_is_noop_when_disabled():
    assert observe_activation_trust_suggestions(enabled=False, suggestions={}) is None


@pytest.mark.asyncio
async def test_manual_review_ack_gate_blocks_silent_approval_when_enabled(
    client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch,
):
    fx = await _seed_eval_fixture(db_session)
    fx["subject"].name = "Hindi"
    fx["paper"].subject_name = "Hindi"
    await db_session.flush()

    for path in (
        "app.modules.examinations.services.answer_sheet_eval_service.settings",
        "app.modules.examinations.endpoints.evaluation.settings",
    ):
        monkeypatch.setattr(f"{path}.AEI_V1_LANGUAGE_OCR_ASSIST_ENABLED", True)
        monkeypatch.setattr(f"{path}.AEI_V1_REVIEW_POLICY_ENABLED", True)
        monkeypatch.setattr(f"{path}.AEI_V1_EVIDENCE_LEDGER_METADATA_ENABLED", True)
        monkeypatch.setattr(f"{path}.AEI_V1_MANUAL_REVIEW_ACK_REQUIRED", True)

    token = access_token_for(fx["incharge"])
    resp = await client.post(
        f"/api/v1/exams/{fx['exam'].id}/evaluations",
        headers=auth_headers(token),
        json={
            "student_id": str(fx["student"].id),
            "student_answers": {
                "1": "uttar",
                "2": "B",
                "3": "answer in Hindi",
            },
        },
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()["data"]
    activation = data["evidence_ledger"]["aei_v1_activation_trust"]
    assert activation["manual_review_acknowledgement_required"] is True
    manual_review_qnos = activation["manual_review_required_questions"]
    assert manual_review_qnos

    missing = await client.post(
        f"/api/v1/exams/evaluations/{data['id']}/approve",
        headers=auth_headers(token),
        json={},
    )
    assert missing.status_code == 400
    assert "Teacher review acknowledgement required" in missing.text

    acknowledgements = {
        qno: {"acknowledged": True, "action": "accepted"} for qno in manual_review_qnos
    }
    approved = await client.post(
        f"/api/v1/exams/evaluations/{data['id']}/approve",
        headers=auth_headers(token),
        json={"manual_review_acknowledgements": acknowledgements},
    )
    assert approved.status_code == 200, approved.text
    approved_data = approved.json()["data"]
    assert approved_data["status"] == "approved"
    for qno in manual_review_qnos:
        ack = approved_data["teacher_overrides"][qno][
            "aei_v1_manual_review_acknowledgement"
        ]
        assert ack["acknowledged"] is True
        assert ack["method"] == "aei_v1_manual_review_acknowledgement"


@pytest.mark.asyncio
async def test_manual_review_ack_gate_off_preserves_approval_behavior(
    client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch,
):
    fx = await _seed_eval_fixture(db_session)
    fx["subject"].name = "Hindi"
    fx["paper"].subject_name = "Hindi"
    await db_session.flush()

    monkeypatch.setattr(
        "app.modules.examinations.services.answer_sheet_eval_service"
        ".settings.AEI_V1_LANGUAGE_OCR_ASSIST_ENABLED",
        True,
    )
    monkeypatch.setattr(
        "app.modules.examinations.services.answer_sheet_eval_service"
        ".settings.AEI_V1_MANUAL_REVIEW_ACK_REQUIRED",
        False,
    )

    token = access_token_for(fx["incharge"])
    resp = await client.post(
        f"/api/v1/exams/{fx['exam'].id}/evaluations",
        headers=auth_headers(token),
        json={
            "student_id": str(fx["student"].id),
            "student_answers": {"1": "uttar", "2": "B", "3": "answer"},
        },
    )
    assert resp.status_code == 201, resp.text

    approved = await client.post(
        f"/api/v1/exams/evaluations/{resp.json()['data']['id']}/approve",
        headers=auth_headers(token),
        json={},
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["data"]["status"] == "approved"
