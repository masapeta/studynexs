"""Admission API security — PII masking and identity document access."""
from __future__ import annotations

import pytest

from tests.conftest import access_token_for, auth_headers

_MIN_PDF = (
    b"%PDF-1.0\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj "
    b"2 0 obj<</Type/Pages/Kids[]/Count 0>>endobj\n"
    b"xref\n0 3\ntrailer<</Root 1 0 R>>\n%%EOF"
)


@pytest.mark.asyncio
async def test_admission_list_masks_aadhaar(client, admin_user, db_session):
    from datetime import date

    from app.db.models.school_ops import AdmissionCandidate, AdmissionStage

    row = AdmissionCandidate(
        school_id=admin_user.school_id,
        name="Mask Test",
        grade_applied="4",
        stage=AdmissionStage.APPLIED,
        enquiry_date=date.today(),
        parent_name="Parent",
        parent_mobile="+919876543210",
        aadhaar_number="123456789012",
        stage_details={
            "applied": {
                "aadhaar_number": "123456789012",
                "birth_certificate_number": "BC-1",
            }
        },
    )
    db_session.add(row)
    await db_session.flush()

    token = access_token_for(admin_user)
    listed = await client.get("/api/v1/ops/admissions", headers=auth_headers(token))
    assert listed.status_code == 200
    candidates = listed.json()["data"]["candidates"]
    item = next(r for r in candidates if r["name"] == "Mask Test")
    assert item["aadhaar_number"] == "XXXX-XXXX-9012"
    assert item["stage_details"]["applied"]["aadhaar_number"] == "XXXX-XXXX-9012"


@pytest.mark.asyncio
async def test_admission_stage_patch_returns_full_candidate(client, admin_user):
    token = access_token_for(admin_user)
    created = await client.post(
        "/api/v1/ops/admissions",
        headers=auth_headers(token),
        json={
            "name": "Stage Patch",
            "grade_applied": "3",
            "parent_name": "Parent",
            "parent_mobile": "+919876543211",
            "enquiry_date": "2026-06-01",
        },
    )
    assert created.status_code == 201, created.text
    candidate_id = created.json()["data"]["id"]

    up = await client.post(
        "/api/v1/files/upload",
        headers=auth_headers(token),
        files={"file": ("birth.pdf", _MIN_PDF, "application/pdf")},
        data={"category": "document"},
    )
    assert up.status_code == 201
    birth_id = up.json()["data"]["id"]

    aad = await client.post(
        "/api/v1/files/upload",
        headers=auth_headers(token),
        files={"file": ("aadhaar.pdf", _MIN_PDF, "application/pdf")},
        data={"category": "document"},
    )
    assert aad.status_code == 201
    aad_id = aad.json()["data"]["id"]

    patched = await client.patch(
        f"/api/v1/ops/admissions/{candidate_id}/stage",
        headers=auth_headers(token),
        json={
            "stage": "applied",
            "details": {
                "application_date": "2026-06-02",
                "birth_certificate_file_id": birth_id,
                "aadhaar_file_id": aad_id,
                "aadhaar_number": "123456789012",
                "birth_certificate_number": "BC-123",
            },
        },
    )
    assert patched.status_code == 200, patched.text
    body = patched.json()["data"]
    assert body["stage"] == "applied"
    assert body["id"] == candidate_id
    assert body["stage_details"]["applied"]["aadhaar_number"] == "123456789012"
