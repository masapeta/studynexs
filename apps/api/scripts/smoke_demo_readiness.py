"""Demo-readiness smoke: log in once as the principal and hit every page's on-load
endpoints over real HTTP, exactly as the admin-web does. Catches anything that would
500 or blank a page in front of the school. Read-only.

Run (with the API server up on :8000):  python scripts/smoke_demo_readiness.py
       (canonical):                      python scripts/smoke_reference_school.py
Uses ``localhost:8000`` first, then ``127.0.0.1:8000`` — avoids stale local uvicorn stealing traffic on Windows.
"""
from __future__ import annotations

import os
import sys
from datetime import date
from pathlib import Path

_scripts_dir = Path(__file__).resolve().parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

import httpx
from reference_school_config import DEMO_PASSWORD, LOGIN_PRINCIPAL, LOGIN_STUDENT, TENANT_SLUG

BASE = os.environ.get("SMOKE_BASE_URL", "").rstrip("/")
H = {"X-Tenant-Slug": TENANT_SLUG}
TODAY = date.today().isoformat()

results: list[tuple[bool, int, str, str]] = []


def _resolve_base(client: httpx.Client) -> str:
    """Pick a healthy API base URL.

    Docker on Windows often listens on ``localhost:8000`` while a stale local
    ``uvicorn --host 127.0.0.1 --port 8000`` returns 500 and steals smoke traffic.
    """
    if BASE:
        return BASE
    candidates = ("http://localhost:8000", "http://127.0.0.1:8000")
    for base in candidates:
        try:
            r = client.get(base + "/health", timeout=5)
            if r.status_code < 400:
                return base
        except Exception:  # noqa: BLE001
            continue
    return candidates[0]


def check(client: httpx.Client, base: str, label: str, path: str) -> dict | list | None:
    try:
        r = client.get(base + path, headers=H, timeout=30)
    except Exception as exc:  # noqa: BLE001
        results.append((False, 0, label, f"EXC {exc}"))
        return None
    ok = r.status_code < 400
    info = ""
    body = None
    try:
        body = r.json()
        if isinstance(body, list):
            info = f"list[{len(body)}]"
        elif isinstance(body, dict):
            if "items" in body:
                info = f"items[{len(body['items'])}] total={body.get('total')}"
            elif "data" in body:
                d = body["data"]
                info = f"data[{len(d)}]" if isinstance(d, list) else "data{obj}"
            else:
                info = "keys=" + ",".join(list(body.keys())[:5])
    except Exception:  # noqa: BLE001
        info = (r.text or "")[:50]
    results.append((ok, r.status_code, label, info))
    return body


def main() -> int:
    client = httpx.Client(follow_redirects=True)
    base = _resolve_base(client)

    try:
        health = client.get(base + "/health", timeout=10)
    except Exception as exc:  # noqa: BLE001
        print(f"API unreachable at {base}: {exc}")
        print("Start the stack: docker compose -f infra/docker/docker-compose.dev.yml up -d")
        return 1
    if health.status_code >= 400:
        print(f"API unhealthy at {base} (GET /health -> {health.status_code})")
        print("If Docker is running, kill any stale local uvicorn on port 8000:")
        print("  Get-Process python | Where-Object { $_.Path -like '*studynexs*' } | Stop-Process")
        print("Then: docker compose -f infra/docker/docker-compose.dev.yml restart api")
        return 1

    if not BASE:
        print(f"API base: {base}\n")

    # One login (respects the 5/15min rate limit).
    r = client.post(
        base + "/api/v1/auth/login", headers=H,
        json={"username": LOGIN_PRINCIPAL, "password": DEMO_PASSWORD}, timeout=30,
    )
    if r.status_code >= 400:
        print(f"LOGIN FAILED {r.status_code}: {r.text[:200]}")
        return 1
    j = r.json()
    token = j.get("access_token") or (j.get("data") or {}).get("access_token")
    if not token:
        print(f"LOGIN: no token in response keys={list(j.keys())}")
        return 1
    H["Authorization"] = f"Bearer {token}"
    print("login OK\n")

    # Resolve a Class 10-A id + a subject + an exam to exercise detail endpoints.
    classes = check(client, base, "classes (Classes page)", "/api/v1/academic/classes?page_size=100")
    items = (classes or {}).get("items") or (classes or {}).get("data") or []
    cid = next(
        (c["id"] for c in items if c.get("grade") == "Class 10" and c.get("section") == "A"),
        items[0]["id"] if items else None,
    )
    check(client, base, "subjects", f"/api/v1/academic/subjects?class_id={cid}")
    exams = check(client, base, "exams (Exams page)", f"/api/v1/exams?class_id={cid}")
    ex: list = []
    if isinstance(exams, dict):
        ex = exams.get("items") or exams.get("data") or []
    elif isinstance(exams, list):
        ex = exams
    eid = ex[0]["id"] if ex else None

    # Every page's on-load reads.
    check(client, base, "dashboard: students count", "/api/v1/academic/students?page_size=1")
    check(client, base, "dashboard: classes count", "/api/v1/academic/classes?page_size=1")
    check(client, base, "dashboard: notices", "/api/v1/notices")
    check(client, base, "dashboard: fees/stats", "/api/v1/fees/stats")
    check(client, base, "dashboard: attendance", f"/api/v1/attendance/school-summary?date={TODAY}")
    check(client, base, "students list", "/api/v1/academic/students?page=1&page_size=20")
    check(client, base, "staff list", "/api/v1/users?role=teacher&search=&page_size=20")
    check(client, base, "ai: usage card", "/api/v1/ai/usage")
    check(client, base, "ai: question papers", "/api/v1/ai/question-papers")
    check(client, base, "report cards list", f"/api/v1/ai/report-cards?class_id={cid}")
    check(client, base, "report cards: roster", f"/api/v1/academic/students?class_id={cid}&page_size=100")
    check(client, base, "attendance: class/date", f"/api/v1/attendance/class/{cid}?date={TODAY}")
    if eid:
        check(client, base, "exams: marks", f"/api/v1/exams/{eid}/marks")
    check(client, base, "timetable: class", f"/api/v1/timetable/class/{cid}")
    check(client, base, "timetable: teachers", "/api/v1/users?role=teacher&page_size=100")
    check(client, base, "finance: stats", "/api/v1/fees/stats")
    check(client, base, "finance: recent", "/api/v1/fees/recent?limit=10")
    check(client, base, "settings: profile", "/api/v1/school/profile")
    check(client, base, "settings: academic-years", "/api/v1/school/academic-years")

    # Demo v1 — curriculum intelligence (Journey 0)
    packs_body = check(client, base, "curriculum: packs", "/api/v1/curriculum/packs")
    pack_id = None
    if isinstance(packs_body, dict):
        packs_list = packs_body.get("data") or []
        approved = next(
            (p for p in packs_list if p.get("status") == "approved" and "Mathematics" in (p.get("subject_name") or "")),
            packs_list[0] if packs_list else None,
        )
        if approved:
            pack_id = approved.get("id")
    if pack_id:
        check(client, base, "curriculum: pack detail", f"/api/v1/curriculum/packs/{pack_id}")
        grounding = check(
            client, base, "curriculum: grounding", f"/api/v1/curriculum/packs/{pack_id}/grounding"
        )
        audit = check(client, base, "curriculum: audit", f"/api/v1/curriculum/packs/{pack_id}/audit")
        if isinstance(grounding, dict):
            g = grounding.get("data") or {}
            if not g.get("source_count"):
                results.append((False, 0, "curriculum: grounding indexed", "source_count=0"))
        if isinstance(audit, dict):
            events = audit.get("data") or []
            if not events:
                results.append((False, 0, "curriculum: audit events", "empty"))
    else:
        results.append((False, 0, "curriculum: approved pack", "none found"))

    # Demo v1 — assessment loop (Journey 2)
    qp_body = check(client, base, "demo: question papers", "/api/v1/ai/question-papers")
    if isinstance(qp_body, dict):
        papers = qp_body.get("data") or []
        approved_demo = any(p.get("status") == "approved" for p in papers)
        if not approved_demo:
            results.append((False, 0, "demo: approved QP seeded", "none"))

    maths_exam_id = None
    if isinstance(exams, dict):
        for ex_item in ex or []:
            title = (ex_item.get("title") or "").lower()
            if "quadratic" in title or ex_item.get("can_evaluate_sheets"):
                maths_exam_id = ex_item.get("id")
                break
    if not maths_exam_id and ex:
        maths_exam_id = ex[0].get("id")
    if maths_exam_id:
        ev_body = check(
            client, base, "demo: eval list", f"/api/v1/exams/{maths_exam_id}/evaluations"
        )
        if isinstance(ev_body, dict):
            evals = ev_body.get("data") or []
            suggested = [e for e in evals if e.get("status") == "suggested"]
            approved = [e for e in evals if e.get("status") == "approved"]
            if not suggested and not approved:
                results.append((False, 0, "demo: eval evidence", "no suggested or approved eval"))

    # Demo v1 — parent class work notice (Journey 3/4)
    notices_body = check(client, base, "demo: class work notice", "/api/v1/notices")
    if isinstance(notices_body, dict):
        notices = notices_body.get("data") or notices_body.get("items") or []
        if not any("class work" in (n.get("title") or "").lower() for n in notices):
            results.append((False, 0, "demo: class work notice", "not found"))

    # Tutor + student portal (G1-02 E2E)
    check(client, base, "tutor: tts status (public)", "/api/v1/tutor/tts/status")
    stu = client.post(
        base + "/api/v1/auth/login",
        headers={"X-Tenant-Slug": TENANT_SLUG},
        json={"username": LOGIN_STUDENT, "password": DEMO_PASSWORD},
        timeout=30,
    )
    if stu.status_code < 400:
        sj = stu.json()
        stoken = sj.get("access_token") or (sj.get("data") or {}).get("access_token")
        if stoken:
            sh = {"X-Tenant-Slug": TENANT_SLUG, "Authorization": f"Bearer {stoken}"}
            try:
                ctx = client.get(base + "/api/v1/portal/context", headers=sh, timeout=30)
                info = ""
                sid = None
                if ctx.status_code < 400:
                    body = ctx.json()
                    sid = (body.get("data") or {}).get("student_id")
                    info = f"student_id={sid}" if sid else "no student_id"
                results.append((ctx.status_code < 400, ctx.status_code, "student: portal context", info))
                if sid:
                    rec = client.get(
                        base + f"/api/v1/tutor/students/{sid}/recommendations",
                        headers=sh,
                        timeout=30,
                    )
                    n = ""
                    try:
                        d = rec.json().get("data") or []
                        n = f"recs[{len(d)}]"
                    except Exception:  # noqa: BLE001
                        n = rec.text[:40]
                    results.append((rec.status_code < 400, rec.status_code, "student: tutor recs", n))
            except Exception as exc:  # noqa: BLE001
                results.append((False, 0, "student: portal/tutor", str(exc)[:80]))
        else:
            results.append((False, stu.status_code, "student: login", "no token"))
    else:
        results.append((False, stu.status_code, "student: login", stu.text[:80]))

    print(f"\n{'RES':<4} {'CODE':<5} {'ENDPOINT':<32} INFO")
    print("-" * 72)
    fails = 0
    for ok, code, label, info in results:
        if not ok:
            fails += 1
        print(f"{'OK ' if ok else 'FAIL':<4} {code:<5} {label:<32} {info}")
    print("-" * 72)
    print(f"{'ALL GREEN' if fails == 0 else str(fails) + ' FAILED'}  ({len(results)} checks)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
