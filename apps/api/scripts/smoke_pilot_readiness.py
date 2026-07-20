"""Pilot-readiness smoke for tenant `naagarjuna` (Naagarjuna Talent School).

Batch 1 reconciled architecture — 12 operational checks (P5).

Run (API on :8000):
  python scripts/smoke_pilot_readiness.py

Writes: docs/pilot/naagarjuna-talent-school/t0-evidence/smoke-results.json
"""
from __future__ import annotations

import json
import os
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import httpx

BASE = os.environ.get("SMOKE_BASE_URL", "http://localhost:8000")
TENANT = "naagarjuna"
WRONG_TENANT = "test"
H: dict[str, str] = {"X-Tenant-Slug": TENANT}
TODAY = date.today().isoformat()

results: list[dict] = []


def record(ok: bool, code: int, label: str, info: str = "") -> None:
    results.append(
        {
            "ok": ok,
            "code": code,
            "label": label,
            "info": info,
            "ts": datetime.now(timezone.utc).isoformat(),
        }
    )


def login(client: httpx.Client, *, tenant: str, username: str, password: str) -> str | None:
    r = client.post(
        BASE + "/api/v1/auth/login",
        headers={"X-Tenant-Slug": tenant},
        json={"username": username, "password": password},
        timeout=30,
    )
    if r.status_code >= 400:
        return None
    j = r.json()
    return j.get("access_token") or (j.get("data") or {}).get("access_token")


def main() -> int:
    client = httpx.Client(follow_redirects=True)
    ctx: dict = {}

    # 1 — Stack health
    try:
        hr = client.get(BASE + "/health", timeout=15)
        rd = client.get(BASE + "/ready", timeout=15)
        ok = hr.status_code == 200 and rd.status_code == 200
        record(ok, hr.status_code, "stack: health + ready", f"ready={rd.status_code}")
    except Exception as exc:  # noqa: BLE001
        record(False, 0, "stack: health + ready", str(exc))
        _print_and_write()
        return 1

    token = login(client, tenant=TENANT, username="principal", password="Demo@1234")
    if not token:
        record(False, 0, "auth: principal login", "failed — run seed_pilot_naagarjuna.py")
        _print_and_write()
        return 1
    H["Authorization"] = f"Bearer {token}"
    record(True, 200, "auth: principal login", f"tenant={TENANT}")

    # Resolve class + approved pack
    cls_r = client.get(BASE + "/api/v1/academic/classes?page_size=100", headers=H, timeout=30)
    classes = (cls_r.json() or {}).get("items") or (cls_r.json() or {}).get("data") or []
    cid = classes[0]["id"] if classes else None
    ctx["class_id"] = cid

    sub_r = client.get(
        BASE + f"/api/v1/academic/subjects?class_id={cid}" if cid else "/api/v1/academic/subjects",
        headers=H,
        timeout=30,
    )
    subjects = (sub_r.json() or {}).get("items") or (sub_r.json() or {}).get("data") or []
    sid = subjects[0]["id"] if subjects else None
    ctx["subject_id"] = sid

    pack_id = None
    if cid and sid:
        packs_r = client.get(
            BASE + f"/api/v1/curriculum/packs?class_id={cid}&subject_id={sid}",
            headers=H,
            timeout=30,
        )
        pack_items = (packs_r.json() or {}).get("data") or []
        approved = next((p for p in pack_items if p.get("status") == "approved"), None)
        pack_id = approved["id"] if approved else None
    ctx["pack_id"] = pack_id

    if not pack_id:
        record(False, 0, "curriculum: approved pack", "none — run seed_pilot_naagarjuna_curriculum.py")
    else:
        # 2 — Learning outcomes
        detail_r = client.get(
            BASE + f"/api/v1/curriculum/packs/{pack_id}",
            headers=H,
            timeout=30,
        )
        detail = (detail_r.json() or {}).get("data") or {}
        lo_count = 0
        for ch in detail.get("chapters") or []:
            lo_count += len(ch.get("learning_outcomes") or [])
            for t in ch.get("topics") or []:
                lo_count += len(t.get("learning_outcomes") or [])
        record(
            detail_r.status_code < 400 and lo_count > 0,
            detail_r.status_code,
            "learning outcomes",
            f"count={lo_count}",
        )

        # 3 — Audit trail
        audit_r = client.get(
            BASE + f"/api/v1/curriculum/packs/{pack_id}/audit",
            headers=H,
            timeout=30,
        )
        events = (audit_r.json() or {}).get("data") or []
        record(
            audit_r.status_code < 400 and len(events) > 0,
            audit_r.status_code,
            "audit trail",
            f"events={len(events)}",
        )

        # 4 — Knowledge graph
        graph_r = client.get(
            BASE + f"/api/v1/curriculum/packs/{pack_id}/graph",
            headers=H,
            timeout=30,
        )
        graph = (graph_r.json() or {}).get("data") or {}
        cc = graph.get("concept_count", 0)
        record(
            graph_r.status_code < 400 and cc >= 0,
            graph_r.status_code,
            "knowledge graph",
            f"concepts={cc} edges={graph.get('edge_count', 0)}",
        )

        # 5 — Hybrid RAG (grounding retrieval)
        ground_r = client.get(
            BASE + f"/api/v1/curriculum/packs/{pack_id}/grounding",
            headers=H,
            timeout=60,
        )
        ground = (ground_r.json() or {}).get("data") or {}
        src_n = ground.get("source_count", 0)
        record(
            ground_r.status_code < 400 and src_n > 0,
            ground_r.status_code,
            "hybrid RAG retrieval",
            f"sources={src_n}",
        )

        # 6 — Grounding facade
        record(
            ground_r.status_code < 400 and ground.get("pack_status") == "approved",
            ground_r.status_code,
            "grounding facade",
            f"status={ground.get('pack_status')} v={ground.get('pack_version')}",
        )

        # 11 — Approval pipeline (audit event)
        types = {e.get("event_type") for e in events}
        record(
            "pack_approved" in types,
            200 if "pack_approved" in types else 0,
            "approval pipeline",
            f"events={','.join(sorted(types)[:6])}",
        )

    # 7 — Question papers
    qp_r = client.get(BASE + "/api/v1/ai/question-papers", headers=H, timeout=30)
    record(qp_r.status_code < 400, qp_r.status_code, "question papers", "list OK")

    # 8 — Lesson plans (template + facade)
    if cid and sid and pack_id:
        lp_r = client.post(
            BASE + "/api/v1/lesson-plans/generate",
            headers=H,
            json={
                "class_id": cid,
                "subject_id": sid,
                "pack_id": pack_id,
                "topic": "Quadratic Equations",
                "generation_mode": "template",
            },
            timeout=120,
        )
        lp = lp_r.json()
        lp_data = lp.get("data") or lp
        grounded = bool(lp_data.get("grounded"))
        record(
            lp_r.status_code in (200, 201) and grounded,
            lp_r.status_code,
            "lesson plans (template + grounding)",
            f"grounded={grounded}",
        )
    else:
        record(False, 0, "lesson plans (template + grounding)", "missing class/subject/pack")

    # 9 — Cross-tenant isolation (token tenant mismatch)
    if pack_id:
        leak_r = client.get(
            BASE + f"/api/v1/curriculum/packs/{pack_id}",
            headers={**H, "X-Tenant-Slug": WRONG_TENANT},
            timeout=30,
        )
        record(
            leak_r.status_code in (403, 404),
            leak_r.status_code,
            "cross-tenant isolation",
            "denied" if leak_r.status_code in (403, 404) else "LEAK?",
        )
    else:
        record(False, 0, "cross-tenant isolation", "no pack_id")

    # 10 — Copilot routing (must not 500)
    if cid and sid and pack_id:
        cop_r = client.post(
            BASE + "/api/v1/lesson-plans/generate",
            headers=H,
            json={
                "class_id": cid,
                "subject_id": sid,
                "pack_id": pack_id,
                "topic": "Quadratic Equations",
                "generation_mode": "copilot",
            },
            timeout=180,
        )
        routed = cop_r.status_code in (200, 201, 400, 402, 422, 429)
        record(
            routed,
            cop_r.status_code,
            "copilot routing",
            "routed" if routed else cop_r.text[:80],
        )
    else:
        record(False, 0, "copilot routing", "missing class/subject/pack")

    return _print_and_write()


def _evidence_dir() -> Path:
    env = os.environ.get("SMOKE_EVIDENCE_DIR")
    if env:
        return Path(env)
    root = Path(__file__).resolve().parents[3]
    if (root / "docs").is_dir():
        return root / "docs" / "pilot" / "naagarjuna-talent-school" / "t0-evidence"
    return Path(__file__).resolve().parent / "output"


def _print_and_write() -> int:
    out_dir = _evidence_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "base_url": BASE,
        "tenant": TENANT,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "checks": results,
        "passed": sum(1 for r in results if r["ok"]),
        "total": len(results),
    }
    (out_dir / "smoke-results.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"\n{'RES':<4} {'CODE':<5} {'CHECK':<36} INFO")
    print("-" * 80)
    fails = 0
    for r in results:
        if not r["ok"]:
            fails += 1
        print(
            f"{'OK ' if r['ok'] else 'FAIL':<4} {r['code']:<5} {r['label']:<36} {r['info']}"
        )
    print("-" * 80)
    print(f"{'ALL GREEN' if fails == 0 else str(fails) + ' FAILED'}  ({len(results)}/12 checks)")
    print(f"Wrote {out_dir / 'smoke-results.json'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
