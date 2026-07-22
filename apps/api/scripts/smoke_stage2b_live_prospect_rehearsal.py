"""Stage 2B live prospect rehearsal — provision demo tenant then full Stage 2A AI flow.

Flow:
  1. POST /api/v1/demo/sessions (prospect tenant)
  2. Propose draft pack from pasted syllabus (real LLM)
  3. Review → approve → poll Academic Intelligence Ready
  4. Grounded lesson plan + question paper with citations
  5. Inline cleanup of prospect tenant

Run: python scripts/smoke_stage2b_live_prospect_rehearsal.py
Requires API + Qdrant + provider key (same as Stage 2A rehearsal).
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

_scripts_dir = Path(__file__).resolve().parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))
_api_root = _scripts_dir.parent
if str(_api_root) not in sys.path:
    sys.path.insert(0, str(_api_root))

import httpx

BASE = os.environ.get("SMOKE_BASE_URL", "").rstrip("/") or "http://127.0.0.1:8000"

# Class 10 Mathematics outline (matches prospect tenant shell: Class 10-A Math)
SYLLABUS_TOC = """
Board: SSC | Subject: Mathematics | Class: 10

Chapter 1: Real Numbers
  Topic: Euclid's division lemma
  Topic: Fundamental theorem of arithmetic
  Topic: Irrational numbers

Chapter 2: Polynomials
  Topic: Zeros of a polynomial
  Topic: Relationship between zeros and coefficients
  Topic: Division algorithm for polynomials

Chapter 3: Pair of Linear Equations in Two Variables
  Topic: Graphical method of solution
  Topic: Algebraic methods — substitution and elimination
  Topic: Consistency of linear equations
"""


def _data(body: dict) -> dict | list:
    if isinstance(body, dict) and "data" in body:
        return body["data"]
    return body


def _poll_intelligence(client: httpx.Client, auth: dict, pack_id: str, timeout_s: int = 120) -> dict:
    deadline = time.time() + timeout_s
    last: dict = {}
    while time.time() < deadline:
        r = client.get(
            f"{BASE}/api/v1/curriculum/packs/{pack_id}/intelligence-status",
            headers=auth,
        )
        r.raise_for_status()
        last = _data(r.json())
        phase = last.get("phase")
        print(
            f"  intelligence: phase={phase} kg={last.get('kg_ready')} "
            f"rag={last.get('rag_ready')} vectors={last.get('rag_vector_count')}"
        )
        if last.get("academic_intelligence_ready"):
            return last
        if phase == "failed":
            rr = client.post(
                f"{BASE}/api/v1/curriculum/packs/{pack_id}/retry-rag-index",
                headers=auth,
            )
            if rr.status_code < 400:
                print("  retry accepted")
        time.sleep(3)
    return last


def _assert_real_llm_available() -> None:
    from app.core.config import get_settings
    from app.modules.ai.gateway.factory import _provider_configured, get_provider

    s = get_settings()
    primary = (s.AI_DEFAULT_PROVIDER or "gemini").lower()
    if primary != "stub" and _provider_configured(primary):
        return
    if primary == "ollama" and (s.OLLAMA_BASE_URL or "").strip():
        return
    provider = get_provider(primary)
    if provider.name == "stub":
        raise RuntimeError(
            f"No API key for AI_DEFAULT_PROVIDER={primary!r}. Set GEMINI_API_KEY in apps/api/.env."
        )


async def _provision_session_async(client: httpx.Client) -> dict:
    """Provision via HTTP when possible; fall back to service on rate limit."""
    prov = client.post(f"{BASE}/api/v1/demo/sessions", json={"display_name": "Live Prospect"})
    if prov.status_code == 201:
        print("  provisioned via POST /api/v1/demo/sessions")
        return prov.json()["data"]

    if prov.status_code == 429:
        print("  HTTP provision rate-limited; using DemoSessionService (E2E covers HTTP path)")
        from app.core.database import async_session_factory
        from app.core.dependencies import get_redis
        from app.modules.demo.services.demo_session_service import DemoSessionService

        redis = await get_redis()
        async with async_session_factory() as db:
            svc = DemoSessionService(db, redis=redis)
            session, _refresh = await svc.create_session(display_name="Live Prospect")
            await db.commit()
            return session.model_dump()

    print(f"PROVISION FAIL: {prov.status_code}\n{prov.text[:400]}")
    raise SystemExit(1)


async def _cleanup_prospect_tenant(school_id: str, slug: str) -> None:
    from app.core.database import async_session_factory
    from app.db.models.school import School
    from app.modules.demo.services.demo_session_service import DemoSessionService

    async with async_session_factory() as db:
        school = await db.get(School, uuid.UUID(school_id))
        if school:
            school.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
            await db.commit()
        svc = DemoSessionService(db)
        swept = await svc.sweep_expired(enqueue_cleanup=False)
        if slug not in swept:
            await svc.purge_now(uuid.UUID(school_id))


async def async_main() -> int:
    print(f"Stage 2B live prospect rehearsal — API {BASE}\n")
    try:
        _assert_real_llm_available()
    except RuntimeError as exc:
        print(f"PREFLIGHT FAIL: {exc}")
        return 2

    client = httpx.Client(timeout=180.0)
    if client.get(f"{BASE}/health").status_code >= 400:
        print("API unhealthy")
        return 1

    print("[0] Provision prospect demo tenant…")
    session = await _provision_session_async(client)
    slug = session["tenant_slug"]
    school_id = session["school_id"]
    auth = {
        "X-Tenant-Slug": slug,
        "Authorization": f"Bearer {session['access_token']}",
    }
    print(f"  tenant={slug} session_token={'yes' if session.get('session_token') else 'no'}")

    classes = client.get(f"{BASE}/api/v1/academic/classes?page_size=10", headers=auth)
    classes.raise_for_status()
    items = classes.json().get("items") or []
    if not items:
        print("FAIL: no classes in prospect tenant")
        return 1
    cls = items[0]
    class_id = cls["id"]

    subs = client.get(f"{BASE}/api/v1/academic/subjects?class_id={class_id}", headers=auth)
    subs.raise_for_status()
    sub_items = _data(subs.json())
    if not isinstance(sub_items, list) or not sub_items:
        print("FAIL: no subjects")
        return 1
    science = sub_items[0]
    subject_id = science["id"]
    year_id = cls.get("academic_year_id")
    if not year_id:
        years = client.get(f"{BASE}/api/v1/school/academic-years", headers=auth)
        years.raise_for_status()
        year_list = _data(years.json())
        year_id = year_list[0]["id"]
    print(f"  target: {cls.get('grade')} {cls.get('section')} · {science.get('name')}")

    print("\n[1] Propose draft pack (real LLM)…")
    propose = client.post(
        f"{BASE}/api/v1/curriculum/onboarding/propose",
        headers=auth,
        json={
            "class_id": class_id,
            "subject_id": subject_id,
            "academic_year_id": year_id,
            "board": "SSC",
            "book_title": "SSC Mathematics Class 10",
            "input_type": "toc",
            "curriculum_text": SYLLABUS_TOC,
        },
    )
    if propose.status_code >= 400:
        print(f"PROPOSE FAIL: {propose.status_code}\n{propose.text[:500]}")
        return 1
    pdata = _data(propose.json())
    pack_id = pdata["pack"]["id"]
    if pdata.get("topics_proposed", 0) < 1:
        print(f"FAIL: no topics — {pdata.get('low_confidence_notes')}")
        return 1
    print(f"  pack_id={pack_id} topics={pdata.get('topics_proposed')}")

    print("\n[2] Approve pack…")
    appr = client.post(f"{BASE}/api/v1/curriculum/packs/{pack_id}/approve", headers=auth)
    if appr.status_code >= 400:
        print(f"APPROVE FAIL: {appr.status_code}\n{appr.text[:400]}")
        return 1

    print("\n[3] Poll Academic Intelligence Ready…")
    intel = _poll_intelligence(client, auth, pack_id)
    if not intel.get("academic_intelligence_ready"):
        print(f"FAIL: not intelligence-ready — {intel.get('message')}")
        return 1

    detail = client.get(f"{BASE}/api/v1/curriculum/packs/{pack_id}", headers=auth)
    detail.raise_for_status()
    d = _data(detail.json())
    ch0 = (d.get("chapters") or [{}])[0]
    topics = ch0.get("topics") or []
    focus_topic = topics[0].get("title") if topics else "Real Numbers"
    focus_chapter = ch0.get("title") or "Real Numbers"

    print("\n[4a] Grounded lesson plan…")
    lp = client.post(
        f"{BASE}/api/v1/lesson-plans/generate",
        headers=auth,
        json={
            "class_id": class_id,
            "subject_id": subject_id,
            "pack_id": pack_id,
            "generation_mode": "copilot",
            "topic": focus_topic,
            "chapter": focus_chapter,
        },
    )
    if lp.status_code >= 400:
        print(f"LESSON PLAN FAIL: {lp.status_code}\n{lp.text[:400]}")
        return 1
    plan = lp.json()
    if not plan.get("grounded"):
        print("FAIL: lesson plan not grounded")
        return 1

    print("\n[4b] Grounded question paper…")
    qp = client.post(
        f"{BASE}/api/v1/ai/question-papers/generate",
        headers=auth,
        json={
            "class_id": class_id,
            "subject_id": subject_id,
            "pack_id": pack_id,
            "topics": [focus_topic],
            "total_marks": 20,
            "duration_minutes": 45,
            "difficulty": "balanced",
            "title": f"Prospect rehearsal — {focus_topic}",
        },
    )
    if qp.status_code >= 400:
        print(f"QP FAIL: {qp.status_code}\n{qp.text[:400]}")
        return 1
    paper = qp.json()
    all_q = [q for sec in (paper.get("sections") or []) for q in (sec.get("questions") or [])]
    cited = [q for q in all_q if q.get("citations")]
    if not paper.get("grounded") or (not cited and not paper.get("grounding_sources")):
        print("FAIL: question paper not grounded/cited")
        return 1
    print(f"  questions={len(all_q)} cited={len(cited)}")

    print("\n[5] Expire + inline cleanup…")
    await _cleanup_prospect_tenant(school_id, slug)
    verify = client.get(f"{BASE}/api/v1/users/me", headers=auth)
    if verify.status_code not in (401, 403, 404, 410):
        print(f"WARN: tenant still reachable: {verify.status_code}")

    print("\n" + "=" * 60)
    print("STAGE 2B LIVE PROSPECT REHEARSAL: PASS")
    print(f"tenant={slug} pack_id={pack_id}")
    print("=" * 60)
    return 0


def main() -> int:
    return asyncio.run(async_main())


if __name__ == "__main__":
    raise SystemExit(main())
