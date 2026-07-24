"""Focused Parent Intelligence runtime proof.

Verifies the parent-facing consumer layer without modifying the certified
Academic Intelligence Core or Student Intelligence:

Parent context -> linked child -> Student daily-plan evidence -> Parent briefing
-> Parent Copilot ask, all tied to the same tenant, child, CurriculumPack, and
concept evidence. Generic fallback is not accepted as certified behavior.

Run with API up:
    python scripts/smoke_parent_intelligence_evidence.py
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
    LOGIN_PARENT,
    LOGIN_PRINCIPAL,
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


def _post(
    client: httpx.Client,
    base: str,
    path: str,
    headers: dict[str, str],
    payload: dict[str, Any],
) -> Any:
    resp = client.post(base + path, headers=headers, json=payload)
    if resp.status_code >= 400:
        raise RuntimeError(f"POST {path} failed: {resp.status_code} {resp.text[:300]}")
    return _data(resp)


def _find_other_student_id(
    client: httpx.Client,
    base: str,
    headers: dict[str, str],
    current_student_id: str,
) -> str:
    rows = _get(client, base, "/api/v1/academic/students?page=1&page_size=30", headers)
    items = rows.get("items") if isinstance(rows, dict) else rows
    for row in items or []:
        sid = str(row.get("id") or row.get("student_id") or "")
        if sid and sid != current_student_id:
            return sid
    raise RuntimeError("Could not find an unrelated student to verify parent access denial")


def _assert_certified_parent_response(
    *,
    label: str,
    payload: dict[str, Any],
    expected_pack_id: str,
    expected_concept_id: str,
    expected_concept_slug: str,
    expected_mastery_topic: str,
) -> None:
    if payload.get("fallback"):
        raise RuntimeError(f"{label} used fallback and cannot be certified: {payload}")
    if not payload.get("grounded"):
        raise RuntimeError(f"{label} is not grounded: {payload}")
    if int(payload.get("source_count") or 0) < 1:
        raise RuntimeError(f"{label} has no curriculum sources: {payload}")
    if str(payload.get("pack_id")) != expected_pack_id:
        raise RuntimeError(f"{label} pack mismatch: {payload.get('pack_id')} != {expected_pack_id}")
    if str(payload.get("concept_id")) != expected_concept_id:
        raise RuntimeError(
            f"{label} concept mismatch: {payload.get('concept_id')} != {expected_concept_id}"
        )
    if str(payload.get("concept_slug")) != expected_concept_slug:
        raise RuntimeError(
            f"{label} concept slug mismatch: {payload.get('concept_slug')} != "
            f"{expected_concept_slug}"
        )
    if str(payload.get("mastery_topic") or "").casefold() != expected_mastery_topic.casefold():
        raise RuntimeError(
            f"{label} mastery topic mismatch: {payload.get('mastery_topic')} != "
            f"{expected_mastery_topic}"
        )
    if not payload.get("evidence_reason") or not payload.get("evidence_summary"):
        raise RuntimeError(f"{label} lacks parent-facing explainability: {payload}")


def main() -> int:
    client = httpx.Client(follow_redirects=True, timeout=120.0)
    base = _resolve_base(client)
    print(f"API base: {base}")
    ready = client.get(base + "/ready")
    if ready.status_code >= 400:
        raise RuntimeError(f"API not ready: {ready.status_code} {ready.text[:200]}")

    parent_headers = _login(client, base, LOGIN_PARENT)
    principal_headers = _login(client, base, LOGIN_PRINCIPAL)

    ctx = _get(client, base, "/api/v1/portal/context", parent_headers)
    children = ctx.get("children") or []
    if not children:
        raise RuntimeError("Parent portal context did not expose linked children")
    student_id = str(children[0].get("student_id") or "")
    if not student_id:
        raise RuntimeError("Linked child is missing student_id")

    daily = _get(client, base, f"/api/v1/tutor/students/{student_id}/daily-plan", parent_headers)
    if daily.get("status") != "ready":
        raise RuntimeError(f"Linked child daily plan is not ready: {daily}")
    if daily.get("fallback") or not daily.get("grounded"):
        raise RuntimeError(f"Linked child daily plan is not certified grounded: {daily}")
    pack_id = str(daily.get("pack_id"))
    concept_id = str(daily.get("concept_id"))
    concept_slug = str(daily.get("concept_slug"))
    mastery_topic = str(daily.get("mastery_topic") or "")
    if not all([pack_id, concept_id, concept_slug, mastery_topic]):
        raise RuntimeError(f"Daily plan lacks evidence identifiers: {daily}")

    progress = _get(client, base, f"/api/v1/portal/child/{student_id}/progress", parent_headers)
    weak_matches = [
        topic
        for topic in progress.get("weak_topics", [])
        if str(topic.get("topic_display") or topic.get("topic")).casefold()
        == mastery_topic.casefold()
    ]
    if not weak_matches:
        raise RuntimeError("Parent child progress does not expose the source weak topic")

    briefing = _get(
        client,
        base,
        f"/api/v1/parent-copilot/students/{student_id}/briefing",
        parent_headers,
    )
    _assert_certified_parent_response(
        label="Parent briefing",
        payload=briefing,
        expected_pack_id=pack_id,
        expected_concept_id=concept_id,
        expected_concept_slug=concept_slug,
        expected_mastery_topic=mastery_topic,
    )
    if not briefing.get("home_tips"):
        raise RuntimeError("Parent briefing did not include home support guidance")

    answer = _post(
        client,
        base,
        f"/api/v1/parent-copilot/students/{student_id}/ask",
        parent_headers,
        {"question": f"How can I help at home with {daily.get('topic')} tonight?"},
    )
    _assert_certified_parent_response(
        label="Parent ask",
        payload=answer,
        expected_pack_id=pack_id,
        expected_concept_id=concept_id,
        expected_concept_slug=concept_slug,
        expected_mastery_topic=mastery_topic,
    )
    if not answer.get("home_tips"):
        raise RuntimeError("Parent ask did not include home support guidance")

    other_student_id = _find_other_student_id(client, base, principal_headers, student_id)
    denied = client.get(
        base + f"/api/v1/parent-copilot/students/{other_student_id}/briefing",
        headers=parent_headers,
    )
    if denied.status_code != 403:
        raise RuntimeError(
            f"Parent could access unlinked child briefing: {denied.status_code} {denied.text[:200]}"
        )
    denied_progress = client.get(
        base + f"/api/v1/portal/child/{other_student_id}/progress",
        headers=parent_headers,
    )
    if denied_progress.status_code != 403:
        raise RuntimeError(
            "Parent could access unlinked child progress: "
            f"{denied_progress.status_code} {denied_progress.text[:200]}"
        )

    ledger = {
        "tenant": TENANT_SLUG,
        "parent_user": LOGIN_PARENT,
        "student_id": student_id,
        "daily_plan_topic": daily.get("topic"),
        "mastery_topic": mastery_topic,
        "mastery_pct": daily.get("mastery_pct"),
        "pack_id": pack_id,
        "concept_id": concept_id,
        "concept_slug": concept_slug,
        "daily_plan_grounded": daily.get("grounded"),
        "daily_plan_fallback": daily.get("fallback"),
        "briefing_grounded": briefing.get("grounded"),
        "briefing_fallback": briefing.get("fallback"),
        "briefing_sources": briefing.get("source_count"),
        "ask_grounded": answer.get("grounded"),
        "ask_fallback": answer.get("fallback"),
        "ask_sources": answer.get("source_count"),
        "home_tips": len(answer.get("home_tips") or []),
        "cross_child_denied": True,
    }
    print("\nParent Intelligence evidence ledger:")
    for key, value in ledger.items():
        print(f"  {key}: {value}")
    print("\nPARENT INTELLIGENCE EVIDENCE: PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"\nPARENT INTELLIGENCE EVIDENCE: FAIL\n{exc}")
        raise
