"""Tests — flags review API: approve (mocked LLM), narrative edit, notify, gates."""

from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from app.db.models.answer_sheet_evaluation import EVAL_STATUS_APPROVED, AnswerSheetEvaluation
from app.db.models.curriculum_pack import (
    CurriculumChapter,
    CurriculumPack,
    CurriculumTopic,
    PackStatus,
)
from app.db.models.examination import Exam
from app.db.models.knowledge_graph import ConceptSource, CurriculumConcept
from app.db.models.mastery import MasteryFlag
from app.db.models.notification import Notification
from app.db.models.question_paper import PaperStatus, QuestionPaper
from tests.conftest import auth_headers, get_auth_token
from tests.test_mastery_flags import _seed_flagging_scenario


class _FakeResult:
    text = "Ravi has found Algebra challenging recently. Practising two problems daily will help."
    model = "fake-model"
    provider = "fake"
    tokens_in = 10
    tokens_out = 20
    latency_ms = 5


class _FakeProvider:
    name = "fake"

    async def generate(self, messages, **kwargs):
        return _FakeResult()


@pytest.fixture(autouse=True)
def mock_llm(monkeypatch):
    """No real LLM calls in tests — patch generate_llm + metering."""
    import app.modules.mastery.services.narrative_service as ns

    async def fake_record_usage(db, **kwargs):
        return None

    async def fake_generate_llm(*_args, **_kwargs):
        return _FakeResult()

    monkeypatch.setattr(ns, "generate_llm", fake_generate_llm)
    monkeypatch.setattr(ns, "record_usage", fake_record_usage)


async def _flag_of(db_session, student_id):
    return (
        await db_session.execute(select(MasteryFlag).where(MasteryFlag.student_id == student_id))
    ).scalar_one()


async def _out_of_scope_maths_flag_and_science_teacher_token(
    client,
    db_session,
    test_school,
    test_class,
    student_user,
    teacher_user,
):
    """Maths weakness flag + teacher who only teaches Science in the same class."""
    from app.db.models.academic import Subject, TeacherSubjectMapping

    weak, _maths_subject, _ = await _seed_flagging_scenario(
        client, db_session, test_school, test_class, student_user
    )
    flag = await _flag_of(db_session, weak.id)
    science = Subject(school_id=test_school.id, class_id=test_class.id, name="Science", code="SCI")
    db_session.add(science)
    await db_session.flush()
    db_session.add(
        TeacherSubjectMapping(
            school_id=test_school.id,
            teacher_id=teacher_user.id,
            subject_id=science.id,
            class_id=test_class.id,
            is_primary=True,
        )
    )
    await db_session.flush()
    token = await get_auth_token(client, "test_teacher", "Teacher@123")
    return flag, token


@pytest.mark.asyncio
async def test_approve_drafts_narrative_then_edit_then_notify(
    client,
    admin_user,
    student_user,
    parent_user,
    test_school,
    test_class,
    db_session,
):
    weak, subject, token = await _seed_flagging_scenario(
        client, db_session, test_school, test_class, student_user
    )
    flag = await _flag_of(db_session, weak.id)

    # Notify before approval → 409.
    resp = await client.post(f"/api/v1/mastery/flags/{flag.id}/notify", headers=auth_headers(token))
    assert resp.status_code == 409

    # Approve → LLM draft attached, status APPROVED.
    resp = await client.post(
        f"/api/v1/mastery/flags/{flag.id}/approve", headers=auth_headers(token)
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["status"] == "approved"
    assert "Algebra" in data["narrative"]
    assert data["ai_model"] == "fake-model"

    # Double-approve → 409.
    resp = await client.post(
        f"/api/v1/mastery/flags/{flag.id}/approve", headers=auth_headers(token)
    )
    assert resp.status_code == 409

    # Teacher edits the note.
    resp = await client.put(
        f"/api/v1/mastery/flags/{flag.id}/narrative",
        headers=auth_headers(token),
        json={"narrative": "Edited note for the parent."},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["narrative"] == "Edited note for the parent."

    # Notify → one in-app notification per linked parent user.
    resp = await client.post(f"/api/v1/mastery/flags/{flag.id}/notify", headers=auth_headers(token))
    assert resp.status_code == 200, resp.text
    body = resp.json()["data"]
    assert body["parents_notified"] == 1  # parent_user fixture links one parent
    assert body["flag"]["status"] == "notified"

    notifs = (
        (
            await db_session.execute(
                select(Notification).where(Notification.user_id == parent_user.id)
            )
        )
        .scalars()
        .all()
    )
    assert len(notifs) == 1
    assert notifs[0].body == "Edited note for the parent."
    assert "Algebra" in notifs[0].title


@pytest.mark.asyncio
async def test_flags_list_and_role_gates(
    client,
    admin_user,
    student_user,
    parent_user,
    test_school,
    test_class,
    db_session,
):
    weak, subject, token = await _seed_flagging_scenario(
        client, db_session, test_school, test_class, student_user
    )

    resp = await client.get(
        "/api/v1/mastery/flags?status=pending_review", headers=auth_headers(token)
    )
    assert resp.status_code == 200
    flags = resp.json()["data"]
    assert len(flags) == 1
    assert flags[0]["student_name"]
    assert flags[0]["class_name"]
    assert flags[0]["evidence"]["history"]

    # Students and parents cannot touch the review pipeline.
    for username, password in (("test_student", "Student@123"), ("test_parent", "Parent@123")):
        bad_token = await get_auth_token(client, username, password)
        resp = await client.get("/api/v1/mastery/flags", headers=auth_headers(bad_token))
        assert resp.status_code == 403, username
        resp = await client.post(
            f"/api/v1/mastery/flags/{flags[0]['id']}/approve", headers=auth_headers(bad_token)
        )
        assert resp.status_code == 403, username


@pytest.mark.asyncio
async def test_teacher_cannot_approve_flag_outside_teaching_scope(
    client,
    admin_user,
    teacher_user,
    student_user,
    test_school,
    test_class,
    db_session,
):
    """Regression: mastery mutations require class+subject teaching scope."""
    flag, token = await _out_of_scope_maths_flag_and_science_teacher_token(
        client, db_session, test_school, test_class, student_user, teacher_user
    )
    resp = await client.post(
        f"/api/v1/mastery/flags/{flag.id}/approve",
        headers=auth_headers(token),
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_teacher_cannot_dismiss_flag_outside_teaching_scope(
    client,
    admin_user,
    teacher_user,
    student_user,
    test_school,
    test_class,
    db_session,
):
    """Wiring guard: dismiss must call _assert_flag_mutation_scope."""
    flag, token = await _out_of_scope_maths_flag_and_science_teacher_token(
        client, db_session, test_school, test_class, student_user, teacher_user
    )
    resp = await client.post(
        f"/api/v1/mastery/flags/{flag.id}/dismiss",
        headers=auth_headers(token),
        json={"reason": "not my subject"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_teacher_cannot_notify_flag_outside_teaching_scope(
    client,
    admin_user,
    teacher_user,
    student_user,
    test_school,
    test_class,
    db_session,
):
    """Wiring guard: notify_parents must call _assert_flag_mutation_scope."""
    flag, wrong_token = await _out_of_scope_maths_flag_and_science_teacher_token(
        client, db_session, test_school, test_class, student_user, teacher_user
    )
    admin_token = await get_auth_token(client, "test_admin", "Admin@123")
    approve = await client.post(
        f"/api/v1/mastery/flags/{flag.id}/approve",
        headers=auth_headers(admin_token),
    )
    assert approve.status_code == 200, approve.text

    resp = await client.post(
        f"/api/v1/mastery/flags/{flag.id}/notify",
        headers=auth_headers(wrong_token),
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_digest_groups_by_student(
    client,
    admin_user,
    student_user,
    test_school,
    test_class,
    db_session,
):
    weak, subject, token = await _seed_flagging_scenario(
        client, db_session, test_school, test_class, student_user
    )
    flag = await _flag_of(db_session, weak.id)
    await client.post(f"/api/v1/mastery/flags/{flag.id}/approve", headers=auth_headers(token))

    resp = await client.get(
        f"/api/v1/mastery/digest?class_id={test_class.id}", headers=auth_headers(token)
    )
    assert resp.status_code == 200
    digest = resp.json()["data"]
    assert len(digest["students"]) == 1
    entry = digest["students"][0]
    assert entry["flags"][0]["topic_display"] == "Algebra"
    assert entry["flags"][0]["narrative"]


@pytest.mark.asyncio
async def test_teacher_cannot_read_heatmap_outside_teaching_scope(
    client,
    admin_user,
    teacher_user,
    student_user,
    test_school,
    test_class,
    db_session,
):
    """Regression: mastery heatmap must enforce staff scope, not just tenant scope.

    A Science-only teacher must not be able to pull the per-student Maths mastery matrix
    for the class.
    """
    flag, science_token = await _out_of_scope_maths_flag_and_science_teacher_token(
        client, db_session, test_school, test_class, student_user, teacher_user
    )
    resp = await client.get(
        f"/api/v1/mastery/classes/{flag.class_id}/heatmap?subject_id={flag.subject_id}",
        headers=auth_headers(science_token),
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_teacher_cannot_read_topic_typeahead_outside_teaching_scope(
    client,
    admin_user,
    teacher_user,
    student_user,
    test_school,
    test_class,
    db_session,
):
    """Topic typeahead must be scoped like the mastery matrix it feeds."""
    flag, science_token = await _out_of_scope_maths_flag_and_science_teacher_token(
        client, db_session, test_class=test_class, test_school=test_school,
        student_user=student_user, teacher_user=teacher_user,
    )
    resp = await client.get(
        f"/api/v1/mastery/topics?subject_id={flag.subject_id}",
        headers=auth_headers(science_token),
    )
    assert resp.status_code == 403

    # Without an explicit subject filter, the Science teacher still sees only their scoped topics.
    resp = await client.get("/api/v1/mastery/topics", headers=auth_headers(science_token))
    assert resp.status_code == 200
    assert resp.json()["data"] == []

    admin_token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.get(
        f"/api/v1/mastery/topics?subject_id={flag.subject_id}",
        headers=auth_headers(admin_token),
    )
    assert resp.status_code == 200
    assert resp.json()["data"] == ["Algebra"]


@pytest.mark.asyncio
async def test_flag_list_subject_filter_cannot_escape_teaching_scope(
    client,
    admin_user,
    teacher_user,
    student_user,
    test_school,
    test_class,
    db_session,
):
    """Regression: passing an explicit subject_id must not bypass the teaching-scope filter.

    The Science teacher explicitly asks for the Maths flags they don't teach → must get none,
    while an admin sees the same flag.
    """
    flag, science_token = await _out_of_scope_maths_flag_and_science_teacher_token(
        client, db_session, test_school, test_class, student_user, teacher_user
    )
    # Explicit out-of-scope subject filter → empty (cannot escape scope).
    resp = await client.get(
        f"/api/v1/mastery/flags?subject_id={flag.subject_id}",
        headers=auth_headers(science_token),
    )
    assert resp.status_code == 200
    assert resp.json()["data"] == []

    # No filter at all → still empty for the Science teacher (no Science flags exist).
    resp = await client.get("/api/v1/mastery/flags", headers=auth_headers(science_token))
    assert resp.status_code == 200
    assert resp.json()["data"] == []

    # Admin sees the Maths flag.
    admin_token = await get_auth_token(client, "test_admin", "Admin@123")
    resp = await client.get("/api/v1/mastery/flags", headers=auth_headers(admin_token))
    assert resp.status_code == 200
    assert any(f["id"] == str(flag.id) for f in resp.json()["data"])


@pytest.mark.asyncio
async def test_digest_scoped_to_teaching_assignments(
    client,
    admin_user,
    teacher_user,
    student_user,
    test_school,
    test_class,
    db_session,
):
    """Regression: the printable digest must not expose other classes'/subjects' narratives."""
    flag, science_token = await _out_of_scope_maths_flag_and_science_teacher_token(
        client, db_session, test_school, test_class, student_user, teacher_user
    )
    admin_token = await get_auth_token(client, "test_admin", "Admin@123")
    approve = await client.post(
        f"/api/v1/mastery/flags/{flag.id}/approve", headers=auth_headers(admin_token)
    )
    assert approve.status_code == 200, approve.text

    # Science teacher's digest excludes the approved Maths narrative.
    resp = await client.get("/api/v1/mastery/digest", headers=auth_headers(science_token))
    assert resp.status_code == 200
    assert resp.json()["data"]["students"] == []

    # Admin's digest includes it.
    resp = await client.get("/api/v1/mastery/digest", headers=auth_headers(admin_token))
    assert resp.status_code == 200
    assert len(resp.json()["data"]["students"]) == 1


@pytest.mark.asyncio
async def test_flag_evidence_chain_links_curriculum_assessment_and_learning(
    client,
    admin_user,
    student_user,
    test_school,
    test_class,
    db_session,
):
    """Learning evidence chain proves pack → paper → exam → marks → mastery → flag."""
    from app.modules.mastery.services.mastery_service import recompute_class_subject

    weak, subject, token = await _seed_flagging_scenario(
        client, db_session, test_school, test_class, student_user
    )
    flag = await _flag_of(db_session, weak.id)

    pack = CurriculumPack(
        school_id=test_school.id,
        class_id=test_class.id,
        subject_id=subject.id,
        academic_year_id=test_class.academic_year_id,
        board="SSC",
        book_title="Maths",
        version=1,
        status=PackStatus.APPROVED,
        created_by=admin_user.id,
        approved_by=admin_user.id,
        approved_at=datetime.now(timezone.utc),
        rag_indexed_at=datetime.now(timezone.utc),
        rag_index_topic_count=1,
    )
    db_session.add(pack)
    await db_session.flush()
    chapter = CurriculumChapter(
        school_id=test_school.id,
        pack_id=pack.id,
        number="1",
        title="Algebra",
        order_index=1,
    )
    db_session.add(chapter)
    await db_session.flush()
    topic = CurriculumTopic(
        school_id=test_school.id,
        chapter_id=chapter.id,
        title="Algebra",
        order_index=1,
        concepts=["Linear equations"],
    )
    db_session.add(topic)
    await db_session.flush()
    concept = CurriculumConcept(
        school_id=test_school.id,
        pack_id=pack.id,
        topic_id=topic.id,
        slug="linear-equations",
        title="Linear equations",
        order_index=1,
        source=ConceptSource.PACK_JSONB,
    )
    db_session.add(concept)
    paper = QuestionPaper(
        school_id=test_school.id,
        class_id=test_class.id,
        subject_id=subject.id,
        created_by=admin_user.id,
        pack_id=pack.id,
        grounded=True,
        grounding_sources=[{"index": 1, "chapter": "Algebra", "topic": "Algebra"}],
        title="Algebra Evidence Paper",
        board="SSC",
        grade=test_class.grade,
        subject_name=subject.name,
        total_marks=25,
        topics=["Algebra"],
        sections=[],
        status=PaperStatus.APPROVED,
        approved_by=admin_user.id,
        approved_at=datetime.now(timezone.utc),
    )
    db_session.add(paper)
    await db_session.flush()

    exams = list(
        (
            await db_session.execute(
                select(Exam).where(
                    Exam.school_id == test_school.id,
                    Exam.class_id == test_class.id,
                    Exam.subject_id == subject.id,
                )
            )
        )
        .scalars()
        .all()
    )
    assert exams
    for exam in exams:
        exam.source_paper_id = paper.id

    evaluation = AnswerSheetEvaluation(
        school_id=test_school.id,
        exam_id=exams[0].id,
        student_id=weak.id,
        created_by=admin_user.id,
        status=EVAL_STATUS_APPROVED,
        ai_suggestions={"1": {"marks_suggested": 2, "max_marks": 5}},
        approved_by=admin_user.id,
        approved_at=datetime.now(timezone.utc),
    )
    db_session.add(evaluation)
    await db_session.flush()

    await recompute_class_subject(db_session, test_school.id, test_class.id, subject.id)

    resp = await client.get(
        f"/api/v1/mastery/flags/{flag.id}/evidence-chain",
        headers=auth_headers(token),
    )
    assert resp.status_code == 200, resp.text
    chain = resp.json()["data"]
    assert chain["tenant_slug"] == "test"
    assert chain["curriculum_pack_ids"] == [str(pack.id)]
    assert chain["question_paper_ids"] == [str(paper.id)]
    assert chain["approved_evaluation_ids"] == [str(evaluation.id)]
    assert chain["mastery"]["topic_display"] == "Algebra"
    assert chain["weak_concept_count"] >= 1
    assert chain["weak_concept_pack_ids"] == [str(pack.id)]
    assert chain["grounded"] is True
    assert chain["fallback"] is False
    assert chain["warnings"] == []


@pytest.mark.asyncio
async def test_teacher_cannot_read_evidence_chain_outside_scope(
    client,
    admin_user,
    teacher_user,
    student_user,
    test_school,
    test_class,
    db_session,
):
    flag, science_token = await _out_of_scope_maths_flag_and_science_teacher_token(
        client, db_session, test_class=test_class, test_school=test_school,
        student_user=student_user, teacher_user=teacher_user,
    )
    resp = await client.get(
        f"/api/v1/mastery/flags/{flag.id}/evidence-chain",
        headers=auth_headers(science_token),
    )
    assert resp.status_code == 403
