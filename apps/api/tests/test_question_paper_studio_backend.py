"""Exact Question Paper Studio blueprint contracts and persistence safeguards."""

from __future__ import annotations

import json
import uuid
from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from httpx import AsyncClient
from pydantic import ValidationError

from app.db.models.academic import AcademicYear, Class, Subject
from app.db.models.examination import ExamType
from app.db.models.question_paper import PaperStatus, QuestionPaper
from app.db.models.school import School
from app.db.models.user import User, UserRole
from app.modules.ai.endpoints.ai import _assert_studio_curriculum_posture
from app.modules.ai.gateway import LLMResult
from app.modules.ai.gateway.output_guard import sanitize_paper_sections
from app.modules.ai.schemas.question_paper import (
    GenerateRequest,
    QuestionPaperFeedbackRequest,
)
from app.modules.ai.services.paper_pdf import render_blueprint_html
from app.modules.ai.services.question_paper_service import (
    _normalize_custom_plan,
    _reject_unvalidated_blueprint_ids,
    _validate_grounded_blueprint_chapters,
    generate_paper,
    validate_exact_sections,
)
from tests.conftest import access_token_for, auth_headers

PLAN = [
    {
        "title": "Section A",
        "type": "mcq",
        "count": 2,
        "marks_per_q": 1,
        "instructions": "Choose the correct answer.",
    },
    {
        "title": "Section B",
        "type": "short",
        "count": 1,
        "marks_per_q": 2,
        "instructions": "Answer briefly.",
    },
]
SLOTS = [
    {"section_index": 0, "question_index": 0, "chapter": "Motion", "bloom": "Remember"},
    {"section_index": 0, "question_index": 1, "chapter": "Light", "bloom": "Understand"},
    {"section_index": 1, "question_index": 0, "chapter": "Motion", "bloom": "Apply"},
]
RAW_SECTIONS = [
    {
        "title": "AI title",
        "questions": [
            {
                "number": "x",
                "text": "What is speed?",
                "marks": 1,
                "type": "mcq",
                "options": ["A", "B", "C", "D"],
                "answer_key": "A",
                "chapter": "Wrong model chapter",
                "bloom": "Create",
            },
            {
                "number": "y",
                "text": "Which is a source of light?",
                "marks": 1,
                "type": "mcq",
                "options": ["Sun", "Moon", "Mirror", "Book"],
                "answer_key": "Sun",
            },
        ],
    },
    {
        "title": "AI title 2",
        "questions": [
            {
                "number": "z",
                "text": "Explain uniform motion.",
                "marks": 2,
                "type": "short",
                "answer_key": "Equal distances in equal intervals of time.",
            }
        ],
    },
]


def _request_payload() -> dict:
    return {
        "class_id": uuid.uuid4(),
        "subject_id": uuid.uuid4(),
        "total_marks": 4,
        "section_plan": [
            {
                "title": "Section A",
                "type": "mcq",
                "question_count": 2,
                "marks_per_question": 1,
            },
            {
                "title": "Section B",
                "type": "short",
                "question_count": 1,
                "marks_per_question": 2,
            },
        ],
        "blueprint_slots": [
            {**SLOTS[0], "bloom": "remember"},
            {**SLOTS[1], "bloom": "understand"},
            {**SLOTS[2], "bloom": "analyse"},
        ],
    }


def test_generate_request_accepts_exact_complete_blueprint() -> None:
    request = GenerateRequest(**_request_payload())
    assert sum(
        item.question_count * item.marks_per_question for item in request.section_plan or []
    ) == 4
    assert len(request.blueprint_slots or []) == 3
    assert [slot.bloom for slot in request.blueprint_slots or []] == [
        "Remember",
        "Understand",
        "Analyze",
    ]


def test_generate_request_uses_canonical_exam_type_and_bounded_exception_reason() -> None:
    payload = _request_payload()
    payload.update(
        exam_type="formative_assessment",
        ungrounded_acknowledged=True,
        ungrounded_reason="Approved pack is temporarily unavailable for this internal draft.",
    )
    request = GenerateRequest(**payload)
    assert request.exam_type == ExamType.FORMATIVE_ASSESSMENT
    assert request.ungrounded_reason == payload["ungrounded_reason"]

    payload["exam_type"] = "weekly_surprise"
    with pytest.raises(ValidationError):
        GenerateRequest(**payload)

    payload["exam_type"] = "unit_test"
    payload["ungrounded_reason"] = ""
    with pytest.raises(ValidationError, match="ungrounded_reason is required"):
        GenerateRequest(**payload)


def test_studio_ungrounded_exception_is_flagged_permissioned_and_acknowledged(
    monkeypatch,
) -> None:
    class_id = uuid.uuid4()
    payload = _request_payload()
    payload["class_id"] = class_id
    request = GenerateRequest(**payload)
    incharge = SimpleNamespace(
        can_generate_ungrounded_question_paper=lambda candidate: candidate == class_id
    )

    monkeypatch.setattr(
        "app.modules.ai.endpoints.ai.settings.QUESTION_PAPER_UNGROUNDED_ENABLED", False
    )
    with pytest.raises(HTTPException) as disabled:
        _assert_studio_curriculum_posture(request, incharge)
    assert disabled.value.status_code == 403

    monkeypatch.setattr(
        "app.modules.ai.endpoints.ai.settings.QUESTION_PAPER_UNGROUNDED_ENABLED", True
    )
    denied = SimpleNamespace(can_generate_ungrounded_question_paper=lambda _candidate: False)
    acknowledged_payload = {
        **payload,
        "ungrounded_acknowledged": True,
        "ungrounded_reason": "No approved pack exists; class incharge will review every item.",
    }
    acknowledged = GenerateRequest(**acknowledged_payload)
    with pytest.raises(HTTPException) as unauthorized:
        _assert_studio_curriculum_posture(acknowledged, denied)
    assert unauthorized.value.status_code == 403

    with pytest.raises(HTTPException) as missing_ack:
        _assert_studio_curriculum_posture(request, incharge)
    assert missing_ack.value.status_code == 422
    _assert_studio_curriculum_posture(acknowledged, incharge)


def test_generate_request_rejects_plan_total_mismatch() -> None:
    payload = _request_payload()
    payload["total_marks"] = 5
    with pytest.raises(ValidationError, match="section_plan totals 4 marks; expected 5"):
        GenerateRequest(**payload)


def test_generate_request_rejects_incomplete_or_duplicate_slots() -> None:
    payload = _request_payload()
    payload["blueprint_slots"] = [SLOTS[0], SLOTS[0], SLOTS[1]]
    with pytest.raises(ValidationError, match="duplicate question coordinates"):
        GenerateRequest(**payload)


def test_generate_request_rejects_unbounded_question_count() -> None:
    payload = _request_payload()
    payload["total_marks"] = 121
    payload["section_plan"] = [
        {
            "title": "Section A",
            "type": "mcq",
            "question_count": 60,
            "marks_per_question": 1,
        },
        {
            "title": "Section B",
            "type": "mcq",
            "question_count": 60,
            "marks_per_question": 1,
        },
        {
            "title": "Section C",
            "type": "mcq",
            "question_count": 1,
            "marks_per_question": 1,
        },
    ]
    payload["blueprint_slots"] = None
    with pytest.raises(ValidationError, match="at most 120 questions"):
        GenerateRequest(**payload)


def test_generate_request_rejects_plan_above_reliable_output_budget() -> None:
    payload = _request_payload()
    payload["total_marks"] = 30
    payload["section_plan"] = [
        {
            "title": "Extended responses",
            "type": "long",
            "question_count": 30,
            "marks_per_question": 1,
        }
    ]
    payload["blueprint_slots"] = None
    with pytest.raises(ValidationError, match="too large for one reliable generation"):
        GenerateRequest(**payload)

    with pytest.raises(ValueError, match="too large for one reliable generation"):
        _normalize_custom_plan(
            30,
            [
                {
                    "title": "Extended responses",
                    "type": "long",
                    "count": 30,
                    "marks_per_q": 1,
                }
            ],
        )


def test_question_paper_feedback_contract_is_bounded() -> None:
    feedback = QuestionPaperFeedbackRequest(rating="down", note="  Needs better balance.  ")
    assert feedback.rating == "down"
    assert feedback.note == "Needs better balance."
    with pytest.raises(ValidationError):
        QuestionPaperFeedbackRequest(rating="neutral")

    payload = _request_payload()
    payload["blueprint_slots"] = SLOTS[:-1]
    with pytest.raises(ValidationError, match="cover every planned question"):
        GenerateRequest(**payload)


def test_exact_validator_applies_authoritative_slot_metadata() -> None:
    slots = {
        (slot["section_index"], slot["question_index"]): {
            "chapter": slot["chapter"],
            "bloom": slot["bloom"],
        }
        for slot in SLOTS
    }
    sections = validate_exact_sections(RAW_SECTIONS, plan=PLAN, blueprint_slots=slots)
    assert sections[0]["title"] == "Section A"
    assert sections[0]["questions"][0]["number"] == "1"
    assert sections[0]["questions"][0]["chapter"] == "Motion"
    assert sections[0]["questions"][0]["bloom"] == "Remember"
    assert sections[1]["questions"][0]["number"] == "3"


@pytest.mark.parametrize(
    ("mutator", "message"),
    [
        (lambda sections: sections[0]["questions"].pop(), "has 1 questions; expected 2"),
        (
            lambda sections: sections[0]["questions"][0].update(marks=2),
            r"carries 2\.0 marks; expected 1",
        ),
        (
            lambda sections: sections[0]["questions"][0].update(options=["A", "B"]),
            "exactly four non-blank options",
        ),
        (
            lambda sections: sections[1]["questions"][0].update(answer_key=""),
            "has no answer key",
        ),
    ],
)
def test_exact_validator_fails_closed_on_model_drift(mutator, message: str) -> None:
    payload = json.loads(json.dumps(RAW_SECTIONS))
    mutator(payload)
    with pytest.raises(ValueError, match=message):
        validate_exact_sections(payload, plan=PLAN)


def test_output_guard_preserves_sanitized_chapter() -> None:
    chapter_id = uuid.uuid4()
    raw = [{
        "title": "S",
        "questions": [{
            "number": "1",
            "text": "Q?",
            "marks": 1,
            "type": "short",
            "chapter": "Motion <script>",
            "chapter_id": str(chapter_id),
        }],
    }]
    question = sanitize_paper_sections(raw)[0]["questions"][0]
    assert question["chapter"] == "Motion <script>"
    assert question["chapter_id"] == str(chapter_id)


def test_ungrounded_blueprint_cannot_claim_unvalidated_chapter_id() -> None:
    slots = {
        (0, 0): {
            "chapter_id": uuid.uuid4(),
            "chapter": "Caller-supplied chapter",
            "bloom": "Remember",
        }
    }
    with pytest.raises(ValueError, match="requires an approved curriculum pack"):
        _reject_unvalidated_blueprint_ids(slots)

    _reject_unvalidated_blueprint_ids(
        {(0, 0): {"chapter_id": None, "chapter": "Motion", "bloom": "Remember"}}
    )


@pytest.mark.asyncio
async def test_grounded_blueprint_is_bound_to_pack_chapter_ids() -> None:
    chapter_id = uuid.uuid4()
    chapter = SimpleNamespace(id=chapter_id, number="1", title="Motion")
    result = SimpleNamespace(
        scalars=lambda: SimpleNamespace(all=lambda: [chapter])
    )
    db = SimpleNamespace(execute=AsyncMock(return_value=result))
    slots = {
        (0, 0): {
            "chapter_id": chapter_id,
            "chapter": "Untrusted label",
            "bloom": "Remember",
        }
    }

    await _validate_grounded_blueprint_chapters(
        db,
        school_id=uuid.uuid4(),
        pack_id=uuid.uuid4(),
        slots=slots,
    )

    assert slots[(0, 0)]["chapter"] == "1. Motion"
    assert slots[(0, 0)]["chapter_id"] == chapter_id


@pytest.mark.asyncio
async def test_grounded_blueprint_rejects_foreign_chapter_id() -> None:
    result = SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: []))
    db = SimpleNamespace(execute=AsyncMock(return_value=result))
    slots = {
        (0, 0): {
            "chapter_id": uuid.uuid4(),
            "chapter": "Motion",
            "bloom": "Remember",
        }
    }

    with pytest.raises(ValueError, match="does not belong"):
        await _validate_grounded_blueprint_chapters(
            db,
            school_id=uuid.uuid4(),
            pack_id=uuid.uuid4(),
            slots=slots,
        )


async def _seed_scope(db):
    school = School(
        name="Studio School",
        code="STUDIO",
        tenant_slug="studio",
        board="CBSE",
        contact_email="studio@example.com",
        contact_phone="+910000000000",
        is_active=True,
    )
    db.add(school)
    await db.flush()
    academic_year = AcademicYear(
        school_id=school.id,
        year_label="2026-2027",
        start_date=date(2026, 6, 1),
        end_date=date(2027, 5, 31),
        is_active=True,
    )
    db.add(academic_year)
    await db.flush()
    school_class = Class(
        school_id=school.id,
        grade="6",
        section="A",
        academic_year_id=academic_year.id,
    )
    teacher = User(
        school_id=school.id,
        mobile="+910000000091",
        full_name="Studio Teacher",
        role=UserRole.TEACHER,
        is_active=True,
    )
    db.add_all([school_class, teacher])
    await db.flush()
    subject = Subject(school_id=school.id, name="Science", class_id=school_class.id)
    db.add(subject)
    await db.flush()
    return school, school_class, subject, teacher


@pytest.mark.asyncio
async def test_service_uses_exact_plan_and_teacher_blueprint(db_session, monkeypatch) -> None:
    school, school_class, subject, teacher = await _seed_scope(db_session)
    captured: dict[str, str] = {}

    async def _fake_llm(messages, **_kwargs):
        captured["prompt"] = "\n".join(message.content for message in messages)
        return LLMResult(
            text=json.dumps({"title": "Draft", "sections": RAW_SECTIONS}),
            provider="stub",
            model="studio-test",
            tokens_in=10,
            tokens_out=20,
            latency_ms=1,
        )

    monkeypatch.setattr(
        "app.modules.ai.services.question_paper_service.generate_llm", _fake_llm
    )
    paper = await generate_paper(
        db_session,
        school_id=school.id,
        created_by=teacher.id,
        class_id=school_class.id,
        subject_id=subject.id,
        topics=["Motion", "Light"],
        total_marks=4,
        duration_minutes=30,
        difficulty="balanced",
        exam_type=ExamType.FORMATIVE_ASSESSMENT,
        ungrounded_reason="Internal manual-review exception for the focused service test.",
        credits_charged=0,
        section_plan=PLAN,
        blueprint_slots=SLOTS,
    )
    assert paper.status == PaperStatus.DRAFT
    assert paper.exam_type == ExamType.FORMATIVE_ASSESSMENT
    assert paper.ungrounded_reason == (
        "Internal manual-review exception for the focused service test."
    )
    assert float(paper.total_marks) == 4
    assert paper.sections[0]["questions"][0]["chapter"] == "Motion"
    assert paper.sections[0]["questions"][0]["bloom"] == "Remember"
    assert "chapter=Motion; Bloom=Remember" in captured["prompt"]
    assert "Assessment type: formative assessment" in captured["prompt"]


def test_blueprint_html_is_derived_from_saved_sections_and_escaped() -> None:
    paper = SimpleNamespace(
        board="CBSE",
        grade="6",
        subject_name="Science",
        title="Unit <Test>",
        total_marks=4,
        sections=validate_exact_sections(RAW_SECTIONS, plan=PLAN, blueprint_slots={
            (0, 0): {"chapter": "Motion", "bloom": "Remember"},
            (0, 1): {"chapter": "Light", "bloom": "Understand"},
            (1, 0): {"chapter": "Motion", "bloom": "Apply"},
        }),
    )
    rendered = render_blueprint_html(paper, school_name="School <One>")
    assert "Question Paper Blueprint" in rendered
    assert "Motion" in rendered and "Remember" in rendered
    assert "School &lt;One&gt;" in rendered
    assert "Unit &lt;Test&gt;" in rendered
    assert "Assessment: Unit Test" in rendered


@pytest.mark.asyncio
async def test_blueprint_pdf_endpoint_is_tenant_scoped(
    client: AsyncClient,
    db_session,
    test_school: School,
    test_class: Class,
    admin_user: User,
    monkeypatch,
) -> None:
    subject = Subject(school_id=test_school.id, name="Science", class_id=test_class.id)
    db_session.add(subject)
    await db_session.flush()
    paper = QuestionPaper(
        school_id=test_school.id,
        class_id=test_class.id,
        subject_id=subject.id,
        created_by=admin_user.id,
        title="Saved blueprint",
        board="CBSE",
        grade=test_class.grade,
        subject_name=subject.name,
        total_marks=4,
        sections=RAW_SECTIONS,
        status=PaperStatus.DRAFT,
    )
    db_session.add(paper)
    await db_session.flush()
    monkeypatch.setattr(
        "app.modules.ai.endpoints.ai.generate_blueprint_pdf",
        lambda *_args, **_kwargs: (b"%PDF-studio", "application/pdf"),
    )
    response = await client.get(
        f"/api/v1/ai/question-papers/{paper.id}/blueprint.pdf",
        headers=auth_headers(access_token_for(admin_user)),
    )
    assert response.status_code == 200
    assert response.content == b"%PDF-studio"
    assert response.headers["content-type"] == "application/pdf"

    other_school = School(
        name="Other",
        code="OTHER-STUDIO",
        tenant_slug="other-studio",
        board="CBSE",
        contact_email="other-studio@example.com",
        contact_phone="+910000000099",
        is_active=True,
    )
    db_session.add(other_school)
    await db_session.flush()
    foreign = QuestionPaper(
        school_id=other_school.id,
        class_id=test_class.id,
        subject_id=subject.id,
        created_by=admin_user.id,
        title="Foreign blueprint",
        board="CBSE",
        grade=test_class.grade,
        subject_name=subject.name,
        total_marks=4,
        sections=RAW_SECTIONS,
        status=PaperStatus.DRAFT,
    )
    db_session.add(foreign)
    await db_session.flush()
    denied = await client.get(
        f"/api/v1/ai/question-papers/{foreign.id}/blueprint.pdf",
        headers=auth_headers(access_token_for(admin_user)),
    )
    assert denied.status_code == 404
