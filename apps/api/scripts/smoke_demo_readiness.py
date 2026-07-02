"""Demo-readiness smoke: log in once as the principal and hit every page's on-load
endpoints over real HTTP, exactly as the admin-web does. Catches anything that would
500 or blank a page in front of the school. Read-only.

Run (with the API server up on :8000):  python scripts/smoke_demo_readiness.py
Uses 127.0.0.1 (not localhost) to avoid Docker/WSL port conflicts on Windows.
"""
from __future__ import annotations

import sys
from datetime import date

import httpx

BASE = "http://127.0.0.1:8000"
H = {"X-Tenant-Slug": "test"}
TODAY = date.today().isoformat()

results: list[tuple[bool, int, str, str]] = []


def check(client: httpx.Client, label: str, path: str) -> dict | list | None:
    try:
        r = client.get(BASE + path, headers=H, timeout=30)
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

    # One login (respects the 5/15min rate limit).
    r = client.post(
        BASE + "/api/v1/auth/login", headers=H,
        json={"username": "principal", "password": "Demo@1234"}, timeout=30,
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
    classes = check(client, "classes (Classes page)", "/api/v1/academic/classes?page_size=100")
    items = (classes or {}).get("items") or (classes or {}).get("data") or []
    cid = next(
        (c["id"] for c in items if c.get("grade") == "Class 10" and c.get("section") == "A"),
        items[0]["id"] if items else None,
    )
    check(client, "subjects", f"/api/v1/academic/subjects?class_id={cid}")
    exams = check(client, "exams (Exams page)", f"/api/v1/exams?class_id={cid}")
    ex: list = []
    if isinstance(exams, dict):
        ex = exams.get("items") or exams.get("data") or []
    elif isinstance(exams, list):
        ex = exams
    eid = ex[0]["id"] if ex else None

    # Every page's on-load reads.
    check(client, "dashboard: students count", "/api/v1/academic/students?page_size=1")
    check(client, "dashboard: classes count", "/api/v1/academic/classes?page_size=1")
    check(client, "dashboard: notices", "/api/v1/notices")
    check(client, "dashboard: fees/stats", "/api/v1/fees/stats")
    check(client, "dashboard: attendance", f"/api/v1/attendance/school-summary?date={TODAY}")
    check(client, "students list", "/api/v1/academic/students?page=1&page_size=20")
    check(client, "staff list", "/api/v1/users?role=teacher&search=&page_size=20")
    check(client, "ai: usage card", "/api/v1/ai/usage")
    check(client, "ai: question papers", "/api/v1/ai/question-papers")
    check(client, "report cards list", f"/api/v1/ai/report-cards?class_id={cid}")
    check(client, "report cards: roster", f"/api/v1/academic/students?class_id={cid}&page_size=100")
    check(client, "attendance: class/date", f"/api/v1/attendance/class/{cid}?date={TODAY}")
    if eid:
        check(client, "exams: marks", f"/api/v1/exams/{eid}/marks")
    check(client, "timetable: class", f"/api/v1/timetable/class/{cid}")
    check(client, "timetable: teachers", "/api/v1/users?role=teacher&page_size=100")
    check(client, "finance: stats", "/api/v1/fees/stats")
    check(client, "finance: recent", "/api/v1/fees/recent?limit=10")
    check(client, "settings: profile", "/api/v1/school/profile")
    check(client, "settings: academic-years", "/api/v1/school/academic-years")

    # Tutor + student portal (G1-02 E2E)
    check(client, "tutor: tts status (public)", "/api/v1/tutor/tts/status")
    stu = client.post(
        BASE + "/api/v1/auth/login",
        headers={"X-Tenant-Slug": "test"},
        json={"username": "student_demo", "password": "Demo@1234"},
        timeout=30,
    )
    if stu.status_code < 400:
        sj = stu.json()
        stoken = sj.get("access_token") or (sj.get("data") or {}).get("access_token")
        if stoken:
            sh = {"X-Tenant-Slug": "test", "Authorization": f"Bearer {stoken}"}
            try:
                ctx = client.get(BASE + "/api/v1/portal/context", headers=sh, timeout=30)
                info = ""
                sid = None
                if ctx.status_code < 400:
                    body = ctx.json()
                    sid = (body.get("data") or {}).get("student_id")
                    info = f"student_id={sid}" if sid else "no student_id"
                results.append((ctx.status_code < 400, ctx.status_code, "student: portal context", info))
                if sid:
                    rec = client.get(
                        BASE + f"/api/v1/tutor/students/{sid}/recommendations",
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
