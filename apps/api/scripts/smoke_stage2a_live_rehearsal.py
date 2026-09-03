"""Stage 2A live rehearsal — real AI gateway, no seed/manual pack data.

Flow:
  1. Propose draft pack from pasted syllabus/TOC (LLM gateway extraction)
  2. Review pack detail
  3. Approve pack
  4. Poll Academic Intelligence Ready
  5. Generate grounded lesson plan + question paper from that pack
  6. Verify citations/grounding trace to the pack

Run: python scripts/smoke_stage2a_live_rehearsal.py
Requires API + Qdrant + a configured non-stub AI provider key.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

_scripts_dir = Path(__file__).resolve().parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

import httpx
from reference_school_config import (
    DEMO_PASSWORD,
    LOGIN_CLASS_INCHARGE,
    LOGIN_PRINCIPAL,
    TENANT_SLUG,
)

BASE = os.environ.get("SMOKE_BASE_URL", "").rstrip("/") or "http://127.0.0.1:8000"
H = {"X-Tenant-Slug": TENANT_SLUG}
SMOKE_LOGIN_USER = os.environ.get("SMOKE_LOGIN_USER", LOGIN_PRINCIPAL)
SMOKE_APPROVER_USER = os.environ.get("SMOKE_APPROVER_USER", LOGIN_PRINCIPAL)
SMOKE_ACCESS_TOKEN = os.environ.get("SMOKE_ACCESS_TOKEN", "").strip()
SMOKE_APPROVER_ACCESS_TOKEN = os.environ.get("SMOKE_APPROVER_ACCESS_TOKEN", "").strip()

# Structured syllabus for reliable LLM chapter → topic extraction (NCERT Class 8 Science outline)
SYLLABUS_TOC = """
Board: CBSE | Subject: Science | Class: 8 | Book: NCERT Science

Chapter 1: Crop Production and Management
  Topic: Agricultural practices and crop seasons
  Topic: Soil preparation, sowing, and irrigation
  Topic: Manure, fertilizers, weed control, harvesting and storage

Chapter 2: Microorganisms — Friend and Foe
  Topic: Microorganisms and their habitats
  Topic: Friendly microorganisms in soil and food
  Topic: Harmful microorganisms, disease prevention, food preservation

Chapter 3: Synthetic Fibres and Plastics
  Topic: Types and characteristics of synthetic fibres
  Topic: Plastics — uses, types, and environmental concerns

Chapter 4: Materials — Metals and Non-Metals
  Topic: Physical properties of metals and non-metals
  Topic: Chemical properties — reaction with oxygen, water, and acids
  Topic: Uses of metals and non-metals in daily life

Chapter 5: Coal and Petroleum
  Topic: Natural resources — exhaustible and inexhaustible
  Topic: Coal, petroleum, fossil fuels, and conservation
"""


def _login(client: httpx.Client, *, username: str, access_token: str = "") -> dict[str, str]:
    if access_token:
        return {**H, "Authorization": f"Bearer {access_token}"}
    r = client.post(
        f"{BASE}/api/v1/auth/login",
        headers=H,
        json={"username": username, "password": DEMO_PASSWORD},
    )
    if r.status_code == 429:
        raise RuntimeError(
            f"Login rate-limited for {username!r}. "
            "Wait 15 minutes, set SMOKE_ACCESS_TOKEN / SMOKE_APPROVER_ACCESS_TOKEN, "
            "or use a different SMOKE_LOGIN_USER / SMOKE_APPROVER_USER "
            f"(Class 10-A incharge; use grade Class 10 section A)."
        )
    r.raise_for_status()
    token = r.json()["access_token"]
    return {**H, "Authorization": f"Bearer {token}"}


def _data(body: dict) -> dict | list:
    if isinstance(body, dict) and "data" in body:
        return body["data"]
    return body


def _pick_class_subject_year(
    client: httpx.Client, auth: dict, *, login_user: str
) -> tuple[dict, dict, dict]:
    classes = client.get(f"{BASE}/api/v1/academic/classes?page_size=100", headers=auth)
    classes.raise_for_status()
    items = classes.json().get("items") or classes.json().get("data") or []
    prefer_10a = login_user == LOGIN_CLASS_INCHARGE
    if prefer_10a:
        cls = next(
            (c for c in items if c.get("grade") == "Class 10" and c.get("section") == "A"),
            None,
        )
    else:
        cls = next(
            (c for c in items if "8" in str(c.get("grade", "")) and c.get("section") == "A"),
            next((c for c in items if "8" in str(c.get("grade", ""))), None),
        )
    if not cls and items:
        cls = items[0]
    if not cls:
        raise RuntimeError("No class found on reference tenant")

    subs = client.get(
        f"{BASE}/api/v1/academic/subjects?class_id={cls['id']}",
        headers=auth,
    )
    subs.raise_for_status()
    sub_items = _data(subs.json())
    if not isinstance(sub_items, list):
        sub_items = []
    science = next(
        (s for s in sub_items if "science" in (s.get("name") or "").lower()),
        sub_items[0] if sub_items else None,
    )
    if not science:
        raise RuntimeError(f"No subject found for class {cls.get('grade')}")

    year_id = cls.get("academic_year_id")
    year: dict = {"id": year_id, "name": "from class"}
    if not year_id:
        years = client.get(f"{BASE}/api/v1/school/academic-years", headers=auth)
        years.raise_for_status()
        year_list = _data(years.json())
        if not isinstance(year_list, list) or not year_list:
            raise RuntimeError("No academic year found")
        year = year_list[0]
        year_id = year["id"]

    return cls, science, year


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
            f"rag={last.get('rag_ready')} vectors={last.get('rag_vector_count')} "
            f"topics={last.get('retrievable_topic_count')}"
        )
        if last.get("academic_intelligence_ready"):
            return last
        if phase == "failed":
            # one retry
            print("  retrying RAG index…")
            rr = client.post(
                f"{BASE}/api/v1/curriculum/packs/{pack_id}/retry-rag-index",
                headers=auth,
            )
            if rr.status_code < 400:
                print("  retry accepted")
            else:
                print(f"  retry failed: {rr.status_code} {rr.text[:200]}")
        time.sleep(3)
    return last


def _assert_real_llm_available() -> None:
    """Fail fast when the API would use the dev stub (no provider API key)."""
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
            f"No API key for AI_DEFAULT_PROVIDER={primary!r}. "
            "The gateway falls back to stub, which cannot extract curriculum topics. "
            "Set GEMINI_API_KEY (or OPENAI/ANTHROPIC) in apps/api/.env and restart the API."
        )


def main() -> int:
    print(f"Stage 2A live rehearsal — API {BASE}\n")
    try:
        _assert_real_llm_available()
    except RuntimeError as exc:
        print(f"PREFLIGHT FAIL: {exc}")
        return 2
    client = httpx.Client(timeout=180.0)

    health = client.get(f"{BASE}/health")
    if health.status_code >= 400:
        print(f"API unhealthy: {health.status_code}")
        return 1

    auth = _login(client, username=SMOKE_LOGIN_USER, access_token=SMOKE_ACCESS_TOKEN)
    cls, science, year = _pick_class_subject_year(client, auth, login_user=SMOKE_LOGIN_USER)
    class_id, subject_id, year_id = cls["id"], science["id"], year["id"]
    print(f"Target: {cls.get('grade')} {cls.get('section')} · {science.get('name')} · year {year.get('name', year_id)}")

    # --- Step 1: Propose from real TOC ---
    print("\n[1] Propose draft pack (real LLM extraction)…")
    propose = client.post(
        f"{BASE}/api/v1/curriculum/onboarding/propose",
        headers=auth,
        json={
            "class_id": class_id,
            "subject_id": subject_id,
            "academic_year_id": year_id,
            "board": "CBSE",
            "book_title": "NCERT Science Class 8",
            "input_type": "toc",
            "curriculum_text": SYLLABUS_TOC,
        },
    )
    if propose.status_code >= 400:
        print(f"PROPOSE FAILED: {propose.status_code}\n{propose.text[:500]}")
        return 1
    pdata = _data(propose.json())
    pack = pdata["pack"]
    pack_id = pack["id"]
    print(
        f"  pack_id={pack_id} chapters={pdata.get('chapters_proposed')} "
        f"topics={pdata.get('topics_proposed')} credits={pdata.get('credits_used')}"
    )
    if pdata.get("topics_proposed", 0) < 1:
        notes = pdata.get("low_confidence_notes") or []
        print(f"  low_confidence_notes: {notes}")
        print("FAIL: extraction produced no topics — cannot approve")
        return 1

    # --- Step 2: Review ---
    print("\n[2] Review pack detail…")
    detail = client.get(f"{BASE}/api/v1/curriculum/packs/{pack_id}", headers=auth)
    detail.raise_for_status()
    d = _data(detail.json())
    ch0 = (d.get("chapters") or [{}])[0]
    print(f"  first chapter: {ch0.get('number')} {ch0.get('title')}")
    topics = ch0.get("topics") or []
    if topics:
        print(f"  first topic: {topics[0].get('title')}")

    # --- Step 3: Approve ---
    print("\n[3] Approve pack…")
    approve_auth = auth
    if SMOKE_APPROVER_USER != SMOKE_LOGIN_USER or SMOKE_APPROVER_ACCESS_TOKEN:
        approve_auth = _login(
            client,
            username=SMOKE_APPROVER_USER,
            access_token=SMOKE_APPROVER_ACCESS_TOKEN,
        )
    appr = client.post(
        f"{BASE}/api/v1/curriculum/packs/{pack_id}/approve",
        headers=approve_auth,
    )
    if appr.status_code >= 400:
        print(f"APPROVE FAILED: {appr.status_code}\n{appr.text[:400]}")
        return 1
    print(f"  status={_data(appr.json()).get('status', 'approved')}")

    # --- Step 4: Intelligence Ready ---
    print("\n[4] Poll Academic Intelligence Ready…")
    intel = _poll_intelligence(client, auth, pack_id)
    if not intel.get("academic_intelligence_ready"):
        print(f"FAIL: not intelligence-ready — {intel.get('message')}")
        return 1
    print(f"  OK: {intel.get('message')}")

    # Pick a topic from the pack for generation
    focus_chapter = ch0.get("title") or "Unit 1"
    focus_topic = topics[0].get("title") if topics else "Agricultural Practices"

    # --- Step 5a: Grounded lesson plan ---
    print("\n[5a] Generate grounded lesson plan (Teacher Copilot)…")
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
        print(f"LESSON PLAN FAILED: {lp.status_code}\n{lp.text[:500]}")
        return 1
    plan = lp.json()
    print(
        f"  plan_id={plan.get('id')} grounded={plan.get('grounded')} "
        f"pack_id={plan.get('pack_id')} model={plan.get('ai_model')}"
    )
    segments = plan.get("segments") or []
    seg_citations = [s.get("citations") for s in segments if s.get("citations")]
    gsrc = plan.get("grounding_sources") or []
    print(f"  segments={len(segments)} with_citations={len(seg_citations)} grounding_sources={len(gsrc)}")
    if not plan.get("grounded") or str(plan.get("pack_id")) != str(pack_id):
        print("FAIL: lesson plan not grounded to pack")
        return 1
    if not seg_citations and not gsrc:
        print("FAIL: lesson plan has no visible citations/grounding")
        return 1

    # --- Step 5b: Grounded question paper ---
    print("\n[5b] Generate grounded question paper…")
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
            "title": f"Stage 2A rehearsal — {focus_topic}",
        },
    )
    if qp.status_code >= 400:
        print(f"QP FAILED: {qp.status_code}\n{qp.text[:500]}")
        return 1
    paper = qp.json()
    print(
        f"  paper_id={paper.get('id')} grounded={paper.get('grounded')} "
        f"pack_id={paper.get('pack_id')} model={paper.get('ai_model')}"
    )
    gsrc_p = paper.get("grounding_sources") or []
    all_q = [q for sec in (paper.get("sections") or []) for q in (sec.get("questions") or [])]
    cited = [q for q in all_q if q.get("citations")]
    print(f"  questions={len(all_q)} cited={len(cited)} grounding_sources={len(gsrc_p)}")
    if not paper.get("grounded") or str(paper.get("pack_id")) != str(pack_id):
        print("FAIL: question paper not grounded to pack")
        return 1
    if not cited and not gsrc_p:
        print("FAIL: question paper has no visible citations/grounding")
        return 1

    # --- Step 6: Traceability sample ---
    print("\n[6] Citation traceability sample")
    if gsrc:
        sample = gsrc[0]
        print(f"  lesson grounding[0]: {json.dumps(sample, default=str)[:200]}")
    if gsrc_p:
        sample_p = gsrc_p[0]
        print(f"  paper grounding[0]: {json.dumps(sample_p, default=str)[:200]}")
    if cited:
        print(f"  first question citation indices: {cited[0].get('citations')}")
        print(f"  first question text: {(cited[0].get('text') or '')[:80]}…")

    print("\n" + "=" * 60)
    print("STAGE 2A LIVE REHEARSAL: PASS")
    print(f"pack_id={pack_id}")
    print("Academic Intelligence Ready -> grounded lesson plan + question paper verified.")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
