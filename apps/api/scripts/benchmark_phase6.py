"""Phase 6 — blind real-school benchmark runner + multi-layer judge.

BLIND: the assistant receives only {text} + the authenticated role. No expected
capability/domain/entity is sent. Expectations live only in the evaluator and are
compared against the captured trace + block afterwards.

Usage (API must be running on :8000 against the reference tenant):
    python scripts/benchmark_phase6.py            # dev set
    python scripts/benchmark_phase6.py --holdout  # holdout set (run once, after fixes)
    python scripts/benchmark_phase6.py --json out.json

Verdicts per question: CORRECT / HONESTLY_UNSUPPORTED / INCORRECT.
Also records per-layer signals (capability/temporal/kind/authorization) and a
failure_category so failures can be clustered by architectural root cause.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request

from benchmark_phase6_questions import DEV_QUESTIONS, HOLDOUT_QUESTIONS

BASE = "http://127.0.0.1:8000"
TENANT = "reference"
PASSWORD = "Demo@1234"
ROLE_LOGIN = {
    "principal": "principal",
    "super_admin": "principal",
    "teacher": "teacher6",
    "class_incharge": "teacher1",
    "parent": "parent_demo",
    "student": "student_demo",
}


def _post(path: str, body: dict, token: str | None = None) -> dict:
    req = urllib.request.Request(f"{BASE}{path}", data=json.dumps(body).encode(), method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("X-Tenant-Slug", TENANT)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode())


def _login(username: str) -> str:
    return _post("/api/v1/auth/login", {"username": username, "password": PASSWORD})["access_token"]


def _answer_text(block: dict) -> str:
    """Flatten a block into a searchable text blob for substring assertions."""
    parts = [str(block.get("title", "")), str(block.get("message", "")),
             str(block.get("subtitle", ""))]
    for r in block.get("rows", []) or []:
        parts.append(" ".join(str(v) for v in r.values()))
    for m in block.get("metrics", []) or []:
        parts.append(f"{m.get('label')} {m.get('value')}")
    for o in block.get("options", []) or []:
        parts.append(str(o.get("label", "")))
    data = block.get("data")
    if isinstance(data, dict):
        parts.append(_answer_text(data))
    return " ".join(parts)


def _domain(qid: str) -> str:
    prefix = qid.split("-")[0].lstrip("h").lstrip("-") or qid.split("-")[0]
    key = qid.replace("h-", "").split("-")[0]
    return {
        "stu": "Students", "att": "Attendance", "fee": "Fees", "tch": "Teachers",
        "stf": "Staff", "exm": "Exams/Marks", "his": "Temporal/History", "amb": "Ambiguity",
        "neg": "Negative", "sec": "Security", "cmp": "Composition",
        "cv1": "Follow-up", "cv2": "Follow-up", "cv3": "Follow-up", "hcv1": "Follow-up",
    }.get(key, "Other")


def judge(q: dict, block: dict, trace: dict) -> dict:
    """Multi-layer scoring -> verdict + failure_category + per-layer signals."""
    kind = block.get("kind")
    cap = trace.get("capability")
    action = trace.get("action")
    route = trace.get("route")
    sem = trace.get("semantic_temporality")
    text = _answer_text(block).lower()

    layers: dict[str, bool | None] = {
        "capability": None, "temporal": None, "kind": None, "authorization": None,
        "answer": None,
    }
    reasons: list[str] = []

    # Capability layer (compose reported via action, not capability).
    exp_cap = q.get("expect_capability")
    actual_cap = "compose" if action == "compose" else cap
    if exp_cap:
        layers["capability"] = actual_cap in exp_cap
        if not layers["capability"]:
            reasons.append(f"capability {actual_cap} not in {sorted(exp_cap)}")

    # Route layer.
    if q.get("expect_route"):
        if route != q["expect_route"]:
            reasons.append(f"route {route} != {q['expect_route']}")

    # Temporal layer (P0.1): semantic temporality must match when specified.
    if q.get("expect_temporality"):
        layers["temporal"] = sem == q["expect_temporality"]
        if not layers["temporal"]:
            reasons.append(f"temporality {sem} != {q['expect_temporality']}")

    # Kind layer.
    if q.get("expect_kind"):
        layers["kind"] = kind in q["expect_kind"]
        if not layers["kind"]:
            reasons.append(f"kind {kind} not in {sorted(q['expect_kind'])}")

    # Substring assertions.
    forbid_hit = [s for s in q.get("forbid_substrings", []) if s.lower() in text]
    if forbid_hit:
        reasons.append(f"forbidden substring present: {forbid_hit}")
    req = q.get("require_substrings")
    require_ok = True
    if req:
        require_ok = any(s.lower() in text for s in req)
        if not require_ok:
            reasons.append(f"missing required substring (one of {req})")

    # Authorization signal: for restricted roles the good outcome is a non-data block.
    unsupported_kinds = {"guide", "not_found", "clarify"}
    if q["role"] in ("student", "parent") and q.get("outcome") == "HONESTLY_UNSUPPORTED":
        layers["authorization"] = kind in unsupported_kinds and not forbid_hit
        if not layers["authorization"]:
            reasons.append("restricted role received data-like block")

    # Verdict.
    expected_outcome = q.get("outcome", "CORRECT")
    hard_layers = [v for k, v in layers.items() if v is not None]
    layers_ok = all(hard_layers) and not forbid_hit and require_ok

    if expected_outcome == "HONESTLY_UNSUPPORTED":
        # Good = honestly declined (unsupported kind) OR the expected honest not_found.
        honest = kind in unsupported_kinds and not forbid_hit
        # temporal-history 'not_found' with the honest message is the correct honest outcome.
        if q.get("expect_kind") and kind in q["expect_kind"] and not forbid_hit and require_ok:
            honest = True
        verdict = "HONESTLY_UNSUPPORTED" if honest else "INCORRECT"
        if verdict == "INCORRECT" and not reasons:
            reasons.append("expected honest refusal, got a data answer")
    else:  # expected CORRECT
        if q.get("soft") and kind in unsupported_kinds:
            verdict = "HONESTLY_UNSUPPORTED"  # acceptable safe fallback
        elif layers_ok:
            verdict = "CORRECT"
        else:
            verdict = "INCORRECT"

    # Failure category (root-cause bucket).
    category = None
    if verdict == "INCORRECT":
        if layers.get("authorization") is False:
            category = "AUTHORIZATION"
        elif layers.get("temporal") is False:
            category = "TEMPORAL"
        elif layers.get("capability") is False and q.get("expect_capability"):
            category = "PLANNING" if actual_cap else "CLASSIFICATION"
        elif forbid_hit:
            category = "RESULT_VALIDATION"
        elif layers.get("kind") is False:
            category = "PLANNING"
        elif not require_ok:
            category = "RESULT_VALIDATION"
        else:
            category = "ANSWER_GENERATION"

    return {
        "verdict": verdict,
        "failure_category": category,
        "layers": layers,
        "reasons": reasons,
        "actual_capability": actual_cap,
        "actual_kind": kind,
        "actual_route": route,
        "actual_temporality": sem,
    }


def run(questions: list[dict], label: str, json_out: str | None) -> None:
    # Group into conversations (shared session) vs singletons.
    tokens: dict[str, str] = {}
    sessions: dict[str, str | None] = {}
    records: list[dict] = []

    # Preserve author order; conversations already ordered by 'turn'.
    ordered = sorted(questions, key=lambda q: (q.get("conversation_id") or q["id"], q.get("turn", 0)))

    for q in ordered:
        role = q["role"]
        login = ROLE_LOGIN.get(role)
        if login not in tokens:
            tokens[login] = _login(login)
        token = tokens[login]
        conv = q.get("conversation_id")
        sid = sessions.get(conv) if conv else None

        body = {"text": q["message"]}
        if sid:
            body["session_id"] = sid
        t0 = time.time()
        try:
            resp = _post("/api/v1/workspace/assistant/turn", body, token).get("data", {})
        except urllib.error.HTTPError as e:
            resp = {"block": {"kind": "error", "title": f"HTTP {e.code}"}, "trace": {}}
        latency_ms = round((time.time() - t0) * 1000)
        block = resp.get("block", {}) or {}
        trace = resp.get("trace", {}) or {}
        if conv:
            sessions[conv] = resp.get("session_id") or sid

        verdict = judge(q, block, trace)
        records.append({
            "id": q["id"], "role": role, "domain": _domain(q["id"]),
            "conversation_id": conv, "message": q["message"],
            "expected_outcome": q.get("outcome", "CORRECT"),
            "critical": bool(q.get("critical")),
            "latency_ms": latency_ms,
            **verdict,
            "trace": {k: trace.get(k) for k in (
                "route", "action", "capability", "semantic_temporality",
                "plan_temporality", "temporal_integrity", "temporal_guard_decision",
            )},
            "block_title": block.get("title"),
        })

    _report(records, label)
    if json_out:
        with open(json_out, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)
        print(f"\nWrote {len(records)} records -> {json_out}")


def _report(records: list[dict], label: str) -> None:
    n = len(records)
    correct = sum(1 for r in records if r["verdict"] == "CORRECT")
    honest = sum(1 for r in records if r["verdict"] == "HONESTLY_UNSUPPORTED")
    incorrect = sum(1 for r in records if r["verdict"] == "INCORRECT")
    print(f"\n{'='*66}\nPHASE 6 BENCHMARK — {label}  (n={n})\n{'='*66}")
    print(f"CORRECT              {correct:3d}  ({correct/n*100:.1f}%)")
    print(f"HONESTLY_UNSUPPORTED {honest:3d}  ({honest/n*100:.1f}%)")
    print(f"INCORRECT            {incorrect:3d}  ({incorrect/n*100:.1f}%)")
    denom = correct + incorrect
    print(f"\nTrust ratio  Correct/(Correct+Incorrect) = "
          f"{(correct/denom*100 if denom else 100):.1f}%")
    print(f"Support ratio (Correct+Honest)/Total       = {(correct+honest)/n*100:.1f}%")

    # Per-domain.
    print("\nPer-domain (CORRECT / HONEST / INCORRECT):")
    domains: dict[str, list[int]] = {}
    for r in records:
        d = domains.setdefault(r["domain"], [0, 0, 0])
        idx = {"CORRECT": 0, "HONESTLY_UNSUPPORTED": 1, "INCORRECT": 2}[r["verdict"]]
        d[idx] += 1
    for dom in sorted(domains):
        c, h, i = domains[dom]
        print(f"  {dom:18s} {c:2d} / {h:2d} / {i:2d}")

    # Per-layer accuracy (only where a layer was checked).
    print("\nPer-layer accuracy (checked cases only):")
    for layer in ("capability", "temporal", "kind", "authorization"):
        vals = [r["layers"].get(layer) for r in records if r["layers"].get(layer) is not None]
        if vals:
            ok = sum(1 for v in vals if v)
            print(f"  {layer:14s} {ok}/{len(vals)}  ({ok/len(vals)*100:.0f}%)")

    # Failure clusters.
    clusters: dict[str, int] = {}
    for r in records:
        if r["failure_category"]:
            clusters[r["failure_category"]] = clusters.get(r["failure_category"], 0) + 1
    if clusters:
        print("\nFailure clusters:")
        for cat, c in sorted(clusters.items(), key=lambda x: -x[1]):
            print(f"  {cat:18s} {c}")

    # Critical failures listed individually.
    crit = [r for r in records if r["critical"] and r["verdict"] == "INCORRECT"]
    print(f"\nCRITICAL FAILURES: {len(crit)}")
    for r in crit:
        print(f"  [{r['id']}] ({r['role']}) {r['message']!r}")
        print(f"      -> {r['actual_kind']} / cap={r['actual_capability']} / {r['reasons']}")

    # All incorrect (for dev inspection).
    inc = [r for r in records if r["verdict"] == "INCORRECT"]
    if inc:
        print(f"\nAll INCORRECT ({len(inc)}):")
        for r in inc:
            print(f"  [{r['id']}] {r['message']!r} -> {r['actual_kind']} "
                  f"cap={r['actual_capability']} cat={r['failure_category']} {r['reasons']}")

    # Latency snapshot.
    lat = sorted(r["latency_ms"] for r in records)
    if lat:
        p50 = lat[len(lat) // 2]
        p95 = lat[min(len(lat) - 1, int(len(lat) * 0.95))]
        print(f"\nLatency ms: p50={p50} p95={p95} max={lat[-1]}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--holdout", action="store_true")
    ap.add_argument("--json", default=None)
    args = ap.parse_args()
    if args.holdout:
        run(HOLDOUT_QUESTIONS, "HOLDOUT", args.json)
    else:
        run(DEV_QUESTIONS, "DEVELOPMENT", args.json)


if __name__ == "__main__":
    try:
        main()
    except urllib.error.URLError as e:
        print(f"Cannot reach the API at {BASE}: {e}. Start it first.", file=sys.stderr)
        sys.exit(1)
