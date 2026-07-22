"""Stage 2B — prospect tenant provisioning, isolation, cleanup, and session renewal."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.job import Job, JobStatus
from app.db.models.school import School
from app.db.models.user import User
from app.modules.demo import TENANT_KIND_PROSPECT_DEMO
from app.core.jobs.worker import register_job_handlers, run_job
from app.modules.demo.services.cleanup_service import TenantCleanupError, TenantCleanupService
from app.modules.demo.services.demo_session_service import DemoSessionService
from tests.conftest import auth_headers


class _TestSessionFactory:
    """Route run_job through the pytest db_session (same outer transaction)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def __aenter__(self) -> AsyncSession:
        return self._session

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None


@pytest.fixture
def patch_worker_session(db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        "app.core.jobs.worker.async_session_factory",
        lambda: _TestSessionFactory(db_session),
    )


@pytest.mark.asyncio
async def test_create_demo_session_provisions_isolated_tenant(client: AsyncClient, db_session: AsyncSession):
    resp = await client.post("/api/v1/demo/sessions", json={"display_name": "Visitor School"})
    assert resp.status_code == 201, resp.text
    body = resp.json()["data"]
    assert body["tenant_slug"].startswith("demo-")
    assert body["access_token"]
    assert body["session_token"]
    assert len(body["session_token"]) >= 16
    assert body["onboarding_path"] == "/dashboard/teaching/curriculum/onboarding"
    assert "studynexs_refresh" in resp.cookies

    school = (
        await db_session.execute(select(School).where(School.tenant_slug == body["tenant_slug"]))
    ).scalar_one()
    assert school.tenant_kind == TENANT_KIND_PROSPECT_DEMO
    assert school.expires_at is not None
    assert school.demo_session_token_hash is not None
    assert school.is_active is True

    principal = (
        await db_session.execute(
            select(User).where(User.school_id == school.id, User.username == "principal")
        )
    ).scalar_one()
    assert principal is not None


@pytest.mark.asyncio
async def test_demo_session_renew_with_token(client: AsyncClient):
    create = await client.post("/api/v1/demo/sessions", json={})
    assert create.status_code == 201
    session = create.json()["data"]
    renew = await client.post(
        "/api/v1/demo/sessions/renew",
        json={"session_token": session["session_token"]},
        headers={"X-Tenant-Slug": session["tenant_slug"]},
    )
    assert renew.status_code == 200, renew.text
    renewed = renew.json()["data"]
    assert renewed["access_token"]
    assert renewed["session_token"] == session["session_token"]
    assert "studynexs_refresh" in renew.cookies


@pytest.mark.asyncio
async def test_prospect_tenant_cannot_see_paid_school_data(
    client: AsyncClient, db_session: AsyncSession, test_school: School
):
    create = await client.post("/api/v1/demo/sessions", json={})
    assert create.status_code == 201
    session = create.json()["data"]
    token = session["access_token"]
    slug = session["tenant_slug"]

    resp = await client.get(
        "/api/v1/academic/classes",
        headers={**auth_headers(token), "X-Tenant-Slug": slug},
    )
    assert resp.status_code == 200
    class_rows = resp.json().get("items") or []
    assert len(class_rows) >= 1

    paid = await db_session.get(School, test_school.id)
    assert paid is not None
    assert paid.tenant_slug == "test"
    assert paid.tenant_kind in ("customer", "reference", "pilot")


@pytest.mark.asyncio
async def test_cleanup_refuses_protected_tenant(db_session: AsyncSession, test_school: School):
    service = TenantCleanupService(db_session)
    with pytest.raises(TenantCleanupError, match="protected"):
        await service.purge_prospect_tenant(test_school.id)


@pytest.mark.asyncio
async def test_cleanup_purges_prospect_tenant(client: AsyncClient, db_session: AsyncSession):
    create = await client.post("/api/v1/demo/sessions", json={})
    assert create.status_code == 201
    session = create.json()["data"]
    school_id = uuid.UUID(session["school_id"])

    service = DemoSessionService(db_session)
    result = await service.purge_now(school_id)
    assert result["tenant_slug"] == session["tenant_slug"]

    gone = await db_session.get(School, school_id)
    assert gone is None


@pytest.mark.asyncio
async def test_cleanup_is_idempotent(client: AsyncClient, db_session: AsyncSession):
    create = await client.post("/api/v1/demo/sessions", json={})
    assert create.status_code == 201
    school_id = uuid.UUID(create.json()["data"]["school_id"])

    service = TenantCleanupService(db_session)
    first = await service.purge_prospect_tenant(school_id)
    assert first.get("already_purged") is not True
    second = await service.purge_prospect_tenant(school_id)
    assert second.get("already_purged") is True


@pytest.mark.asyncio
async def test_cleanup_purges_prospect_with_file_referencing_rows(
    client: AsyncClient, db_session: AsyncSession
):
    from datetime import date
    from decimal import Decimal

    from app.db.models.academic import AcademicYear, Class, Subject
    from app.db.models.curriculum_pack import CurriculumPack, PackStatus
    from app.db.models.document_ingestion import DocumentIngestion, DocumentType, IngestStatus
    from app.db.models.file import FileCategory, UploadedFile
    from app.db.models.school_ops import SchoolExpense, StaffProfile

    create = await client.post("/api/v1/demo/sessions", json={})
    assert create.status_code == 201
    session = create.json()["data"]
    school_id = uuid.UUID(session["school_id"])
    slug = session["tenant_slug"]

    principal = (
        await db_session.execute(
            select(User).where(User.school_id == school_id, User.username == "principal")
        )
    ).scalar_one()
    cls = (await db_session.execute(select(Class).where(Class.school_id == school_id))).scalar_one()
    subject = (
        await db_session.execute(select(Subject).where(Subject.school_id == school_id))
    ).scalar_one()
    ay = (
        await db_session.execute(select(AcademicYear).where(AcademicYear.school_id == school_id))
    ).scalar_one()

    file_row = UploadedFile(
        school_id=school_id,
        filename="syllabus.pdf",
        original_name="syllabus.pdf",
        content_type="application/pdf",
        size_bytes=1024,
        category=FileCategory.DOCUMENT,
        storage_path=f"{school_id}/syllabus.pdf",
        url=f"/files/{school_id}/syllabus.pdf",
        uploaded_by=principal.id,
    )
    db_session.add(file_row)
    await db_session.flush()

    pack = CurriculumPack(
        school_id=school_id,
        class_id=cls.id,
        subject_id=subject.id,
        academic_year_id=ay.id,
        board="SSC",
        version=1,
        status=PackStatus.DRAFT,
        created_by=principal.id,
    )
    db_session.add(pack)
    await db_session.flush()

    db_session.add(
        DocumentIngestion(
            school_id=school_id,
            pack_id=pack.id,
            file_id=file_row.id,
            doc_type=DocumentType.NOTES,
            status=IngestStatus.COMPLETED,
            source_name="syllabus.pdf",
            ingested_by=principal.id,
        )
    )
    db_session.add(
        StaffProfile(
            school_id=school_id,
            user_id=principal.id,
            first_name="Demo",
            last_name="Principal",
            aadhaar_document_file_id=file_row.id,
            created_by=principal.id,
        )
    )
    db_session.add(
        SchoolExpense(
            school_id=school_id,
            vendor="Stationery Co",
            category="supplies",
            amount=Decimal("500.00"),
            expense_date=date.today(),
            receipt_file_id=file_row.id,
            created_by=principal.id,
        )
    )
    await db_session.commit()

    service = TenantCleanupService(db_session)
    result = await service.purge_prospect_tenant(school_id)
    assert result["tenant_slug"] == slug
    assert await db_session.get(School, school_id) is None


@pytest.mark.asyncio
async def test_run_job_marks_tenant_cleanup_done(
    client: AsyncClient, db_session: AsyncSession, patch_worker_session
):
    await register_job_handlers()

    create = await client.post("/api/v1/demo/sessions", json={})
    assert create.status_code == 201
    session = create.json()["data"]
    school_id = uuid.UUID(session["school_id"])

    job = Job(
        type="tenant_cleanup",
        params={"school_id": str(school_id)},
        school_id=school_id,
        status=JobStatus.QUEUED,
    )
    db_session.add(job)
    await db_session.commit()
    job_id = job.id

    await run_job({}, str(job_id))

    refreshed = await db_session.get(Job, job_id)
    assert refreshed is not None
    assert refreshed.status == JobStatus.DONE
    assert refreshed.result.get("tenant_slug") == session["tenant_slug"]
    assert await db_session.get(School, school_id) is None


@pytest.mark.asyncio
async def test_cleanup_worker_excludes_running_job_row(
    client: AsyncClient, db_session: AsyncSession, patch_worker_session
):
    create = await client.post("/api/v1/demo/sessions", json={})
    assert create.status_code == 201
    session = create.json()["data"]
    school_id = uuid.UUID(session["school_id"])

    job = Job(
        type="tenant_cleanup",
        params={"school_id": str(school_id)},
        school_id=school_id,
        status=JobStatus.RUNNING,
    )
    db_session.add(job)
    await db_session.commit()

    await register_job_handlers()
    await run_job({}, str(job.id))

    assert await db_session.get(School, school_id) is None
    surviving = await db_session.get(Job, job.id)
    assert surviving is not None
    assert surviving.status == JobStatus.DONE


@pytest.mark.asyncio
async def test_expired_tenant_returns_410(db_session: AsyncSession, client: AsyncClient):
    from fastapi import HTTPException

    from app.core.tenant import resolve_tenant

    create = await client.post("/api/v1/demo/sessions", json={})
    assert create.status_code == 201
    session = create.json()["data"]
    slug = session["tenant_slug"]
    school_id = uuid.UUID(session["school_id"])

    school = await db_session.get(School, school_id)
    assert school is not None
    school.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    await db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        await resolve_tenant(slug, db_session)
    assert exc_info.value.status_code == 410


@pytest.mark.asyncio
async def test_sweep_expired_deactivates_and_purges(client: AsyncClient, db_session: AsyncSession):
    create = await client.post("/api/v1/demo/sessions", json={})
    assert create.status_code == 201
    session = create.json()["data"]
    school_id = uuid.UUID(session["school_id"])

    school = await db_session.get(School, school_id)
    assert school is not None
    school.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    await db_session.commit()

    service = DemoSessionService(db_session)
    swept = await service.sweep_expired(enqueue_cleanup=False)
    assert session["tenant_slug"] in swept

    gone = await db_session.get(School, school_id)
    assert gone is None


@pytest.mark.asyncio
async def test_sweep_releases_capacity_for_new_prospect(
    client: AsyncClient, db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(
        "app.modules.demo.services.provisioning_service.settings.DEMO_MAX_ACTIVE_PROSPECTS",
        1,
    )
    first = await client.post("/api/v1/demo/sessions", json={"display_name": "Cap One"})
    assert first.status_code == 201
    school_id = uuid.UUID(first.json()["data"]["school_id"])

    blocked = await client.post("/api/v1/demo/sessions", json={"display_name": "Cap Two"})
    assert blocked.status_code == 429

    school = await db_session.get(School, school_id)
    assert school is not None
    school.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    await db_session.commit()

    service = DemoSessionService(db_session)
    await service.sweep_expired(enqueue_cleanup=False)

    active = await db_session.execute(
        select(func.count())
        .select_from(School)
        .where(
            School.tenant_kind == TENANT_KIND_PROSPECT_DEMO,
            School.is_active.is_(True),
        )
    )
    assert int(active.scalar_one()) == 0

    third = await client.post("/api/v1/demo/sessions", json={"display_name": "Cap Three"})
    assert third.status_code == 201
