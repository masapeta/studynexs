"""PII masking helpers — used to keep phone numbers, emails, and IDs out of logs/summaries."""

from app.core.pii import mask_aadhaar, mask_email, mask_id_number, mask_mobile


def test_mask_mobile_keeps_only_last_four():
    assert mask_mobile("+919876543210") == "+********3210"  # 12 digits → 8 masked + last 4
    assert mask_mobile("9876543210") == "******3210"
    # Never echoes the full number.
    assert "9876543" not in mask_mobile("+919876543210")


def test_mask_mobile_edge_cases():
    assert mask_mobile(None) is None
    assert mask_mobile("") is None
    assert mask_mobile("12") == "**"
    assert mask_mobile("+12") == "+**"


def test_mask_email_keeps_domain_and_first_char():
    assert mask_email("john.doe@example.com") == "j***@example.com"
    assert mask_email("a@b.com") == "a***@b.com"
    assert mask_email(None) is None
    # Malformed falls back to id masking (no '@').
    assert mask_email("notanemail") == mask_id_number("notanemail")


def test_mask_aadhaar_still_works():
    assert mask_aadhaar("123456789012") == "XXXX-XXXX-9012"
    assert mask_aadhaar("bad") == "****"
