"""Live smoke: supporting-material ingestion into an approved CurriculumPack.

Uploads a small worksheet PDF (≤1 MB platform limit — not for full textbooks),
indexes it into pack grounding, verifies chunks, then cleans up file/ingestion/vectors
so the Reference tenant is not polluted on every run.

Run (API on :8000, reference tenant seeded with approved pack):
  python scripts/smoke_document_ingest_live.py
"""
from __future__ import annotations

import asyncio
import os
import sys
import uuid
from pathlib import Path

_scripts_dir = Path(__file__).resolve().parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))
_api_root = _scripts_dir.parent
if str(_api_root) not in sys.path:
    sys.path.insert(0, str(_api_root))

import httpx
from sqlalchemy import delete, select

from app.core.database import async_session_factory
from app.db.models.academic import Subject
from app.db.models.curriculum_pack import CurriculumPack, PackStatus
from app.db.models.document_ingestion import DocumentIngestion
from app.db.models.file import UploadedFile
from app.db.models.school import School
from app.modules.ai.rag import RagService
from app.modules.ai.vectorstore import get_vector_store
from reference_school_config import DEMO_PASSWORD, LOGIN_PRINCIPAL, TENANT_SLUG

BASE = os.environ.get("SMOKE_BASE_URL", "").rstrip("/") or "http://127.0.0.1:8000"
H = {"X-Tenant-Slug": TENANT_SLUG}
SMOKE_FILE_TAG = "smoke-supporting-material-ingest"


def _minimal_text_pdf(text: str) -> bytes:
    """Build a tiny PDF whose text pypdf can extract (no OCR)."""
    safe = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = f"BT /F1 12 Tf 72 720 Td ({safe}) Tj ET"
    stream_len = len(stream.encode("latin-1", errors="replace"))
    parts = [
        b"%PDF-1.4\n",
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n",
        (
            b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n"
        ),
        f"4 0 obj << /Length {stream_len} >> stream\n{stream}\nendstream endobj\n".encode(),
        b"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n",
        b"xref\n0 6\n0000000000 65535 f \n",
        b"trailer << /Size 6 /Root 1 0 R >>\nstartxref\n0\n%%EOF\n",
    ]
    return b"".join(parts)


def _login(client: httpx.Client) -> dict[str, str]:
    r = client.post(
        f"{BASE}/api/v1/auth/login",
        headers=H,
        json={"username": LOGIN_PRINCIPAL, "password": DEMO_PASSWORD},
    )
    if r.status_code >= 400:
        print(f"LOGIN FAIL: {r.status_code}\n{r.text[:300]}")
        raise SystemExit(1)
    token = r.json().get("access_token")
    return {**H, "Authorization": f"Bearer {token}"}


def _data(body: dict) -> dict | list:
    if isinstance(body, dict) and "data" in body:
        return body["data"]
    return body


async def _cleanup_ingest_artifacts(
    *,
    school_id: uuid.UUID,
    pack_id: uuid.UUID,
    file_id: uuid.UUID,
) -> None:
    """Remove smoke upload, ingestion row, and pack-scoped document vectors."""
    fid = str(file_id)
    async with async_session_factory() as db:
        pack = await db.get(CurriculumPack, pack_id)
        if pack is not None:
            store = get_vector_store()
            rag = RagService(db, store=store)
            await store.delete(
                rag._collection(),
                school_id=str(school_id),
                filters={"pack_id": str(pack_id), "file_id": fid},
            )
        await db.execute(
            delete(DocumentIngestion).where(
                DocumentIngestion.school_id == school_id,
                DocumentIngestion.pack_id == pack_id,
                DocumentIngestion.file_id == file_id,
            )
        )
        await db.execute(
            delete(UploadedFile).where(
                UploadedFile.school_id == school_id,
                UploadedFile.id == file_id,
            )
        )
        await db.commit()
    print(f"  cleanup: removed file={fid}, ingestion rows, and document vectors")


async def _resolve_reference_context() -> tuple[uuid.UUID | None, uuid.UUID | None]:
    """Return (school_id, approved maths pack_id) for the reference tenant."""
    async with async_session_factory() as db:
        school = (
            await db.execute(select(School).where(School.tenant_slug == TENANT_SLUG))
        ).scalar_one_or_none()
        if school is None:
            return None, None
        row = (
            await db.execute(
                select(CurriculumPack)
                .join(Subject, Subject.id == CurriculumPack.subject_id)
                .where(
                    CurriculumPack.school_id == school.id,
                    CurriculumPack.status == PackStatus.APPROVED,
                    Subject.name.ilike("%math%"),
                )
                .order_by(CurriculumPack.version.desc())
            )
        ).scalar_one_or_none()
        return school.id, (row.id if row else None)


def main() -> int:
    print(f"Supporting-material ingestion live smoke — API {BASE}\n")
    client = httpx.Client(timeout=120.0)
    if client.get(f"{BASE}/health").status_code >= 400:
        print("API unhealthy")
        return 1

    auth = _login(client)

    async def _run() -> int:
        file_id: uuid.UUID | None = None
        pack_id: uuid.UUID | None = None
        school_id, maths_pack = await _resolve_reference_context()
        if school_id is None:
            print("FAIL: reference school not found")
            return 1

        result = 1
        try:
            packs = client.get(f"{BASE}/api/v1/curriculum/packs", headers=auth)
            packs.raise_for_status()
            approved = [p for p in (_data(packs.json()) or []) if p.get("status") == "approved"]
            if not approved:
                print("FAIL: no approved CurriculumPack — run seed_reference_school_demo_v1.py")
                return 1

            pack = approved[0]
            for p in approved:
                if "quadratic" in (p.get("title") or "").lower():
                    pack = p
                    break
            pack_id = maths_pack or uuid.UUID(str(pack["id"]))
            print(f"  pack_id={pack_id}")

            before = client.get(
                f"{BASE}/api/v1/curriculum/packs/{pack_id}/ingest-status", headers=auth
            )
            chunks_before = 0
            if before.status_code < 400:
                chunks_before = _data(before.json()).get("indexed_document_chunks") or 0
            else:
                print(f"WARN: ingest-status {before.status_code} before ingest")

            pdf_bytes = _minimal_text_pdf(
                "Quadratic equations worksheet — factorisation practice for class ten."
            )
            smoke_name = f"{SMOKE_FILE_TAG}-{uuid.uuid4().hex[:8]}.pdf"
            upload = client.post(
                f"{BASE}/api/v1/files/upload",
                headers=auth,
                params={"category": "document"},
                files={"file": (smoke_name, pdf_bytes, "application/pdf")},
            )
            if upload.status_code >= 400:
                print(f"UPLOAD FAIL: {upload.status_code}\n{upload.text[:400]}")
                return 1
            file_id = uuid.UUID(str(_data(upload.json())["id"]))
            print(f"  uploaded supporting material file_id={file_id} name={smoke_name}")

            ingest = client.post(
                f"{BASE}/api/v1/curriculum/packs/{pack_id}/ingest-document",
                headers=auth,
                json={"file_id": str(file_id), "doc_type": "worksheet"},
            )
            if ingest.status_code >= 400:
                print(f"INGEST FAIL: {ingest.status_code}\n{ingest.text[:400]}")
                return 1
            ing = _data(ingest.json())
            indexed = ing.get("chunks_indexed") or 0
            print(f"  chunks_indexed={indexed} status={ing.get('status')}")

            after = client.get(
                f"{BASE}/api/v1/curriculum/packs/{pack_id}/ingest-status", headers=auth
            )
            if after.status_code < 400:
                st = _data(after.json())
                chunks_after = st.get("indexed_document_chunks") or 0
                print(
                    f"  ingest-status: chunks {chunks_before} -> {chunks_after} "
                    f"recent={len(st.get('recent_ingestions') or [])}"
                )

            if indexed < 1:
                print("FAIL: supporting-material ingest did not index any chunks")
                return 1

            print("\nSUPPORTING-MATERIAL INGESTION LIVE SMOKE: PASS")
            result = 0
            return 0
        finally:
            if file_id and pack_id and school_id:
                try:
                    await _cleanup_ingest_artifacts(
                        school_id=school_id, pack_id=pack_id, file_id=file_id
                    )
                except Exception as exc:  # noqa: BLE001
                    print(f"WARN: cleanup failed ({exc}) — remove smoke artifacts manually")
        return result

    try:
        return asyncio.run(_run())
    finally:
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())
