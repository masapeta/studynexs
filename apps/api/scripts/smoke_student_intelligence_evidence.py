"""Focused Student Intelligence runtime proof.

Verifies the student-facing consumer layer without modifying the certified
Academic Intelligence Core:

Student context -> daily plan -> recommendations -> lesson -> Student Copilot,
all tied to the same student, CurriculumPack, and concept evidence.

Run with API up:
    python scripts/smoke_student_intelligence_evidence.py
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
    LOGIN_STUDENT,
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
) -> str | None:
    rows = _get(client, base, "/api/v1/academic/students?page=1&page_size=20", headers)
    items = rows.get("items") if isinstance(rows, dict) else rows
    for row in items or []:
        sid = str(row.get("id") or row.get("student_id") or "")
        if sid and sid != current_student_id:
            return sid
    return None


def main() -> int:
    client = httpx.Client(follow_redirects=True, timeout=120.0)
    base = _resolve_base(client)
    print(f"API base: {base}")
    ready = client.get(base + "/ready")
    if ready.status_code >= 400:
        raise RuntimeError(f"API not ready: {ready.status_code} {ready.text[:200]}")

    student_headers = _login(client, base, LOGIN_STUDENT)
    principal_headers = _login(client, base, LOGIN_PRINCIPAL)

    ctx = _get(client, base, "/api/v1/portal/context", student_headers)
    student_id = str(ctx.get("student_id") or ctx.get("children", [{}])[0].get("student_id"))
    if not student_id:
        raise RuntimeError("Student portal context did not expose student_id")

    daily = _get(client, base, f"/api/v1/tutor/students/{student_id}/daily-plan", student_headers)
    if daily.get("status") != "ready":
        raise RuntimeError(f"Daily plan is not ready: {daily}")
    if daily.get("fallback") or not daily.get("grounded"):
        raise RuntimeError(f"Daily plan is not certified grounded: {daily}")
    pack_id = str(daily.get("pack_id"))
    concept_id = str(daily.get("concept_id"))
    concept_slug = str(daily.get("concept_slug"))
    lesson_key = str(daily.get("lesson_key"))
    mastery_topic = str(daily.get("mastery_topic") or "")
    if not all([pack_id, concept_id, concept_slug, lesson_key, mastery_topic]):
        raise RuntimeError(f"Daily plan lacks evidence identifiers: {daily}")

    mastery = _get(client, base, f"/api/v1/mastery/students/{student_id}", student_headers)
    mastery_topics = [
        topic
        for subject in mastery.get("subjects", [])
        for topic in subject.get("topics", [])
        if str(topic.get("topic_display") or topic.get("topic")).casefold()
        == mastery_topic.casefold()
    ]
    if not mastery_topics:
        raise RuntimeError("Student mastery does not include the source mastery topic")
    daily_mastery = float(daily.get("mastery_pct"))
    source_mastery = float(mastery_topics[0].get("mastery_pct"))
    if round(daily_mastery, 2) != round(source_mastery, 2):
        raise RuntimeError(
            "Daily plan mastery does not match the source mastery topic: "
            f"{daily_mastery} != {source_mastery}"
        )

    study_context = _get(
        client,
        base,
        f"/api/v1/tutor/students/{student_id}/study-context",
        student_headers,
    )
    weak_matches = [
        c
        for c in study_context.get("weak_concepts", [])
        if str(c.get("pack_id")) == pack_id and str(c.get("concept_id")) == concept_id
    ]
    if not weak_matches or not study_context.get("grounded"):
        raise RuntimeError("Study context is not grounded on the daily-plan concept")
    if str(weak_matches[0].get("mastery_topic") or "") != mastery_topic:
        raise RuntimeError("Study context weak concept does not retain mastery topic evidence")

    recs = _get(
        client,
        base,
        f"/api/v1/tutor/students/{student_id}/recommendations",
        student_headers,
    )
    rec = next(
        (
            r
            for r in recs or []
            if str(r.get("pack_id")) == pack_id
            and str(r.get("concept_id")) == concept_id
            and r.get("lesson_key") == lesson_key
        ),
        None,
    )
    if not rec:
        raise RuntimeError("Tutor recommendations do not include the daily-plan evidence")

    lesson = _get(
        client,
        base,
        f"/api/v1/tutor/students/{student_id}/lessons/{lesson_key}",
        student_headers,
    )
    if (
        str(lesson.get("pack_id")) != pack_id
        or str(lesson.get("concept_id")) != concept_id
        or lesson.get("trigger") != "concept_card"
    ):
        raise RuntimeError(f"Tutor lesson is not tied to the daily-plan concept: {lesson}")

    answer = _post(
        client,
        base,
        f"/api/v1/tutor/students/{student_id}/ask",
        student_headers,
        {
            "question": f"Why should I study {daily.get('topic')} today?",
            "concept_slug": concept_slug,
        },
    )
    if (
        not answer.get("grounded")
        or str(answer.get("pack_id")) != pack_id
        or str(answer.get("concept_id")) != concept_id
        or not answer.get("citations")
    ):
        raise RuntimeError(f"Student Copilot answer is not grounded on same evidence: {answer}")

    other_student_id = _find_other_student_id(client, base, principal_headers, student_id)
    if other_student_id:
        denied = client.get(
            base + f"/api/v1/tutor/students/{other_student_id}/daily-plan",
            headers=student_headers,
        )
        if denied.status_code != 403:
            raise RuntimeError(
                f"Student could access another student's daily plan: {denied.status_code}"
            )

    ledger = {
        "tenant": TENANT_SLUG,
        "student_id": student_id,
        "learning_concept": daily.get("topic"),
        "mastery_topic": mastery_topic,
        "mastery_pct": daily.get("mastery_pct"),
        "pack_id": pack_id,
        "concept_id": concept_id,
        "concept_slug": concept_slug,
        "lesson_key": lesson_key,
        "daily_plan_grounded": daily.get("grounded"),
        "daily_plan_fallback": daily.get("fallback"),
        "study_context_sources": study_context.get("source_count"),
        "recommendation_source": rec.get("source"),
        "lesson_trigger": lesson.get("trigger"),
        "copilot_grounded": answer.get("grounded"),
        "copilot_citations": answer.get("citations"),
        "cross_student_denied": bool(other_student_id),
    }
    print("\nStudent Intelligence evidence ledger:")
    for key, value in ledger.items():
        print(f"  {key}: {value}")
    print("\nSTUDENT INTELLIGENCE EVIDENCE: PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"\nSTUDENT INTELLIGENCE EVIDENCE: FAIL\n{exc}")
        raise
