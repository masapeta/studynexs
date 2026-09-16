"""Fresh blind conversational benchmark (P1.2b evaluation).

Distinct from benchmark_followup.py: this judges EVERY turn of a conversation (not just the
last) so it measures whether the semantic state *evolves* across a chain rather than merely
copying fields forward. It targets UNSEEN combinations, not repeats of prior suites:

  previous domain + new metric        previous entity + new relationship
  previous class   + new subject      previous historical context + new month
  composite result + narrower Q       topic switch / implicit / ambiguous refs
  security after context carry-over

Blind: sends only {text}+role per turn on one session; expectations are private to the
evaluator and checked against the captured trace + block.

Usage (API on :8000, reference tenant):  python scripts/benchmark_conversation.py [--json out.json]
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request

BASE, TENANT, PASSWORD = "http://127.0.0.1:8000", "reference", "Demo@1234"
ROLE_LOGIN = {"principal": "principal", "teacher": "teacher6", "student": "student_demo",
              "parent": "parent_demo"}

# Reference anchors: ARM0242 = Class 10 A, 27 marks (Maths+English etc.); ARM0218 = Class 9 B.
# teacher6 teaches Class 10 A/B only. Incharge 2A = Deepak Kumar. Past months: July/August.

# Each conversation: role + ordered turns. Each turn has {text} + private expectations:
#   cap (acceptable capability set) · temporality · entity (key,val) · kind · outcome · note
CONVERSATIONS = [
    {
        "id": "evolving-chain", "role": "principal", "note": "state must EVOLVE, not just copy",
        "turns": [
            {"text": "show me ARM0242's marks",
             "cap": {"student_marks"}, "entity": ("student", "ARM0242"), "kind": {"table"},
             "outcome": "CORRECT"},
            {"text": "what about English?",
             "cap": {"student_marks"}, "entity": ("student", "ARM0242"),
             "outcome": "CORRECT", "note": "keep student, add subject=English"},
            {"text": "who scored highest?",
             "cap": {"subject_toppers", "class_results"}, "kind": {"table"},
             "outcome": "CORRECT",
             "note": "pivot to class ranking in English — class DERIVED from the student (P1.3)"},
            {"text": "what about last month?",
             "temporality": "PAST", "outcome": "CORRECT",
             "note": "apply a temporal window to the evolved query"},
        ],
    },
    {
        "id": "domain-then-metric", "role": "principal", "note": "prev domain + new metric",
        "turns": [
            {"text": "how much did we collect in July?",
             "cap": {"fee_collection_period"}, "temporality": "PAST", "kind": {"metrics"},
             "outcome": "CORRECT"},
            {"text": "and how many receipts?",
             "cap": {"fee_collection_period"}, "temporality": "PAST",
             "outcome": "CORRECT", "note": "metric switch keeps July+collection"},
        ],
    },
    {
        "id": "entity-then-relationship", "role": "principal",
        "note": "prev entity + new relationship (student -> who teaches their class)",
        "turns": [
            {"text": "which class is ARM0218 in?",
             "cap": {"student_profile"}, "entity": ("student", "ARM0218"), "outcome": "CORRECT"},
            {"text": "who teaches that class?",
             "cap": {"teachers_for_class"}, "outcome": "CORRECT",
             "note": "relationship pivot from student to their class's teachers"},
        ],
    },
    {
        "id": "class-then-subject", "role": "teacher", "note": "prev class + new subject",
        "turns": [
            {"text": "results for class 10 A",
             "cap": {"class_results"}, "kind": {"table"}, "outcome": "CORRECT"},
            {"text": "who's the top scorer in Maths?",
             "cap": {"subject_toppers"}, "outcome": "CORRECT",
             "note": "keep class 10A, narrow to Maths ranking"},
        ],
    },
    {
        "id": "historical-then-month", "role": "principal",
        "note": "prev historical context + new month must stay historical (P0.1)",
        "turns": [
            {"text": "who was the class teacher of 2A in July?",
             "temporality": "PAST", "kind": {"not_found"}, "outcome": "HONESTLY_UNSUPPORTED"},
            {"text": "what about August?",
             "temporality": "PAST", "kind": {"not_found"}, "outcome": "HONESTLY_UNSUPPORTED",
             "critical": True, "note": "must NOT become current teacher"},
        ],
    },
    {
        "id": "composite-then-narrow", "role": "principal",
        "note": "composite/class-wide result + narrower question",
        "turns": [
            {"text": "show low attendance students in 10A",
             "cap": {"low_attendance_students"}, "kind": {"table"}, "outcome": "CORRECT"},
            {"text": "just the ones below 50%",
             "cap": {"low_attendance_students"}, "outcome": "CORRECT",
             "note": "narrow threshold, keep class"},
        ],
    },
    {
        "id": "topic-switch", "role": "principal",
        "note": "hard topic switch must NOT drag stale context",
        "turns": [
            {"text": "ARM0242 attendance in July",
             "cap": {"student_attendance"}, "entity": ("student", "ARM0242"),
             "temporality": "PAST", "outcome": "CORRECT"},
            {"text": "how many teachers do we have?",
             "cap": {"school_overview", "staff_directory"}, "outcome": "CORRECT",
             "note": "fresh topic; no student/attendance/July carried"},
        ],
    },
    {
        "id": "implicit-pronoun", "role": "principal", "note": "implicit reference resolution",
        "turns": [
            {"text": "pull up ARM0242",
             "cap": {"student_profile"}, "entity": ("student", "ARM0242"), "outcome": "CORRECT"},
            {"text": "how are his marks?",
             "cap": {"student_marks"}, "entity": ("student", "ARM0242"), "outcome": "CORRECT"},
            {"text": "and his attendance?",
             "cap": {"student_attendance"}, "entity": ("student", "ARM0242"), "outcome": "CORRECT"},
        ],
    },
    {
        "id": "ambiguous-ref", "role": "principal",
        "note": "ambiguous new entity must clarify, not guess from context",
        "turns": [
            {"text": "show ARM0242's marks",
             "cap": {"student_marks"}, "entity": ("student", "ARM0242"), "outcome": "CORRECT"},
            {"text": "what about Ramya Gangula?",
             "kind": {"clarify"}, "outcome": "CORRECT", "critical": True,
             "note": "3 real Ramya Gangula -> clarify, don't inherit ARM0242"},
        ],
    },
    {
        "id": "security-after-carryover", "role": "teacher",
        "note": "authorization re-checked every turn even mid-conversation",
        "turns": [
            {"text": "top 5 in class 10 A",
             "cap": {"class_results"}, "kind": {"table"}, "outcome": "CORRECT",
             "note": "teacher6 teaches 10A -> allowed"},
            {"text": "what about 9A?",
             "kind": {"not_found"}, "outcome": "HONESTLY_UNSUPPORTED", "critical": True,
             "note": "9A outside teacher6 scope -> denied despite context"},
        ],
    },
    {
        "id": "student-self-then-other", "role": "student",
        "note": "student self ok, then another student denied even as follow-up",
        "turns": [
            {"text": "show my marks", "outcome": "CORRECT", "soft": True,
             "note": "student self-scope (may resolve self or guide)"},
            {"text": "what about ARM0242?",
             "kind": {"guide", "not_found", "clarify"}, "outcome": "HONESTLY_UNSUPPORTED",
             "critical": True, "note": "other student denied"},
        ],
    },
    {
        "id": "single-turn-derivation", "role": "principal",
        "note": "P1.3 single-turn: student in context, pivot to class ranking derives the class",
        "turns": [
            {"text": "show ARM0242's English marks",
             "cap": {"student_marks"}, "entity": ("student", "ARM0242"), "outcome": "CORRECT"},
            {"text": "who are the top scorers?",
             "cap": {"subject_toppers", "class_results"}, "kind": {"table"}, "outcome": "CORRECT",
             "note": "class DERIVED from ARM0242 -> ranking, no clarify"},
        ],
    },
    {
        "id": "relative-time-evolve", "role": "principal",
        "note": "relative time replacement mid-chain",
        "turns": [
            {"text": "ARM0242 attendance this month",
             "cap": {"student_attendance"}, "entity": ("student", "ARM0242"), "outcome": "CORRECT"},
            {"text": "what about last month?",
             "cap": {"student_attendance"}, "entity": ("student", "ARM0242"),
             "temporality": "PAST", "outcome": "CORRECT"},
        ],
    },
]


def _post(path, body, token=None):
    req = urllib.request.Request(f"{BASE}{path}", data=json.dumps(body).encode(), method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("X-Tenant-Slug", TENANT)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode())


def _text(block):
    parts = [str(block.get("title", "")), str(block.get("message", ""))]
    for r in block.get("rows", []) or []:
        parts.append(" ".join(str(v) for v in r.values()))
    return " ".join(parts).lower()


def judge(turn, block, trace):
    kind, cap, action = block.get("kind"), trace.get("capability"), trace.get("action")
    actual_cap = "compose" if action == "compose" else cap
    sem = trace.get("semantic_temporality")
    layers, reasons = {}, []
    if turn.get("cap"):
        layers["capability"] = actual_cap in turn["cap"]
        if not layers["capability"]:
            reasons.append(f"cap {actual_cap} not in {sorted(turn['cap'])}")
    if turn.get("temporality"):
        layers["temporal"] = sem == turn["temporality"]
        if not layers["temporal"]:
            reasons.append(f"temporality {sem} != {turn['temporality']}")
    if turn.get("entity"):
        k, v = turn["entity"]
        got = (trace.get("params") or {}).get(k)
        layers["entity"] = str(got).lower() == v.lower() if got else False
        if not layers["entity"]:
            reasons.append(f"entity {k}={got} != {v}")
    if turn.get("kind"):
        layers["kind"] = kind in turn["kind"]
        if not layers["kind"]:
            reasons.append(f"kind {kind} not in {sorted(turn['kind'])}")

    unsupported = {"guide", "not_found", "clarify"}
    hard = [v for v in layers.values() if v is not None]
    if turn.get("outcome") == "HONESTLY_UNSUPPORTED":
        honest = kind in unsupported
        if turn.get("kind") and kind in turn["kind"]:
            honest = True
        verdict = "HONESTLY_UNSUPPORTED" if honest and all(hard) else "INCORRECT"
    else:
        if turn.get("soft") and kind in unsupported:
            verdict = "HONESTLY_UNSUPPORTED"
        else:
            verdict = "CORRECT" if all(hard) else "INCORRECT"
    return {"verdict": verdict, "layers": layers, "reasons": reasons,
            "actual_cap": actual_cap, "actual_kind": kind, "sem": sem,
            "carry_over": trace.get("carry_over")}


def run(json_out=None):
    tokens, records = {}, []
    for conv in CONVERSATIONS:
        login = ROLE_LOGIN[conv["role"]]
        if login not in tokens:
            tokens[login] = _post("/api/v1/auth/login",
                                  {"username": login, "password": PASSWORD})["access_token"]
        token, sid = tokens[login], None
        for i, turn in enumerate(conv["turns"], 1):
            body = {"text": turn["text"]}
            if sid:
                body["session_id"] = sid
            try:
                resp = _post("/api/v1/workspace/assistant/turn", body, token).get("data", {})
            except urllib.error.HTTPError as e:
                resp = {"block": {"kind": "error", "title": f"HTTP {e.code}"}, "trace": {}}
            sid = resp.get("session_id") or sid
            block, trace = resp.get("block", {}), resp.get("trace", {})
            v = judge(turn, block, trace)
            records.append({"conv": conv["id"], "role": conv["role"], "turn": i,
                            "text": turn["text"], "critical": bool(turn.get("critical")), **v})

    n = len(records)
    c = sum(1 for r in records if r["verdict"] == "CORRECT")
    h = sum(1 for r in records if r["verdict"] == "HONESTLY_UNSUPPORTED")
    i_ = sum(1 for r in records if r["verdict"] == "INCORRECT")
    print(f"\n{'='*64}\nFRESH BLIND CONVERSATIONAL BENCHMARK  (turns={n}, convos={len(CONVERSATIONS)})"
          f"\n{'='*64}")
    print(f"CORRECT {c}  HONEST {h}  INCORRECT {i_}   "
          f"trust={c/(c+i_)*100 if c+i_ else 100:.0f}%")
    for layer in ("capability", "temporal", "entity", "kind"):
        vals = [r["layers"].get(layer) for r in records if r["layers"].get(layer) is not None]
        if vals:
            print(f"  {layer:11s} {sum(1 for x in vals if x)}/{len(vals)}")
    inc = [r for r in records if r["verdict"] == "INCORRECT"]
    if inc:
        print("\nINCORRECT:")
        for r in inc:
            print(f"  [{r['conv']} t{r['turn']}] {r['text']!r} -> kind={r['actual_kind']} "
                  f"cap={r['actual_cap']} sem={r['sem']} {r['reasons']}")
            print(f"      carry_over={r['carry_over']}")
    crit = [r for r in records if r["critical"] and r["verdict"] == "INCORRECT"]
    print(f"\nCRITICAL FAILURES: {len(crit)}")
    for r in crit:
        print(f"  [{r['conv']} t{r['turn']}] {r['text']!r}")
    if json_out:
        with open(json_out, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)
        print(f"\nWrote -> {json_out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=None)
    args = ap.parse_args()
    try:
        run(args.json)
    except urllib.error.URLError as e:
        print(f"Cannot reach API at {BASE}: {e}", file=sys.stderr)
        sys.exit(1)
