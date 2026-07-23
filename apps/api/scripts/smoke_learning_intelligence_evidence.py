"""Focused Learning Intelligence runtime proof.

Verifies one post-assessment learning chain on the reference tenant:

CurriculumPack -> QuestionPaper -> Exam -> marks/evaluation -> mastery -> flag
-> weak-concept KG -> tutor + parent consumers.

Run with API up:
    python scripts/smoke_learning_intelligence_evidence.py
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
    LOGIN_STUDENT,
    TENANT_SLUG,
)

BASE = os.environ.get("SMOKE_BASE_URL", "").rstrip("/")
TEACHER_LOGIN = os.environ.get("SMOKE_LEARNING_TEACHER", "teacher6")
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
    return body.get("data") if isinstance(body, dict) else body


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


def _topic_match(candidate: str | None, target: str) -> bool:
    return (candidate or "").strip().casefold() == target.strip().casefold()


def _parent_child_ids(progress: list[dict[str, Any]]) -> set[str]:
    return {str(row.get("student_id")) for row in progress if row.get("student_id")}


def _all_flags(client: httpx.Client, base: str, headers: dict[str, str]) -> list[dict[str, Any]]:
    flags: list[dict[str, Any]] = []
    for status in ("pending_review", "approved", "notified"):
        rows = _get(client, base, f"/api/v1/mastery/flags?status={status}", headers)
        flags.extend(rows or [])
    # Preserve ordering but remove duplicates when the same endpoint returns a row twice.
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for flag in flags:
        fid = str(flag.get("id"))
        if fid and fid not in seen:
            unique.append(flag)
            seen.add(fid)
    return unique


def _find_verified_chain(
    client: httpx.Client,
    base: str,
    teacher_headers: dict[str, str],
    flags: list[dict[str, Any]],
    preferred_student_ids: set[str],
) -> tuple[dict[str, Any], dict[str, Any]]:
    candidates = sorted(
        flags,
        key=lambda f: str(f.get("student_id")) not in preferred_student_ids,
    )
    errors: list[str] = []
    for flag in candidates:
        try:
            chain = _get(
                client,
                base,
                f"/api/v1/mastery/flags/{flag['id']}/evidence-chain",
                teacher_headers,
            )
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{flag.get('id')}: {exc}")
            continue
        if (
            chain.get("grounded")
            and not chain.get("fallback")
            and chain.get("curriculum_pack_ids")
            and chain.get("question_paper_ids")
            and chain.get("mastery")
        ):
            return flag, chain
        errors.append(f"{flag.get('id')}: warnings={chain.get('warnings')}")
    raise RuntimeError(
        "No verified Learning Intelligence evidence chain found: " + " | ".join(errors[:5])
    )


def main() -> int:
    client = httpx.Client(follow_redirects=True, timeout=120.0)
    base = _resolve_base(client)
    print(f"API base: {base}")
    health = client.get(base + "/health")
    if health.status_code >= 400:
        raise RuntimeError(f"API unhealthy: {health.status_code}")

    teacher_headers = _login(client, base, TEACHER_LOGIN)
    parent_headers = _login(client, base, LOGIN_PARENT)
    student_headers = _login(client, base, LOGIN_STUDENT)

    parent_progress = _get(client, base, "/api/v1/portal/parent/children-progress", parent_headers)
    parent_child_ids = _parent_child_ids(parent_progress or [])

    flags = _all_flags(client, base, teacher_headers)
    if not flags:
        # Principal fallback gives an honest diagnostic for setup issues.
        principal_headers = _login(client, base, LOGIN_PRINCIPAL)
        flags = _all_flags(client, base, principal_headers)
        teacher_headers = principal_headers
    if not flags:
        raise RuntimeError("No mastery flags found. Seed/run assessment-to-mastery data first.")

    flag, chain = _find_verified_chain(client, base, teacher_headers, flags, parent_child_ids)
    topic = chain["topic_display"]
    student_id = chain["student_id"]
    pack_ids = {str(pid) for pid in chain.get("curriculum_pack_ids") or []}

    mastery = _get(client, base, f"/api/v1/mastery/students/{student_id}", teacher_headers)
    mastery_topics = [
        t
        for subject in mastery.get("subjects", [])
        for t in subject.get("topics", [])
        if _topic_match(t.get("topic_display"), topic)
    ]
    if not mastery_topics:
        raise RuntimeError(f"Student mastery profile does not include topic {topic!r}")

    student_context = _get(client, base, "/api/v1/portal/context", student_headers)
    if str(student_context.get("student_id")) != str(student_id):
        raise RuntimeError("Reference student login is not the selected evidence-chain student")
    student_mastery = _get(
        client,
        base,
        f"/api/v1/mastery/students/{student_id}",
        student_headers,
    )
    student_topics = [
        t
        for subject in student_mastery.get("subjects", [])
        for t in subject.get("topics", [])
        if _topic_match(t.get("topic_display"), topic)
    ]
    if not student_topics:
        raise RuntimeError("Student portal identity does not see the same mastery topic")

    weak = _get(
        client,
        base,
        f"/api/v1/curriculum/students/{student_id}/weak-concepts",
        teacher_headers,
    )
    weak_concepts = weak.get("concepts") or []
    chain_weak_pack_ids = set(map(str, chain.get("weak_concept_pack_ids") or []))
    if not weak_concepts or not (chain_weak_pack_ids & pack_ids):
        raise RuntimeError("Weak-concept KG consumer is not linked to the evidence chain")

    recs = _get(
        client,
        base,
        f"/api/v1/tutor/students/{student_id}/recommendations",
        teacher_headers,
    )
    rec_pack_ids = {str(r.get("pack_id")) for r in recs or [] if r.get("pack_id")}
    if not (rec_pack_ids & pack_ids):
        raise RuntimeError("Tutor recommendations are not linked to the same CurriculumPack")

    parent_row = next(
        (row for row in parent_progress or [] if str(row.get("student_id")) == str(student_id)),
        None,
    )
    if not parent_row:
        raise RuntimeError("Reference parent is not linked to the selected mastery-flag student")
    parent_topics = parent_row.get("weak_topics") or []
    if not any(_topic_match(t.get("topic_display"), topic) for t in parent_topics):
        raise RuntimeError("Parent portal progress does not show the same weak topic")

    briefing = _get(
        client,
        base,
        f"/api/v1/parent-copilot/students/{student_id}/briefing",
        parent_headers,
    )
    if not briefing.get("grounded") or str(briefing.get("pack_id")) not in pack_ids:
        raise RuntimeError("Parent Copilot briefing is not grounded on the same CurriculumPack")

    ledger = {
        "tenant": chain["tenant_slug"],
        "flag_id": chain["flag_id"],
        "student_id": student_id,
        "topic": topic,
        "curriculum_pack_ids": chain["curriculum_pack_ids"],
        "question_paper_ids": chain["question_paper_ids"],
        "exam_ids": [e["exam_id"] for e in chain["exams"]],
        "approved_evaluation_ids": chain["approved_evaluation_ids"],
        "mastery_pct": chain["mastery"]["mastery_pct"],
        "weak_concept_count": chain["weak_concept_count"],
        "student_consumer": "verified",
        "tutor_pack_ids": sorted(rec_pack_ids),
        "parent_pack_id": briefing.get("pack_id"),
        "grounded": chain["grounded"],
        "fallback": chain["fallback"],
    }
    print("\nLearning Intelligence evidence ledger:")
    for key, value in ledger.items():
        print(f"  {key}: {value}")
    print("\nLEARNING INTELLIGENCE EVIDENCE: PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"\nLEARNING INTELLIGENCE EVIDENCE: FAIL\n{exc}")
        raise SystemExit(1)
