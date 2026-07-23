"""Tests — Stage 2A Academic Onboarding correctness batch."""

from __future__ import annotations

import json
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db.models.academic import Class, Subject
from app.db.models.school import School
from app.db.models.user import User, UserRole
from app.modules.ai.gateway.base import LLMResult
from app.modules.curriculum.schemas.onboarding import IntelligencePhase
from app.modules.curriculum.services.intelligence_status import compute_intelligence_status
from app.modules.curriculum.services.pack_audit import PackAuditEventType
from app.modules.curriculum.services.pack_readiness import PackReadinessSnapshot
from tests.conftest import access_token_for, auth_headers, get_auth_token


async def _subject(db: AsyncSession, school: School, test_class: Class) -> Subject:
    subject = Subject(school_id=school.id, class_id=test_class.id, name="Maths", code="MTH")
    db.add(subject)
    await db.flush()
    return subject


async def _second_class(
    db: AsyncSession, school: School, academic_year, *, grade: str = "Grade 2", section: str = "B"
) -> Class:
    cls = Class(
        school_id=school.id,
        grade=grade,
        section=section,
        academic_year_id=academic_year.id,
    )
    db.add(cls)
    await db.flush()
    return cls


async def _incharge_user(
    db: AsyncSession, school: School, incharge_class: Class, *, username: str = "incharge_a"
) -> User:
    user = User(
        school_id=school.id,
        username=username,
        mobile="+919876543299",
        full_name="Class Incharge",
        role=UserRole.CLASS_INCHARGE,
        password_hash=hash_password("Incharge@123"),
        is_active=True,
    )
    db.add(user)
    await db.flush()
    incharge_class.class_incharge_id = user.id
    await db.flush()
    return user


_EXTRACTION_JSON = {
    "chapters": [
        {
            "number": "1",
            "title": "Algebra",
            "topics": [
                {
                    "title": "Linear Equations",
                    "concepts": ["slope"],
                    "learning_outcomes": ["Solve linear equations"],
                }
            ],
            "learning_outcomes": [],
        }
    ],
    "low_confidence_notes": [],
    "summary": "Extracted syllabus",
}


@pytest.mark.asyncio
async def test_onboarding_propose_creates_draft_pack(
    client: AsyncClient,
    admin_user: User,
    test_school: School,
    test_class,
    academic_year,
    db_session: AsyncSession,
):
    subject = await _subject(db_session, test_school, test_class)
    token = await get_auth_token(client, "test_admin", "Admin@123")

    async def fake_llm(*_args, **_kwargs):
        return LLMResult(
            text=json.dumps(_EXTRACTION_JSON),
            provider="stub",
            model="dev-stub",
            tokens_in=100,
            tokens_out=200,
            latency_ms=5,
        )

    with patch(
        "app.modules.curriculum.services.curriculum_extraction_service.generate_llm",
        fake_llm,
    ):
        resp = await client.post(
            "/api/v1/curriculum/onboarding/propose",
            headers=auth_headers(token),
            json={
                "class_id": str(test_class.id),
                "subject_id": str(subject.id),
                "academic_year_id": str(academic_year.id),
                "board": "SSC",
                "book_title": "Maths Part I",
                "input_type": "chapter_list",
                "curriculum_text": "1. Algebra\n2. Geometry",
            },
        )
    assert resp.status_code == 201, resp.text
    data = resp.json()["data"]
    assert data["chapters_proposed"] == 1
    assert data["pack"]["status"] == "draft"
    assert len(data["pack"]["chapters"]) == 1
    assert data["pack"]["chapters"][0]["topics"][0]["title"] == "Linear Equations"


@pytest.mark.asyncio
async def test_empty_fallback_pack_cannot_approve(
    client: AsyncClient,
    admin_user: User,
    test_school: School,
    test_class,
    academic_year,
    db_session: AsyncSession,
):
    """Chapter-only fallback packs have no retrievable topics — approval must fail."""
    subject = await _subject(db_session, test_school, test_class)
    token = await get_auth_token(client, "test_admin", "Admin@123")

    async def empty_topics_llm(*_args, **_kwargs):
        return LLMResult(
            text=json.dumps({"chapters": [], "low_confidence_notes": [], "summary": None}),
            provider="stub",
            model="dev-stub",
            tokens_in=10,
            tokens_out=10,
            latency_ms=1,
        )

    with patch(
        "app.modules.curriculum.services.curriculum_extraction_service.generate_llm",
        empty_topics_llm,
    ):
        resp = await client.post(
            "/api/v1/curriculum/onboarding/propose",
            headers=auth_headers(token),
            json={
                "class_id": str(test_class.id),
                "subject_id": str(subject.id),
                "academic_year_id": str(academic_year.id),
                "board": "SSC",
                "input_type": "chapter_list",
                "curriculum_text": "1. Algebra\n2. Geometry",
            },
        )
    assert resp.status_code == 201, resp.text
    pack_id = resp.json()["data"]["pack"]["id"]
    # Line-based fallback creates chapters without topics
    assert resp.json()["data"]["topics_proposed"] == 0

    status_resp = await client.get(
        f"/api/v1/curriculum/packs/{pack_id}/intelligence-status",
        headers=auth_headers(token),
    )
    status = status_resp.json()["data"]
    assert status["can_approve"] is False
    assert status["retrievable_topic_count"] == 0
    assert status["academic_intelligence_ready"] is False

    approve = await client.post(
        f"/api/v1/curriculum/packs/{pack_id}/approve",
        headers=auth_headers(token),
    )
    assert approve.status_code == 400
    assert "topic" in approve.json()["detail"].lower()


@pytest.mark.asyncio
async def test_teacher_denied_onboarding_propose_and_approve(
    client: AsyncClient,
    admin_user: User,
    teacher_user: User,
    test_school: School,
    test_class,
    academic_year,
    db_session: AsyncSession,
):
    subject = await _subject(db_session, test_school, test_class)
    teacher_token = await get_auth_token(client, "test_teacher", "Teacher@123")
    admin_token = access_token_for(admin_user)

    propose = await client.post(
        "/api/v1/curriculum/onboarding/propose",
        headers=auth_headers(teacher_token),
        json={
            "class_id": str(test_class.id),
            "subject_id": str(subject.id),
            "academic_year_id": str(academic_year.id),
            "board": "SSC",
            "curriculum_text": "1. Algebra",
        },
    )
    assert propose.status_code == 403

    create = await client.post(
        "/api/v1/curriculum/packs",
        headers=auth_headers(admin_token),
        json={
            "class_id": str(test_class.id),
            "subject_id": str(subject.id),
            "academic_year_id": str(academic_year.id),
            "board": "SSC",
        },
    )
    pack_id = create.json()["data"]["id"]
    await client.post(
        f"/api/v1/curriculum/packs/{pack_id}/chapters",
        headers=auth_headers(admin_token),
        json={"title": "Ch1", "topics": [{"title": "Topic A"}]},
    )

    approve = await client.post(
        f"/api/v1/curriculum/packs/{pack_id}/approve",
        headers=auth_headers(teacher_token),
    )
    assert approve.status_code == 403


@pytest.mark.asyncio
async def test_wrong_class_incharge_denied_propose_and_approve(
    client: AsyncClient,
    admin_user: User,
    test_school: School,
    test_class,
    academic_year,
    db_session: AsyncSession,
):
    other_class = await _second_class(db_session, test_school, academic_year)
    await _incharge_user(db_session, test_school, test_class, username="incharge_grade1")
    subject_other = await _subject(db_session, test_school, other_class)
    incharge_token = await get_auth_token(client, "incharge_grade1", "Incharge@123")
    admin_token = await get_auth_token(client, "test_admin", "Admin@123")

    propose = await client.post(
        "/api/v1/curriculum/onboarding/propose",
        headers=auth_headers(incharge_token),
        json={
            "class_id": str(other_class.id),
            "subject_id": str(subject_other.id),
            "academic_year_id": str(academic_year.id),
            "board": "SSC",
            "curriculum_text": "1. Algebra",
        },
    )
    assert propose.status_code == 403

    create = await client.post(
        "/api/v1/curriculum/packs",
        headers=auth_headers(admin_token),
        json={
            "class_id": str(other_class.id),
            "subject_id": str(subject_other.id),
            "academic_year_id": str(academic_year.id),
            "board": "SSC",
        },
    )
    pack_id = create.json()["data"]["id"]
    await client.post(
        f"/api/v1/curriculum/packs/{pack_id}/chapters",
        headers=auth_headers(admin_token),
        json={"title": "Ch1", "topics": [{"title": "Topic A"}]},
    )

    approve = await client.post(
        f"/api/v1/curriculum/packs/{pack_id}/approve",
        headers=auth_headers(incharge_token),
    )
    assert approve.status_code == 403


async def _admin_draft_pack_with_structure(
    client: AsyncClient,
    admin_token: str,
    other_class: Class,
    subject: Subject,
    academic_year,
) -> dict[str, str]:
    create = await client.post(
        "/api/v1/curriculum/packs",
        headers=auth_headers(admin_token),
        json={
            "class_id": str(other_class.id),
            "subject_id": str(subject.id),
            "academic_year_id": str(academic_year.id),
            "board": "SSC",
        },
    )
    assert create.status_code == 201, create.text
    pack_id = create.json()["data"]["id"]
    chapter = await client.post(
        f"/api/v1/curriculum/packs/{pack_id}/chapters",
        headers=auth_headers(admin_token),
        json={"title": "Other Class Chapter", "topics": [{"title": "Topic A"}]},
    )
    assert chapter.status_code == 201, chapter.text
    chapter_id = chapter.json()["data"]["id"]
    topic_id = chapter.json()["data"]["topics"][0]["id"]
    topic_lo = await client.post(
        f"/api/v1/curriculum/topics/{topic_id}/learning-outcomes",
        headers=auth_headers(admin_token),
        json={"description": "Topic outcome"},
    )
    assert topic_lo.status_code == 201, topic_lo.text
    topic_outcome_id = topic_lo.json()["data"]["id"]
    chapter_lo = await client.post(
        f"/api/v1/curriculum/chapters/{chapter_id}/learning-outcomes",
        headers=auth_headers(admin_token),
        json={"description": "Chapter outcome"},
    )
    assert chapter_lo.status_code == 201, chapter_lo.text
    chapter_outcome_id = chapter_lo.json()["data"]["id"]
    return {
        "pack_id": pack_id,
        "chapter_id": chapter_id,
        "topic_id": topic_id,
        "topic_outcome_id": topic_outcome_id,
        "chapter_outcome_id": chapter_outcome_id,
    }


@pytest.mark.asyncio
async def test_wrong_class_incharge_denied_all_pack_mutations(
    client: AsyncClient,
    admin_user: User,
    test_school: School,
    test_class,
    academic_year,
    db_session: AsyncSession,
):
    other_class = await _second_class(db_session, test_school, academic_year)
    await _incharge_user(db_session, test_school, test_class, username="mut_incharge")
    subject_other = await _subject(db_session, test_school, other_class)
    incharge_token = await get_auth_token(client, "mut_incharge", "Incharge@123")
    admin_token = await get_auth_token(client, "test_admin", "Admin@123")
    ids = await _admin_draft_pack_with_structure(
        client, admin_token, other_class, subject_other, academic_year
    )
    headers = auth_headers(incharge_token)

    update_pack = await client.put(
        f"/api/v1/curriculum/packs/{ids['pack_id']}",
        headers=headers,
        json={"book_title": "Blocked"},
    )
    assert update_pack.status_code == 403

    add_chapter = await client.post(
        f"/api/v1/curriculum/packs/{ids['pack_id']}/chapters",
        headers=headers,
        json={"title": "Blocked chapter"},
    )
    assert add_chapter.status_code == 403

    update_chapter = await client.put(
        f"/api/v1/curriculum/chapters/{ids['chapter_id']}",
        headers=headers,
        json={"title": "Blocked title"},
    )
    assert update_chapter.status_code == 403

    add_topic = await client.post(
        f"/api/v1/curriculum/chapters/{ids['chapter_id']}/topics",
        headers=headers,
        json={"title": "Blocked topic"},
    )
    assert add_topic.status_code == 403

    update_topic = await client.put(
        f"/api/v1/curriculum/topics/{ids['topic_id']}",
        headers=headers,
        json={"title": "Blocked topic title"},
    )
    assert update_topic.status_code == 403

    add_topic_lo = await client.post(
        f"/api/v1/curriculum/topics/{ids['topic_id']}/learning-outcomes",
        headers=headers,
        json={"description": "Blocked topic LO"},
    )
    assert add_topic_lo.status_code == 403

    add_chapter_lo = await client.post(
        f"/api/v1/curriculum/chapters/{ids['chapter_id']}/learning-outcomes",
        headers=headers,
        json={"description": "Blocked chapter LO"},
    )
    assert add_chapter_lo.status_code == 403

    update_lo = await client.put(
        f"/api/v1/curriculum/learning-outcomes/{ids['topic_outcome_id']}",
        headers=headers,
        json={"description": "Blocked LO edit"},
    )
    assert update_lo.status_code == 403

    delete_lo = await client.delete(
        f"/api/v1/curriculum/learning-outcomes/{ids['chapter_outcome_id']}",
        headers=headers,
    )
    assert delete_lo.status_code == 403

    delete_chapter = await client.delete(
        f"/api/v1/curriculum/chapters/{ids['chapter_id']}",
        headers=headers,
    )
    assert delete_chapter.status_code == 403


@pytest.mark.asyncio
async def test_incharge_allowed_for_own_class(
    client: AsyncClient,
    test_school: School,
    test_class,
    academic_year,
    db_session: AsyncSession,
):
    await _incharge_user(db_session, test_school, test_class, username="incharge_own")
    subject = await _subject(db_session, test_school, test_class)
    token = await get_auth_token(client, "incharge_own", "Incharge@123")

    async def fake_llm(*_args, **_kwargs):
        return LLMResult(
            text=json.dumps(_EXTRACTION_JSON),
            provider="stub",
            model="dev-stub",
            tokens_in=10,
            tokens_out=10,
            latency_ms=1,
        )

    with patch(
        "app.modules.curriculum.services.curriculum_extraction_service.generate_llm",
        fake_llm,
    ):
        resp = await client.post(
            "/api/v1/curriculum/onboarding/propose",
            headers=auth_headers(token),
            json={
                "class_id": str(test_class.id),
                "subject_id": str(subject.id),
                "academic_year_id": str(academic_year.id),
                "board": "SSC",
                "curriculum_text": "1. Algebra",
            },
        )
    assert resp.status_code == 201, resp.text


@pytest.mark.asyncio
async def test_file_upload_deferred_requires_curriculum_text(
    client: AsyncClient,
    admin_user: User,
    test_school: School,
    test_class,
    academic_year,
    db_session: AsyncSession,
):
    subject = await _subject(db_session, test_school, test_class)
    token = await get_auth_token(client, "test_admin", "Admin@123")

    missing_text = await client.post(
        "/api/v1/curriculum/onboarding/propose",
        headers=auth_headers(token),
        json={
            "class_id": str(test_class.id),
            "subject_id": str(subject.id),
            "academic_year_id": str(academic_year.id),
            "board": "SSC",
        },
    )
    assert missing_text.status_code == 422

    file_only = await client.post(
        "/api/v1/curriculum/onboarding/propose",
        headers=auth_headers(token),
        json={
            "class_id": str(test_class.id),
            "subject_id": str(subject.id),
            "academic_year_id": str(academic_year.id),
            "board": "SSC",
            "file_id": str(uuid.uuid4()),
        },
    )
    assert file_only.status_code == 422


@pytest.mark.asyncio
async def test_pack_detail_preserves_review_context(
    client: AsyncClient,
    admin_user: User,
    test_school: School,
    test_class,
    academic_year,
    db_session: AsyncSession,
):
    subject = await _subject(db_session, test_school, test_class)
    token = await get_auth_token(client, "test_admin", "Admin@123")

    async def fake_llm(*_args, **_kwargs):
        return LLMResult(
            text=json.dumps(_EXTRACTION_JSON),
            provider="stub",
            model="dev-stub",
            tokens_in=10,
            tokens_out=10,
            latency_ms=1,
        )

    with patch(
        "app.modules.curriculum.services.curriculum_extraction_service.generate_llm",
        fake_llm,
    ):
        resp = await client.post(
            "/api/v1/curriculum/onboarding/propose",
            headers=auth_headers(token),
            json={
                "class_id": str(test_class.id),
                "subject_id": str(subject.id),
                "academic_year_id": str(academic_year.id),
                "board": "SSC",
                "curriculum_text": "1. Algebra",
            },
        )
    pack_id = resp.json()["data"]["pack"]["id"]

    detail = await client.get(
        f"/api/v1/curriculum/packs/{pack_id}",
        headers=auth_headers(token),
    )
    assert detail.status_code == 200
    body = detail.json()["data"]
    assert body["class_id"] == str(test_class.id)
    assert body["subject_id"] == str(subject.id)
    assert len(body["chapters"]) == 1
    assert body["chapters"][0]["topics"][0]["learning_outcomes"]


@pytest.mark.asyncio
async def test_intelligence_status_ready_after_indexing_with_vectors(
    client: AsyncClient,
    admin_user: User,
    test_school: School,
    test_class,
    academic_year,
    db_session: AsyncSession,
):
    subject = await _subject(db_session, test_school, test_class)
    token = await get_auth_token(client, "test_admin", "Admin@123")

    create = await client.post(
        "/api/v1/curriculum/packs",
        headers=auth_headers(token),
        json={
            "class_id": str(test_class.id),
            "subject_id": str(subject.id),
            "academic_year_id": str(academic_year.id),
            "board": "SSC",
            "book_title": "NCERT",
        },
    )
    pack_id = create.json()["data"]["id"]
    await client.post(
        f"/api/v1/curriculum/packs/{pack_id}/chapters",
        headers=auth_headers(token),
        json={"number": "1", "title": "Algebra", "topics": [{"title": "Linear"}]},
    )

    with patch(
        "app.modules.ai.rag.service.RagService.index_pack",
        new_callable=AsyncMock,
        return_value=4,
    ):
        approve = await client.post(
            f"/api/v1/curriculum/packs/{pack_id}/approve",
            headers=auth_headers(token),
        )
    assert approve.status_code == 200, approve.text

    status_resp = await client.get(
        f"/api/v1/curriculum/packs/{pack_id}/intelligence-status",
        headers=auth_headers(token),
    )
    body = status_resp.json()["data"]
    assert body["pack_approved"] is True
    assert body["retrievable_topic_count"] >= 1
    assert body["rag_vector_count"] == 4
    assert body["academic_intelligence_ready"] is True
    assert body["phase"] == IntelligencePhase.READY.value


@pytest.mark.asyncio
async def test_retry_rag_index_after_failure(
    client: AsyncClient,
    admin_user: User,
    test_school: School,
    test_class,
    academic_year,
    db_session: AsyncSession,
):
    subject = await _subject(db_session, test_school, test_class)
    token = await get_auth_token(client, "test_admin", "Admin@123")

    create = await client.post(
        "/api/v1/curriculum/packs",
        headers=auth_headers(token),
        json={
            "class_id": str(test_class.id),
            "subject_id": str(subject.id),
            "academic_year_id": str(academic_year.id),
            "board": "SSC",
        },
    )
    pack_id = create.json()["data"]["id"]
    await client.post(
        f"/api/v1/curriculum/packs/{pack_id}/chapters",
        headers=auth_headers(token),
        json={"title": "Ch1", "topics": [{"title": "Topic"}]},
    )

    with patch(
        "app.modules.ai.rag.service.RagService.index_pack",
        new_callable=AsyncMock,
        return_value=0,
    ):
        await client.post(
            f"/api/v1/curriculum/packs/{pack_id}/approve",
            headers=auth_headers(token),
        )

    failed = await client.get(
        f"/api/v1/curriculum/packs/{pack_id}/intelligence-status",
        headers=auth_headers(token),
    )
    assert failed.json()["data"]["academic_intelligence_ready"] is False

    with patch(
        "app.modules.ai.rag.service.RagService.index_pack",
        new_callable=AsyncMock,
        return_value=2,
    ):
        retry = await client.post(
            f"/api/v1/curriculum/packs/{pack_id}/retry-rag-index",
            headers=auth_headers(token),
        )
    assert retry.status_code == 200, retry.text
    intel = retry.json()["data"]["intelligence"]
    assert intel["rag_vector_count"] == 2
    assert intel["academic_intelligence_ready"] is True


@pytest.mark.asyncio
async def test_intelligence_status_ready_after_approve_pipeline(
    client: AsyncClient,
    admin_user: User,
    test_school: School,
    test_class,
    academic_year,
    db_session: AsyncSession,
):
    subject = await _subject(db_session, test_school, test_class)
    token = await get_auth_token(client, "test_admin", "Admin@123")

    create = await client.post(
        "/api/v1/curriculum/packs",
        headers=auth_headers(token),
        json={
            "class_id": str(test_class.id),
            "subject_id": str(subject.id),
            "academic_year_id": str(academic_year.id),
            "board": "SSC",
            "book_title": "NCERT",
        },
    )
    pack_id = create.json()["data"]["id"]
    await client.post(
        f"/api/v1/curriculum/packs/{pack_id}/chapters",
        headers=auth_headers(token),
        json={"number": "1", "title": "Algebra", "topics": [{"title": "Linear"}]},
    )

    status_resp = await client.get(
        f"/api/v1/curriculum/packs/{pack_id}/intelligence-status",
        headers=auth_headers(token),
    )
    assert status_resp.status_code == 200
    assert status_resp.json()["data"]["phase"] == IntelligencePhase.DRAFT.value
    assert status_resp.json()["data"]["academic_intelligence_ready"] is False

    approve = await client.post(
        f"/api/v1/curriculum/packs/{pack_id}/approve",
        headers=auth_headers(token),
    )
    assert approve.status_code == 200, approve.text

    status_resp = await client.get(
        f"/api/v1/curriculum/packs/{pack_id}/intelligence-status",
        headers=auth_headers(token),
    )
    body = status_resp.json()["data"]
    assert body["pack_approved"] is True
    assert body["phase"] in {
        IntelligencePhase.READY.value,
        IntelligencePhase.APPROVED_PREPARING.value,
        IntelligencePhase.PARTIAL.value,
        IntelligencePhase.FAILED.value,
    }


@pytest.mark.asyncio
async def test_update_topic_on_draft_pack(
    client: AsyncClient,
    admin_user: User,
    test_school: School,
    test_class,
    academic_year,
    db_session: AsyncSession,
):
    subject = await _subject(db_session, test_school, test_class)
    token = await get_auth_token(client, "test_admin", "Admin@123")
    create = await client.post(
        "/api/v1/curriculum/packs",
        headers=auth_headers(token),
        json={
            "class_id": str(test_class.id),
            "subject_id": str(subject.id),
            "academic_year_id": str(academic_year.id),
            "board": "SSC",
        },
    )
    pack_id = create.json()["data"]["id"]
    ch = await client.post(
        f"/api/v1/curriculum/packs/{pack_id}/chapters",
        headers=auth_headers(token),
        json={"title": "Ch1", "topics": [{"title": "Old Topic"}]},
    )
    topic_id = ch.json()["data"]["topics"][0]["id"]
    upd = await client.put(
        f"/api/v1/curriculum/topics/{topic_id}",
        headers=auth_headers(token),
        json={"title": "New Topic", "concepts": ["concept-a"]},
    )
    assert upd.status_code == 200, upd.text
    assert upd.json()["data"]["title"] == "New Topic"


@pytest.mark.asyncio
async def test_permissions_can_manage_curriculum(
    client: AsyncClient,
    admin_user: User,
    teacher_user: User,
    test_school: School,
    test_class,
    db_session: AsyncSession,
):
    await _incharge_user(db_session, test_school, test_class, username="perm_incharge")
    teacher_token = await get_auth_token(client, "test_teacher", "Teacher@123")
    incharge_token = await get_auth_token(client, "perm_incharge", "Incharge@123")
    admin_token = access_token_for(admin_user)

    teacher_perms = await client.get(
        "/api/v1/users/me/permissions",
        headers=auth_headers(teacher_token),
    )
    assert teacher_perms.json()["data"]["can_manage_curriculum"] is False
    assert teacher_perms.json()["data"]["can_edit_curriculum_draft"] is False
    assert teacher_perms.json()["data"]["can_approve_curriculum"] is False

    incharge_perms = await client.get(
        "/api/v1/users/me/permissions",
        headers=auth_headers(incharge_token),
    )
    assert incharge_perms.json()["data"]["can_manage_curriculum"] is True
    assert incharge_perms.json()["data"]["can_edit_curriculum_draft"] is True
    assert incharge_perms.json()["data"]["can_approve_curriculum"] is True

    admin_perms = await client.get(
        "/api/v1/users/me/permissions",
        headers=auth_headers(admin_token),
    )
    assert admin_perms.json()["data"]["can_manage_curriculum"] is True
    assert admin_perms.json()["data"]["can_edit_curriculum_draft"] is True
    assert admin_perms.json()["data"]["can_approve_curriculum"] is True


def test_compute_intelligence_status_ready():
    pack_id = uuid.uuid4()
    events = [
        {"event_type": PackAuditEventType.PACK_APPROVED.value},
        {"event_type": PackAuditEventType.KG_SPINE_SUCCEEDED.value},
        {
            "event_type": PackAuditEventType.RAG_INDEX_SUCCEEDED.value,
            "metadata": {"vector_count": 3},
        },
    ]
    readiness = PackReadinessSnapshot(
        chapter_count=1,
        topic_count=1,
        retrievable_topic_count=1,
    )
    status = compute_intelligence_status(
        pack_id=pack_id,
        pack_status="approved",
        rag_index_error=None,
        events=events,
        readiness=readiness,
        rag_vector_count=3,
    )
    assert status.academic_intelligence_ready is True
    assert status.phase == IntelligencePhase.READY


def test_compute_intelligence_status_not_ready_without_vectors():
    pack_id = uuid.uuid4()
    events = [
        {"event_type": PackAuditEventType.PACK_APPROVED.value},
        {"event_type": PackAuditEventType.KG_SPINE_SUCCEEDED.value},
        {
            "event_type": PackAuditEventType.RAG_INDEX_SUCCEEDED.value,
            "metadata": {"vector_count": 0},
        },
    ]
    readiness = PackReadinessSnapshot(chapter_count=1, topic_count=1, retrievable_topic_count=1)
    status = compute_intelligence_status(
        pack_id=pack_id,
        pack_status="approved",
        rag_index_error=None,
        events=events,
        readiness=readiness,
        rag_vector_count=0,
    )
    assert status.academic_intelligence_ready is False
    assert status.rag_ready is False
