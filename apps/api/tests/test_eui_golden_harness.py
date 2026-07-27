"""EUI Golden Harness — Educational Identity deterministic ID cases."""

from __future__ import annotations

import json
from pathlib import Path

from app.modules.eui.services.educational_identity_id import stable_identity_id

GOLDEN_DIR = Path(__file__).parent / "golden" / "eui_v1"


def test_eui_identity_golden_harness_cases_are_deterministic_and_unique():
    payload = json.loads((GOLDEN_DIR / "educational_identity_cases.json").read_text())

    assert payload["version"] == "eui-identity-golden-v1"
    assert payload["authorization"] == "EUI-PH1-AUTH-001"
    case_ids = [case["id"] for case in payload["cases"]]
    assert len(case_ids) == len(set(case_ids))

    expected_ids: set[str] = set()
    for case in payload["cases"]:
        actual = stable_identity_id(**case["input"])
        assert actual == case["expected_id"], case["id"]
        expected_ids.add(case["expected_id"])

    assert len(expected_ids) == len(payload["cases"])
