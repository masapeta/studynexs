"""Adversarial generalization eval — paraphrases, cross-domain, follow-ups, ambiguity,
temporal, negative, and security probes against the LIVE assistant.

Captures the per-turn trace (route / capability / params / time_range) so failures can be
classified by architectural layer (spec §17, §24). This is a DISCOVERY tool: it reports a
matrix, it does not add question-specific hacks. Usage: python scripts/eval_adversarial.py
"""

from __future__ import annotations

import json
import sys
import urllib.request
from dataclasses import dataclass, field

BASE = "http://127.0.0.1:8000"
TENANT = "reference"
USERNAME = "principal"
PASSWORD = "Demo@1234"


def _post(path: str, body: dict, token: str | None = None) -> dict:
    data = json.dumps(body).encode()
    req = urllib.request.Request(f"{BASE}{path}", data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("X-Tenant-Slug", TENANT)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def login(username: str = USERNAME, password: str = PASSWORD) -> str:
    res = _post("/api/v1/auth/login", {"username": username, "password": password})
    token = res.get("access_token") or (res.get("data") or {}).get("access_token")
    if not token:
        print(f"LOGIN FAILED for {username}: {res}")
        sys.exit(1)
    return token


@dataclass
class Case:
    q: str
    category: str
    expect_route: str | None = None
    expect_capability: str | None = None
    expect_kind: str | None = None  # block kind
    expect_time_label: str | None = None
    note: str = ""


@dataclass
class Result:
    case: Case
    route: str | None
    capability: str | None
    kind: str | None
    time_label: str | None
    rows: int | None
    passed: bool
    reasons: list[str] = field(default_factory=list)


def turn(token: str, text: str, session_id: str | None) -> tuple[dict, dict, str | None]:
    res = _post(
        "/api/v1/workspace/assistant/turn", {"text": text, "session_id": session_id}, token
    )
    data = res.get("data") or res
    return data.get("block") or {}, data.get("trace") or {}, data.get("session_id")


def check(case: Case, block: dict, trace: dict) -> Result:
    kind = block.get("kind")
    route = trace.get("route")
    cap = trace.get("capability")
    time_label = (trace.get("time_range") or {}).get("label")
    rows = len(block.get("rows", [])) if kind == "table" else None
    reasons: list[str] = []
    if case.expect_route and route != case.expect_route:
        reasons.append(f"route {route}!={case.expect_route}")
    if case.expect_capability and cap != case.expect_capability:
        reasons.append(f"capability {cap}!={case.expect_capability}")
    if case.expect_kind and kind != case.expect_kind:
        reasons.append(f"kind {kind}!={case.expect_kind}")
    if case.expect_time_label and time_label != case.expect_time_label:
        reasons.append(f"time {time_label}!={case.expect_time_label}")
    return Result(case, route, cap, kind, time_label, rows, not reasons, reasons)


# ── Cases (paraphrases; NO code keys off these strings) ────────────────────────

CASES: list[Case] = [
    # Attendance paraphrases -> student_attendance
    Case("attendance of ARM0218", "Attendance", "STRUCTURED", "student_attendance", "metrics"),
    Case("What's ARM0218's attendance rate?", "Attendance", "STRUCTURED", "student_attendance"),
    Case("Tell me the attendance percentage for admission number ARM0218.", "Attendance",
         "STRUCTURED", "student_attendance"),
    Case("How many days has ARM0218 attended?", "Attendance", "STRUCTURED", "student_attendance"),
    Case("Show me ARM0218's attendance this month.", "Attendance", "STRUCTURED",
         "student_attendance", expect_time_label="this month"),
    # Teacher/class relationship -> teachers_for_class (all) vs class teacher (narrow)
    Case("Who teaches 2A?", "Teachers", "STRUCTURED", "teachers_for_class"),
    Case("Who handles class 2A?", "Teachers", "STRUCTURED", "teachers_for_class"),
    Case("Give me the teachers for 2A.", "Teachers", "STRUCTURED", "teachers_for_class"),
    Case("Show me all teachers and their assigned classes.", "Teachers", "STRUCTURED",
         "teachers_for_class", "table"),
    Case("Give me a teacher-class mapping.", "Teachers", "STRUCTURED", "teachers_for_class",
         "table"),
    Case("What subjects does Deepak Kumar teach?", "Teachers", "STRUCTURED",
         "teacher_assignments"),
    # Fees: collection vs balance; temporal
    Case("How much fee was collected today?", "Fees", "STRUCTURED", "fee_collection_period",
         expect_time_label="today"),
    Case("What was today's fee collection?", "Fees", "STRUCTURED", "fee_collection_period",
         expect_time_label="today"),
    Case("What did we collect this month?", "Fees", "STRUCTURED", "fee_collection_period",
         expect_time_label="this month"),
    Case("Show me fee collection from August 1 to August 31.", "Fees", "STRUCTURED",
         "fee_collection_period"),
    Case("What's ARM0218's outstanding balance?", "Fees", "STRUCTURED", "student_fees",
         "metrics"),
    Case("Which students owe more than 50%?", "Fees", "STRUCTURED", "students_fee_pending_over",
         "table"),
    # Classes / roster
    Case("List the students in 2A.", "Classes", "STRUCTURED", "class_roster", "table"),
    Case("students with attendance below 75%", "Attendance", "STRUCTURED",
         "low_attendance_students", "table"),
    # Document (no store -> honest)
    Case("what is the school's attendance policy?", "Document", "DOCUMENT", None, "guide"),
    Case("what does the fee policy say?", "Document", "DOCUMENT", None, "guide"),
    # Mixed
    Case("ARM0218 has attendance below 75%. What does the attendance policy say?", "CrossDomain",
         "MIXED", "student_attendance", "mixed"),
    # Negative / hallucination
    Case("attendance of NONEXISTENT999", "Negative", "STRUCTURED", "student_attendance",
         "not_found"),
    Case("Who teaches class 99Z?", "Negative", "STRUCTURED", "teachers_for_class"),
    # Ambiguity (depends on seed having >1 same-name; may be unique -> metrics)
    Case("attendance of Rahul", "Ambiguity", "STRUCTURED", "student_attendance"),
    # Entity normalization
    Case("attendance of arm0218", "EntityRes", "STRUCTURED", "student_attendance", "metrics"),
    Case("attendance of ARM 0218", "EntityRes", "STRUCTURED", "student_attendance"),
    # Action (recognized, refused)
    Case("mark ARM0218 absent today", "Action", "ACTION", None, "guide"),
    # Composition (multi-capability; no special-purpose tool)
    Case("Which classes have attendance below 75% and who are their teachers?", "Compose",
         "STRUCTURED", None, "table"),
    Case("Show students in 2A whose attendance is below 75% and fee dues exceed 1000.",
         "Compose", "STRUCTURED", None, "table"),
    Case("Give each class, number of students, attendance percentage, and class teacher.",
         "Compose", "STRUCTURED", None, "table"),
    Case("Show the top 5 students by outstanding fee balance and their classes.", "Compose",
         "STRUCTURED", None, "table"),
]


def run() -> None:
    token = login()
    results: list[Result] = []
    for c in CASES:
        try:
            block, trace, _ = turn(token, c.q, None)  # each independent (no session)
            results.append(check(c, block, trace))
        except Exception as exc:  # noqa: BLE001
            results.append(Result(c, None, None, None, None, None, False, [f"ERROR {exc}"]))

    # ── Report by category ──
    cats: dict[str, list[Result]] = {}
    for r in results:
        cats.setdefault(r.case.category, []).append(r)

    print("\n=== GENERALIZATION BY CATEGORY ===")
    for cat, rs in sorted(cats.items()):
        p = sum(1 for r in rs if r.passed)
        print(f"{cat:12} {p}/{len(rs)}")

    print("\n=== FAILURE MATRIX ===")
    any_fail = False
    for r in results:
        if not r.passed:
            any_fail = True
            print(
                f"Q: {r.case.q}\n   route={r.route} cap={r.capability} kind={r.kind} "
                f"time={r.time_label} rows={r.rows}\n   reasons: {', '.join(r.reasons)}\n"
            )
    if not any_fail:
        print("(no failures)")

    total_p = sum(1 for r in results if r.passed)
    print(f"\nTOTAL: {total_p}/{len(results)} passed")

    # ── Composition traces (show the DAG the planner built) ──
    print("\n=== COMPOSITION TRACES ===")
    for q in (
        "Which classes have attendance below 75% and who are their teachers?",
        "Show students in 2A whose attendance is below 75% and fee dues exceed 1000.",
        "Give each class, number of students, attendance percentage, and class teacher.",
        "Show the top 5 students by outstanding fee balance and their classes.",
    ):
        block, trace, _ = turn(token, q, None)
        ops = trace.get("operations") or []
        chain = " -> ".join(
            f"{o['capability']}[{o['row_count']}]"
            + (f" filt{o['filters']}" if o.get("filters") else "")
            for o in ops
        )
        print(
            f"Q: {q}\n   route={trace.get('route')} action={trace.get('action')} "
            f"kind={block.get('kind')} rows={len(block.get('rows', []))}\n   DAG: {chain or '(none)'}\n"
        )

    # ── Follow-up conversation traces (spec §5) ──
    print("\n=== FOLLOW-UP CONVERSATIONS ===")
    for convo in (
        [("What is ARM0218's attendance?", None), ("What about his fees?", None)],
        [("How much fee was collected in August?", None), ("What about September?", None)],
    ):
        sid: str | None = None
        print("--")
        for q, _ in convo:
            block, trace, sid = turn(token, q, sid)
            tl = (trace.get("time_range") or {}).get("label")
            print(f"Q: {q}\n   -> route={trace.get('route')} cap={trace.get('capability')} "
                  f"kind={block.get('kind')} time={tl} title={block.get('title')}")


if __name__ == "__main__":
    run()
