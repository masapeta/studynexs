"""Focused Principal Intelligence runtime proof.

Verifies the principal-facing Intervention Center without modifying certified
Academic Intelligence Core, Student Intelligence, or Parent Intelligence:

Dashboard intervention -> existing mastery evidence chain -> approved academic
evidence lineage. Generic KPI-only dashboard data is not accepted as certified
Principal Intelligence behavior.

Run with API up:
    python scripts/smoke_principal_intelligence_evidence.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

_scripts_dir = Path(__file__).resolve().parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

import httpx  # noqa: E402
from reference_school_config import (  # noqa: E402
    DEMO_PASSWORD,
    LOGIN_PRINCIPAL,
    LOGIN_TEACHER_MATHS,
    TENANT_SLUG,
)

BASE = os.environ.get("SMOKE_BASE_URL", "").rstrip("/")
H: dict[str, str] = {"X-Tenant-Slug": TENANT_SLUG}


def _resolve_base(client: httpx.Client) -> str:
    if BASE:
        return BASE
    for base in ("http://127.0.0.1:8000", "http://localhost:8000"):
        try:
            if client.get(base + "/health", timeout=5).status_code < 400:
                return base
        except Exception:  # noqa: BLE001
            continue
    return "http://127.0.0.1:8000"


def _data(resp: httpx.Response) -> Any:
    body = resp.json()
    if isinstance(body, dict) and "data" in body:
        return body["data"]
    return body


def _login(client: httpx.Client, base: str, username: str) -> dict[str, str]:
    resp = client.post(
        base + "/api/v1/auth/login",
        headers=H,
        json={"username": username, "password": DEMO_PASSWORD},
    )
    if resp.status_code == 429:
        raise RuntimeError(f"Login rate-limited for {username}; wait or clear scoped keys.")
    if resp.status_code >= 400:
        raise RuntimeError(f"Login failed for {username}: {resp.status_code} {resp.text[:200]}")
    token = resp.json().get("access_token")
    if not token:
        raise RuntimeError(f"Login for {username} returned no access token")
    return {**H, "Authorization": f"Bearer {token}"}


def _get(client: httpx.Client, base: str, path: str, headers: dict[str, str]) -> Any:
    resp = client.get(base + path, headers=headers)
    if resp.status_code >= 400:
        raise RuntimeError(f"GET {path} failed: {resp.status_code} {resp.text[:240]}")
    return _data(resp)


def _require_card_answers(card: dict[str, Any]) -> None:
    required = {
        "issue": "what is the issue",
        "why_it_matters": "why does it matter",
        "evidence": "what evidence supports it",
        "owner": "who owns the next action",
        "recommended_intervention": "what human intervention is recommended",
    }
    missing = [
        label
        for key, label in required.items()
        if not card.get(key) or (key == "evidence" and not card.get("evidence"))
    ]
    if missing:
        raise RuntimeError(f"Intervention card is not certifiable; missing: {missing}")
    if "human" not in str(card["recommended_intervention"]).casefold():
        raise RuntimeError("Recommended intervention must be explicitly human-led")


def main() -> int:
    client = httpx.Client(follow_redirects=True, timeout=120.0)
    base = _resolve_base(client)
    print(f"API base: {base}")
    ready = client.get(base + "/ready")
    if ready.status_code >= 400:
        raise RuntimeError(f"API not ready: {ready.status_code} {ready.text[:200]}")

    principal_headers = _login(client, base, LOGIN_PRINCIPAL)
    teacher_headers = _login(client, base, LOGIN_TEACHER_MATHS)

    summary = _get(client, base, "/api/v1/dashboard/summary", principal_headers)
    if summary.get("persona") != "admin":
        raise RuntimeError(f"Principal summary persona mismatch: {summary.get('persona')}")
    interventions = summary.get("principal_interventions") or []
    if not interventions:
        raise RuntimeError("Principal Intervention Center has no evidence-backed priorities")

    card = interventions[0]
    _require_card_answers(card)
    chain_href = str(card.get("evidence_chain_href") or "")
    if not chain_href.startswith("/api/v1/mastery/flags/"):
        raise RuntimeError(f"Intervention lacks mastery evidence-chain link: {card}")

    chain = _get(client, base, chain_href, principal_headers)
    if chain.get("tenant_slug") != TENANT_SLUG:
        raise RuntimeError(f"Evidence-chain tenant mismatch: {chain.get('tenant_slug')}")
    if chain.get("fallback"):
        raise RuntimeError(f"Principal intervention lineage has fallback warnings: {chain}")
    if not chain.get("grounded"):
        raise RuntimeError(f"Principal intervention lineage is not grounded: {chain}")
    if not chain.get("curriculum_pack_ids"):
        raise RuntimeError("Lineage lacks CurriculumPack IDs")
    if not chain.get("question_paper_ids"):
        raise RuntimeError("Lineage lacks QuestionPaper IDs")
    if not chain.get("approved_evaluation_ids"):
        raise RuntimeError("Lineage lacks approved evaluation IDs")
    if not chain.get("mastery"):
        raise RuntimeError("Lineage lacks mastery record")

    teacher_summary = _get(client, base, "/api/v1/dashboard/summary", teacher_headers)
    if teacher_summary.get("principal_interventions"):
        raise RuntimeError("Teacher dashboard leaked principal interventions")

    ledger = {
        "tenant": TENANT_SLUG,
        "card_id": card.get("id"),
        "issue": card.get("issue"),
        "owner": card.get("owner"),
        "recommended_intervention": card.get("recommended_intervention"),
        "flag_id": chain.get("flag_id"),
        "student_id": chain.get("student_id"),
        "topic": chain.get("topic_display"),
        "curriculum_pack_ids": chain.get("curriculum_pack_ids"),
        "question_paper_ids": chain.get("question_paper_ids"),
        "approved_evaluation_ids": chain.get("approved_evaluation_ids"),
        "mastery_pct": (chain.get("mastery") or {}).get("mastery_pct"),
        "grounded": chain.get("grounded"),
        "fallback": chain.get("fallback"),
        "teacher_leak_denied": True,
    }

    print("\nPrincipal Intelligence evidence ledger:")
    for key, value in ledger.items():
        print(f"  {key}: {value}")

    print("\nPRINCIPAL INTELLIGENCE EVIDENCE: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
