"""Field encryption for regulated PII (Aadhaar): round-trip, legacy plaintext, rotation, and
that the value is actually ciphertext at rest in the database."""

from datetime import date

import pytest
from cryptography.fernet import Fernet, MultiFernet
from sqlalchemy import select, text

import app.core.encryption as enc
from app.db.models.school_ops import AdmissionCandidate, AdmissionStage

AADHAAR = "123456789012"


def _use_keys(monkeypatch, *keys: bytes) -> None:
    """Pin a STABLE cipher for the test (a fresh key per _cipher() call would never decrypt)."""
    cipher = MultiFernet([Fernet(k) for k in keys])
    monkeypatch.setattr(enc, "_cipher", lambda: cipher)


def test_encrypt_decrypt_roundtrip(monkeypatch):
    _use_keys(monkeypatch, Fernet.generate_key())
    token = enc.encrypt_value(AADHAAR)
    assert token != AADHAAR  # stored value is not the plaintext
    assert enc.decrypt_value(token) == AADHAAR


def test_none_passthrough(monkeypatch):
    _use_keys(monkeypatch, Fernet.generate_key())
    assert enc.encrypt_value(None) is None
    assert enc.decrypt_value(None) is None


def test_legacy_plaintext_reads_through(monkeypatch):
    # A value written before encryption was enabled isn't a valid token — read it verbatim.
    _use_keys(monkeypatch, Fernet.generate_key())
    assert enc.decrypt_value(AADHAAR) == AADHAAR


def test_disabled_is_transparent(monkeypatch):
    monkeypatch.setattr(enc, "_cipher", lambda: None)
    assert enc.encrypt_value(AADHAAR) == AADHAAR
    assert enc.decrypt_value(AADHAAR) == AADHAAR


def test_key_rotation_decrypts_old_and_writes_new(monkeypatch):
    old, new = Fernet.generate_key(), Fernet.generate_key()
    _use_keys(monkeypatch, old)
    token_old = enc.encrypt_value(AADHAAR)
    # Rotate: new key primary, old key retained for decryption.
    _use_keys(monkeypatch, new, old)
    assert enc.decrypt_value(token_old) == AADHAAR  # old token still readable
    token_new = enc.encrypt_value("999900001111")
    assert enc.decrypt_value(token_new) == "999900001111"  # new writes use the new key


def test_type_decorator_bind_and_result(monkeypatch):
    _use_keys(monkeypatch, Fernet.generate_key())
    col = enc.EncryptedString(512)
    stored = col.process_bind_param(AADHAAR, None)
    assert stored != AADHAAR
    assert col.process_result_value(stored, None) == AADHAAR
    assert col.process_result_value("legacy-plaintext", None) == "legacy-plaintext"


@pytest.mark.asyncio
async def test_aadhaar_ciphertext_at_rest(db_session, test_school, monkeypatch):
    """End-to-end: the raw DB column holds ciphertext; the ORM returns plaintext."""
    _use_keys(monkeypatch, Fernet.generate_key())

    candidate = AdmissionCandidate(
        school_id=test_school.id,
        name="Test Candidate",
        grade_applied="Grade 1",
        stage=AdmissionStage.ENQUIRY,
        enquiry_date=date(2026, 7, 1),
        aadhaar_number=AADHAAR,
    )
    db_session.add(candidate)
    await db_session.flush()
    candidate_id = candidate.id

    # Raw column value must NOT be the plaintext Aadhaar.
    raw = (
        await db_session.execute(
            text("SELECT aadhaar_number FROM admission_candidates WHERE id = :id"),
            {"id": candidate_id},
        )
    ).scalar_one()
    assert raw != AADHAAR
    assert AADHAAR not in (raw or "")

    # But the ORM decrypts transparently on read.
    db_session.expire_all()
    reloaded = (
        await db_session.execute(
            select(AdmissionCandidate).where(AdmissionCandidate.id == candidate_id)
        )
    ).scalar_one()
    assert reloaded.aadhaar_number == AADHAAR
