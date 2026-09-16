"""Phase P1.2 — follow-up (conversational carry-over) benchmark.

A SEPARATE blind suite (does not touch the Phase 6 dev/holdout sets). Each scenario is a
multi-turn conversation run on ONE session; only the final turn is judged, on the semantic
dimensions that must carry over. Sends only {text}+role; expectations are private to the
evaluator and checked against the captured trace.

Usage (API on :8000, reference tenant):
    python scripts/benchmark_followup.py [--json out.json]

Measures: temporal inheritance, entity inheritance, relationship (historical) preservation,
authorization, and final-answer class (CORRECT / HONESTLY_UNSUPPORTED / INCORRECT).
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

# Each scenario: turns [(text)], role, and expectations on the FINAL turn.
SCENARIOS = [
    {
        "id": "fu-fee-period", "role": "principal",
        "turns": ["how much did we collect in July?", "what about August?"],
        "expect_capability": {"fee_collection_period"}, "expect_temporality": "PAST",
        "expect_kind": {"metrics"}, "outcome": "CORRECT",
        "note": "fee period replacement, same domain (both past months)",
    },
    {
        "id": "fu-att-period", "role": "principal",
        "turns": ["show ARM0003 attendance in July", "what about August?"],
        "expect_capability": {"student_attendance"}, "expect_temporality": "PAST",
        "expect_entity": ("student", "ARM0003"), "outcome": "CORRECT",
        "note": "student + attendance kept, time swapped (past months)",
    },
    {
        "id": "fu-hist-teacher", "role": "principal",
        "turns": ["who was the class teacher of 2A in August?", "what about September?"],
        "expect_temporality": "PAST", "expect_kind": {"not_found"},
        "outcome": "HONESTLY_UNSUPPORTED", "critical": True,
        "note": "historical stays historical (P0.1 regression guard)",
    },
    {
        "id": "fu-current-class", "role": "principal",
        "turns": ["who is the class teacher of 2A?", "what about 10A?"],
        "expect_capability": {"teachers_for_class"}, "expect_temporality": "CURRENT",
        "expect_kind": {"table"}, "outcome": "CORRECT",
        "note": "current preserved, class replaced (both classes exist)",
    },
    {
        "id": "fu-domain-switch", "role": "principal",
        "turns": ["what is ARM0003's attendance?", "what about his fees?"],
        "expect_capability": {"student_fees", "student_profile"},
        "expect_entity": ("student", "ARM0003"), "outcome": "CORRECT",
        "note": "entity kept, domain switched to fees",
    },
    {
        "id": "fu-metric-change", "role": "principal",
        "turns": ["how much fee was collected in August?", "how many receipts were there?"],
        "expect_capability": {"fee_collection_period"}, "expect_temporality": "PAST",
        "outcome": "CORRECT", "note": "time inherited when metric changes",
    },
    {
        "id": "fu-subject-change", "role": "principal",
        "turns": ["show ARM0242's Mathematics marks", "what about English?"],
        "expect_capability": {"student_marks"}, "expect_entity": ("student", "ARM0242"),
        "outcome": "CORRECT", "note": "student kept, subject swapped",
    },
    {
        "id": "fu-class-swap", "role": "principal",
        "turns": ["show students in 10A below 80% attendance", "what about 9A?"],
        "expect_capability": {"low_attendance_students"}, "outcome": "CORRECT",
        "note": "class replaced, threshold kept (no over-inheritance)",
    },
    # Adversarial (§23)
    {
        "id": "fu-both-change", "role": "principal",
        "turns": ["attendance of ARM0003 in July", "August fees"],
        "expect_capability": {"fee_collection_period", "students_fee_pending_over"},
        "expect_temporality": "PAST", "outcome": "CORRECT",
        "note": "domain + time both change (past months)",
    },
    {
        "id": "fu-entity-domain", "role": "principal",
        "turns": ["ARM0003 attendance", "ARM0004 fees"],
        "expect_entity": ("student", "ARM0004"), "outcome": "CORRECT",
        "note": "entity + domain both change",
    },
    {
        "id": "fu-relative-time", "role": "principal",
        "turns": ["ARM0003 attendance this month", "last month"],
        "expect_capability": {"student_attendance"}, "expect_entity": ("student", "ARM0003"),
        "expect_temporality": "PAST", "outcome": "CORRECT",
        "note": "same student, time replaced to last month",
    },
    # Security: follow-up must re-check authorization every turn (§18)
    {
        "id": "fu-sec-scope", "role": "teacher",
        "turns": ["top 5 in class 10 A", "what about 9A?"],
        "outcome": "HONESTLY_UNSUPPORTED", "critical": True,
        "expect_kind": {"not_found"},
        "note": "teacher6 teaches 10A not 9A -> follow-up to 9A denied",
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


def _answer_text(block):
    parts = [str(block.get("title", "")), str(block.get("message", ""))]
    for r in block.get("rows", []) or []:
        parts.append(" ".join(str(v) for v in r.values()))
    for m in block.get("metrics", []) or []:
        parts.append(f"{m.get('label')} {m.get('value')}")
    return " ".join(parts).lower()


def judge(sc, block, trace):
    kind, cap, action = block.get("kind"), trace.get("capability"), trace.get("action")
    actual_cap = "compose" if action == "compose" else cap
    sem = trace.get("semantic_temporality")
    reasons = []
    layers = {"temporal": None, "entity": None, "capability": None, "kind": None}

    if sc.get("expect_capability"):
        layers["capability"] = actual_cap in sc["expect_capability"]
        if not layers["capability"]:
            reasons.append(f"capability {actual_cap} not in {sorted(sc['expect_capability'])}")
    if sc.get("expect_temporality"):
        layers["temporal"] = sem == sc["expect_temporality"]
        if not layers["temporal"]:
            reasons.append(f"temporality {sem} != {sc['expect_temporality']}")
    if sc.get("expect_entity"):
        k, v = sc["expect_entity"]
        got = (trace.get("params") or {}).get(k)
        layers["entity"] = str(got).lower() == v.lower() if got else False
        if not layers["entity"]:
            reasons.append(f"entity {k}={got} != {v}")
    if sc.get("expect_kind"):
        layers["kind"] = kind in sc["expect_kind"]
        if not layers["kind"]:
            reasons.append(f"kind {kind} not in {sorted(sc['expect_kind'])}")

    unsupported = {"guide", "not_found", "clarify"}
    hard = [v for v in layers.values() if v is not None]
    if sc.get("outcome") == "HONESTLY_UNSUPPORTED":
        honest = kind in unsupported
        if sc.get("expect_kind") and kind in sc["expect_kind"]:
            honest = True
        verdict = "HONESTLY_UNSUPPORTED" if honest and all(
            v for v in hard if v is not None
        ) else "INCORRECT"
    else:
        verdict = "CORRECT" if all(hard) else "INCORRECT"
    return {"verdict": verdict, "layers": layers, "reasons": reasons,
            "actual_capability": actual_cap, "actual_kind": kind, "semantic_temporality": sem,
            "carry_over": trace.get("carry_over")}


def run(json_out=None):
    tokens, records = {}, []
    for sc in SCENARIOS:
        login = ROLE_LOGIN[sc["role"]]
        if login not in tokens:
            tokens[login] = _post("/api/v1/auth/login",
                                  {"username": login, "password": PASSWORD})["access_token"]
        token, sid = tokens[login], None
        last = {}
        for text in sc["turns"]:
            body = {"text": text}
            if sid:
                body["session_id"] = sid
            try:
                resp = _post("/api/v1/workspace/assistant/turn", body, token).get("data", {})
            except urllib.error.HTTPError as e:
                resp = {"block": {"kind": "error", "title": f"HTTP {e.code}"}, "trace": {}}
            sid = resp.get("session_id") or sid
            last = resp
        block, trace = last.get("block", {}), last.get("trace", {})
        v = judge(sc, block, trace)
        records.append({"id": sc["id"], "role": sc["role"], "turns": sc["turns"],
                        "critical": bool(sc.get("critical")), **v})

    n = len(records)
    c = sum(1 for r in records if r["verdict"] == "CORRECT")
    h = sum(1 for r in records if r["verdict"] == "HONESTLY_UNSUPPORTED")
    i = sum(1 for r in records if r["verdict"] == "INCORRECT")
    print(f"\n{'='*60}\nFOLLOW-UP CARRY-OVER BENCHMARK  (n={n})\n{'='*60}")
    print(f"CORRECT {c}  HONEST {h}  INCORRECT {i}   trust={c/(c+i)*100 if c+i else 100:.0f}%")
    for layer in ("temporal", "entity", "capability", "kind"):
        vals = [r["layers"].get(layer) for r in records if r["layers"].get(layer) is not None]
        if vals:
            print(f"  {layer:11s} {sum(1 for x in vals if x)}/{len(vals)}")
    inc = [r for r in records if r["verdict"] == "INCORRECT"]
    if inc:
        print("\nINCORRECT:")
        for r in inc:
            print(f"  [{r['id']}] {r['turns']} -> kind={r['actual_kind']} "
                  f"cap={r['actual_capability']} sem={r['semantic_temporality']} {r['reasons']}")
            print(f"      carry_over={r['carry_over']}")
    crit = [r for r in records if r["critical"] and r["verdict"] == "INCORRECT"]
    print(f"\nCRITICAL FAILURES: {len(crit)}")
    for r in crit:
        print(f"  [{r['id']}] {r['turns']}")
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
