"""Phase 5 baseline benchmark — realistic NL questions vs. the LIVE Phase-4 assistant.

Analysis only: this does NOT change production code. It classifies each question's actual
behavior (route/capability/kind/rows + composed DAG) so we can produce an honest coverage map
and failure matrix. Coverage is judged from the observed result kind, not from a hardcoded
answer key (the reference tenant's data drives row counts).

Usage: python scripts/benchmark_phase5.py  (API on :8000, tenant reference, principal login)
"""

from __future__ import annotations

import json
import sys
import urllib.request
from collections import Counter
from dataclasses import dataclass, field

BASE = "http://127.0.0.1:8000"
TENANT = "reference"


def _post(path: str, body: dict, token: str | None = None) -> dict:
    data = json.dumps(body).encode()
    req = urllib.request.Request(f"{BASE}{path}", data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("X-Tenant-Slug", TENANT)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode())


def login(username: str, password: str = "Demo@1234") -> str | None:
    try:
        res = _post("/api/v1/auth/login", {"username": username, "password": password})
        return res.get("access_token") or (res.get("data") or {}).get("access_token")
    except Exception as exc:  # noqa: BLE001
        print(f"login failed for {username}: {exc}")
        return None


@dataclass
class Q:
    text: str
    category: str
    # expected coverage: what a correct system SHOULD do (analysis, not a hack)
    expect: str  # SUPPORTED | PARTIAL | NOT_SUPPORTED | AMBIGUOUS | SECURITY_DENY
    persona: str = "principal"


def turn(token, text, sid=None):
    res = _post("/api/v1/workspace/assistant/turn", {"text": text, "session_id": sid}, token)
    d = res.get("data") or res
    return d.get("block") or {}, d.get("trace") or {}, d.get("session_id")


# ── Benchmark questions (realistic; multiple paraphrases; personas) ────────────

QUESTIONS: list[Q] = []


def add(cat, expect, *texts, persona="principal"):
    for t in texts:
        QUESTIONS.append(Q(t, cat, expect, persona))


# LOOKUP / student
add("Lookup", "SUPPORTED",
    "attendance of ARM0218",
    "what's ARM0218's attendance rate?",
    "how regularly has ARM0218 attended?",
    "tell me the attendance percentage for admission number ARM0218",
    "fee balance of ARM0218",
    "show me ARM0218's profile")
# LIST / roster
add("List", "SUPPORTED",
    "list the students in 2A",
    "show all students in class 10 B",
    "list all staff",
    "give me all teachers and their classes")
# RELATIONSHIP
add("Relationship", "SUPPORTED",
    "who is the class teacher of 2A?",
    "who teaches 2A?",
    "what subjects does Deepak Kumar teach?",
    "which classes does Deepak Kumar handle?")
# COUNT / aggregation
add("Aggregation", "SUPPORTED",
    "how many students are in 2A?",
    "how many students are absent today in 2A?")
add("Aggregation", "PARTIAL",
    "how many students are there in the school?",
    "what is the average attendance across the school?")
# FILTER
add("Filter", "SUPPORTED",
    "students with attendance below 75%",
    "students with fees pending over 50%",
    "which students owe more than 10000?")
# RANKING
add("Ranking", "SUPPORTED",
    "top 5 students by outstanding fee balance and their classes",
    "show the 10 students with the highest fee dues")
add("Ranking", "PARTIAL",
    "which class has the lowest attendance?",
    "which class collected the most fees this month?")
# TEMPORAL / fees
add("Temporal", "SUPPORTED",
    "how much fee was collected today?",
    "what was today's fee collection?",
    "how much did we collect this month?",
    "fee collected in August",
    "fee collected between 2026-08-01 and 2026-08-31",
    "attendance of ARM0218 this month")
# TEMPORAL relationship (historical) — must NOT silently answer with current data
add("TemporalHistory", "NOT_SUPPORTED",
    "who was the class teacher of 2A in August?",
    "which class was ARM0218 in last year?")
# COMPOSITIONAL
add("Compositional", "SUPPORTED",
    "which classes have attendance below 75% and who are their teachers?",
    "show students in 2A whose attendance is below 75% and fee dues exceed 1000",
    "give each class, number of students, attendance percentage, and class teacher",
    "which teachers have classes with attendance below 75%?")
add("Compositional", "PARTIAL",
    "which class has the highest fee collection and what is its attendance?",
    "show the top 10 students by fee dues with their class and attendance")
# EXAMS / marks
add("Exams", "PARTIAL",
    "what are ARM0218's exam marks?",
    "show the marks for class 10 A",
    "which students failed the last exam?")
# TIMETABLE
add("Timetable", "NOT_SUPPORTED",
    "what is the timetable for 2A?",
    "who teaches 2A in the second period today?",
    "which teachers are free during second period?")
# OTHER DOMAINS present in ERP but likely not exposed to assistant
add("Transport", "NOT_SUPPORTED", "which students use transport route 1?", "show transport routes")
add("Library", "NOT_SUPPORTED", "which books are issued to ARM0218?", "list overdue library books")
add("Events", "NOT_SUPPORTED", "what events are scheduled this month?")
add("Admissions", "NOT_SUPPORTED", "how many admission enquiries this month?")
add("ReportCards", "NOT_SUPPORTED", "show ARM0218's report card")
add("Notices", "NOT_SUPPORTED", "what notices went out this week?")
# DOCUMENT / policy
add("Document", "NOT_SUPPORTED",
    "what is the school's attendance policy?",
    "what does the fee policy say?")
# MIXED
add("Mixed", "PARTIAL",
    "ARM0218 has attendance below 75%. What does the attendance policy say?")
# ACTION
add("Action", "NOT_SUPPORTED",
    "mark ARM0218 absent today",
    "record a fee payment of 5000 for ARM0218")
# NEGATIVE
add("Negative", "SUPPORTED",
    "attendance of NONEXISTENT999",
    "who teaches class 99Z?")
# AMBIGUITY
add("Ambiguity", "AMBIGUOUS", "attendance of Rahul", "show me Priya's fees")
# SECURITY (persona = student asking staff/other data)
add("Security", "SECURITY_DENY",
    "show me all teacher salaries",
    "list every student's fee dues",
    persona="student")


# ── Coverage judgement from observed behavior ─────────────────────────────────

def classify_actual(expect: str, block: dict, trace: dict) -> tuple[str, str]:
    """Return (verdict, note). Verdict in SUPPORTED/PARTIAL/NOT_SUPPORTED/AMBIGUOUS/
    SECURITY_DENY/UNEXPECTED — compared against the analysis expectation."""
    kind = block.get("kind")
    route = trace.get("route")
    action = trace.get("action")

    # Data answers that actually resolved.
    answered = kind in ("metrics", "table") and (
        kind == "metrics" or block.get("rows") is not None
    )
    guided = kind == "guide"  # honest "I can't answer that / go here"
    clarified = kind == "clarify"
    notfound = kind == "not_found"

    if expect == "SECURITY_DENY":
        # Denied if we did NOT return the sensitive data (guide/redirect is acceptable).
        return ("SECURITY_DENY" if not answered else "UNEXPECTED",
                f"route={route} kind={kind}")
    if expect == "AMBIGUOUS":
        # Either clarify (ideal) or a unique resolve (seed has unique names) is acceptable.
        v = "AMBIGUOUS" if clarified else ("SUPPORTED" if answered else "NOT_SUPPORTED")
        return (v, f"kind={kind}")
    if expect == "SUPPORTED":
        if answered or notfound:  # not_found is correct for nonexistent entities
            return ("SUPPORTED", f"route={route} kind={kind}")
        return ("NOT_SUPPORTED", f"got kind={kind} route={route}")
    if expect == "PARTIAL":
        if answered:
            return ("SUPPORTED", f"kind={kind}")  # better than expected
        return ("PARTIAL", f"kind={kind}")
    if expect == "NOT_SUPPORTED":
        # Honest guide / not_found is the CORRECT behavior for an unsupported domain.
        if guided or notfound or action in ("act", "document"):
            return ("NOT_SUPPORTED", f"honest kind={kind} action={action}")
        if answered:
            return ("UNEXPECTED", f"answered an unsupported domain? kind={kind}")
        return ("NOT_SUPPORTED", f"kind={kind}")
    return ("UNEXPECTED", f"kind={kind}")


def run():
    principal = login("principal")
    if not principal:
        sys.exit(1)
    # Real seed usernames (reference_school_config). Security cases MUST use a low-privilege
    # token; if it's missing, skip rather than silently fall back to principal (false pass).
    student = login("student_demo") or login("teacher6")
    if not student:
        print("WARN: no low-privilege login; security cases will be SKIPPED, not faked.\n")

    verdicts: Counter = Counter()
    by_cat: dict[str, Counter] = {}
    failures: list[str] = []
    rows_total = len(QUESTIONS)

    for q in QUESTIONS:
        if q.persona == "student" and not student:
            verdicts["SKIPPED"] += 1
            continue
        token = student if q.persona == "student" else principal
        try:
            block, trace, _ = turn(token, q.text)
            verdict, note = classify_actual(q.expect, block, trace)
        except Exception as exc:  # noqa: BLE001
            verdict, note = "ERROR", str(exc)
        verdicts[verdict] += 1
        by_cat.setdefault(q.category, Counter())[verdict] += 1
        if verdict in ("UNEXPECTED", "ERROR") or (
            q.expect == "SUPPORTED" and verdict != "SUPPORTED"
        ):
            failures.append(f"[{q.category}/{q.persona}] {q.text}\n    -> {verdict} ({note})")

    print(f"\n=== PHASE 5 BASELINE — {rows_total} questions ===\n")
    print("VERDICT TOTALS:")
    for v, n in verdicts.most_common():
        print(f"  {v:14} {n}")
    print("\nBY CATEGORY:")
    for cat in sorted(by_cat):
        parts = ", ".join(f"{v}:{n}" for v, n in by_cat[cat].most_common())
        print(f"  {cat:16} {parts}")
    print("\nNOTABLE (unexpected / regressions):")
    if failures:
        for f in failures:
            print("  " + f)
    else:
        print("  (none — all matched analysis expectations)")


if __name__ == "__main__":
    run()
