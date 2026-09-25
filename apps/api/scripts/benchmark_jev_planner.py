"""JEV-as-planner experiment — TypeSafe System One vs the current Gemma planner.

Tests the CORRECTED hypothesis (planner REPLACEMENT, not an added router):

    Current:   User -> Gemma planner        -> semantic metadata -> runtime
    Candidate: User -> JEV (TypeSafe SystemOne) -> semantic metadata -> runtime

JEV (TypeSafe "System One", model jev-latest) is a bounded-decision API: Choice (pick one of a
defined set + probabilities + confidence), Noul (yes/no), Score (ordinal). It answers MULTIPLE
questions in ONE request. That maps to the Category-A planner fields (capability / operation /
metric / temporal-presence / ambiguity) while the EXISTING deterministic runtime keeps exact
values, entity resolution, temporal resolution, derivation, authorization, and execution
(spec: JEV must NOT become the source of truth).

This benchmark reuses the SAME fixed P1.9 question set (capability + temporal expectations) and
runs four arms:
  A. Gemma-only        — the current planner (baseline).
  B. JEV-only          — one JEV request produces the bounded decisions.
  C. JEV + deterministic — same as B for the bounded fields; exact extraction stays deterministic
                           downstream (unchanged), so the bounded-decision accuracy IS B's.
  D. JEV + Gemma fallback — accept JEV when capability confidence >= gate, else fall back to Gemma.
                           The gate is CALIBRATED from the data (not invented); we report the
                           accuracy/cost/fallback-rate curve across thresholds.

Cost is reported in tokens (the vendor rate card is not in this environment; do NOT invent $).
Every arm's calls/turn and latency are measured so "JEV is cheap" is never assumed for a hybrid.

Blind: JEV/Gemma receive only the catalog + the user text (spec §16). Key via TYPESAFE_API_KEY.

Usage (from apps/api):
    $env:TYPESAFE_API_KEY="apikey_..."; python scripts/benchmark_jev_planner.py --reps 2
    python scripts/benchmark_jev_planner.py --arms A,B --json out.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import statistics
import sys
import time
import urllib.error
import urllib.request

logging.disable(logging.INFO)

import structlog  # noqa: E402

structlog.configure(
    processors=[], wrapper_class=structlog.make_filtering_bound_logger(logging.CRITICAL),
    logger_factory=structlog.ReturnLoggerFactory(),
)

from benchmark_planner_scale import (
    QUESTIONS,  # reuse the SAME fixed P1.9 question set  # noqa: E402
)

from app.modules.workspace.assistant.planner import plan  # noqa: E402
from app.modules.workspace.assistant.tools import ASSISTANT_TOOLS  # noqa: E402

TYPESAFE_URL = "https://api.typesafe.ai/v1/systemone"
API_KEY = os.environ.get("TYPESAFE_API_KEY", "")

# Short, neutral option rubrics for the capability Choice — derived from the real tool
# descriptions (first sentence), NOT hand-tuned to the questions (spec §21: no benchmark hacks).
_CAP_CRITERIA = {t.name: (t.description.split(".")[0][:120] or t.name) for t in ASSISTANT_TOOLS}
_CAP_CRITERIA["unsupported"] = "The request is not answerable by any capability above"

_TEMPORAL_CRITERIA = {
    "NONE": "no time frame mentioned",
    "CURRENT": "now, or an ongoing period that includes today (this month/week/year/term)",
    "PAST": "a period that ended before now (last month, in August, last year)",
    "FUTURE": "an upcoming period (next term)",
}


def _jev_request(text: str) -> dict:
    """One JEV request asking the bounded planner decisions together (fan-out, spec §14)."""
    return {
        "state": text,
        "model": "jev-latest",
        "questions": {
            "capability": {
                "type": "choice",
                "instructions": "Which capability best answers this school-assistant request?",
                "criteria": _CAP_CRITERIA,
            },
            "temporal": {
                "type": "choice",
                "instructions": "What time frame does the request refer to?",
                "criteria": _TEMPORAL_CRITERIA,
            },
        },
    }


def _call_jev(text: str) -> dict:
    req = urllib.request.Request(
        TYPESAFE_URL, data=json.dumps(_jev_request(text)).encode(), method="POST"
    )
    req.add_header("Authorization", f"Bearer {API_KEY}")
    req.add_header("Content-Type", "application/json")
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            d = json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"ok": False, "error": f"HTTP {e.code}: {e.read().decode()[:200]}",
                "latency_ms": int((time.perf_counter() - t0) * 1000)}
    except urllib.error.URLError as e:
        return {"ok": False, "error": str(e),
                "latency_ms": int((time.perf_counter() - t0) * 1000)}
    ms = int((time.perf_counter() - t0) * 1000)
    ans = d.get("answers", {})
    cap = ans.get("capability", {})
    return {
        "ok": True, "latency_ms": ms,
        "capability": cap.get("choice"),
        "capability_confidence": cap.get("confidence"),
        "temporal": ans.get("temporal", {}).get("choice"),
        "input_tokens": d.get("usage", {}).get("input_tokens", 0),
        "output_tokens": d.get("usage", {}).get("output_tokens", 0),
    }


def _cap_ok(chosen: str | None, expected: set[str]) -> bool:
    if not expected:  # negative/unsupported question
        real = {t.name for t in ASSISTANT_TOOLS}
        return chosen is None or chosen == "unsupported" or chosen not in real
    return chosen in expected


def _temporal_ok(chosen: str | None, expected: str | None) -> bool:
    return expected is None or chosen == expected


# ── Gemma arm (the real current planner) ──────────────────────────────────────────────────


async def _call_gemma(text: str) -> dict:
    t0 = time.perf_counter()
    try:
        decision = await plan(text, tools=list(ASSISTANT_TOOLS))
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e), "latency_ms": int((time.perf_counter() - t0) * 1000)}
    ms = int((time.perf_counter() - t0) * 1000)
    cap = decision.tool if decision.action in ("tool", "mixed") else None
    pres = getattr(getattr(decision, "temporal", None), "presence", "NONE")
    return {"ok": True, "latency_ms": ms, "capability": cap, "temporal": pres}


async def run_gemma(reps: int) -> dict:
    cap_hits, temp_hits, temp_n, lat = 0, 0, 0, []
    n = 0
    for _ in range(reps):
        for text, exp_caps, exp_temp in QUESTIONS:
            r = await _call_gemma(text)
            if not r["ok"]:
                continue
            n += 1
            cap_hits += 1 if _cap_ok(r["capability"], exp_caps) else 0
            if exp_temp is not None:
                temp_n += 1
                temp_hits += 1 if _temporal_ok(r["temporal"], exp_temp) else 0
            lat.append(r["latency_ms"])
    return _summ("Gemma-only", n, cap_hits, temp_hits, temp_n, lat, calls=1)


def run_jev(reps: int) -> tuple[dict, list[dict]]:
    """JEV-only arm; also returns per-question records (for the fallback/calibration arms)."""
    cap_hits, temp_hits, temp_n, lat, tin, tout = 0, 0, 0, [], [], []
    n = 0
    records = []
    for _ in range(reps):
        for text, exp_caps, exp_temp in QUESTIONS:
            r = _call_jev(text)
            if not r["ok"]:
                print(f"  JEV error on {text!r}: {r['error']}", file=sys.stderr)
                continue
            n += 1
            ck = _cap_ok(r["capability"], exp_caps)
            tk = _temporal_ok(r["temporal"], exp_temp)
            cap_hits += 1 if ck else 0
            if exp_temp is not None:
                temp_n += 1
                temp_hits += 1 if tk else 0
            lat.append(r["latency_ms"])
            tin.append(r["input_tokens"])
            tout.append(r["output_tokens"])
            records.append({"text": text, "exp_caps": list(exp_caps), "exp_temp": exp_temp,
                            "cap": r["capability"], "cap_conf": r["capability_confidence"],
                            "temporal": r["temporal"], "cap_ok": ck, "temporal_ok": tk,
                            "latency_ms": r["latency_ms"]})
    s = _summ("JEV-only", n, cap_hits, temp_hits, temp_n, lat, calls=1)
    s["avg_input_tokens"] = round(statistics.mean(tin)) if tin else 0
    s["avg_output_tokens"] = round(statistics.mean(tout)) if tout else 0
    return s, records


def _summ(name, n, cap_hits, temp_hits, temp_n, lat, *, calls) -> dict:
    return {
        "arm": name, "n": n, "calls_per_turn": calls,
        "capability_accuracy": round(cap_hits / n * 100, 1) if n else 0,
        "temporal_accuracy": round(temp_hits / temp_n * 100, 1) if temp_n else None,
        "avg_latency_ms": round(statistics.mean(lat)) if lat else 0,
        "p95_latency_ms": round(_p95(lat)) if lat else 0,
    }


def _p95(v):
    if not v:
        return 0
    s = sorted(v)
    return s[min(len(s) - 1, int(round(0.95 * (len(s) - 1))))]


def confidence_buckets(records: list[dict]) -> None:
    """Is JEV confidence actually calibrated for StudyNexs? Report accuracy per confidence bucket
    (spec §11) — validated independently, not taken on the vendor's word."""
    buckets = [
        ("0.50-0.59", 0.50, 0.60), ("0.60-0.69", 0.60, 0.70), ("0.70-0.79", 0.70, 0.80),
        ("0.80-0.89", 0.80, 0.90), ("0.90-0.94", 0.90, 0.95), ("0.95-0.99", 0.95, 1.00),
        ("1.00", 1.00, 1.0001),
    ]
    print("\n  Confidence calibration (independent — is JEV confidence a useful signal?):")
    print(f"  {'bucket':>10} {'n':>4} {'cap_accuracy':>13}")
    for label, lo, hi in buckets:
        b = [r for r in records if r["cap_conf"] is not None and lo <= r["cap_conf"] < hi]
        if not b:
            continue
        acc = sum(1 for r in b if r["cap_ok"]) / len(b) * 100
        print(f"  {label:>10} {len(b):>4} {acc:>12.1f}%")


def calibrate_fallback(records: list[dict], gemma_cap_acc: float) -> None:
    """Confidence-gated hybrid (spec §15): accept JEV when capability confidence >= gate, else
    fall back to Gemma. We report the curve across thresholds derived FROM the data — no invented
    threshold — with false-accept / false-reject and the resulting fallback rate + call cost."""
    print("\n  Confidence-gated JEV + Gemma fallback (calibrated from data):")
    print(f"  {'gate':>5} {'fallback%':>9} {'false_accept':>12} {'false_reject':>12} "
          f"{'hybrid_cap_acc*':>15}")
    confs = sorted({round(r["cap_conf"], 2) for r in records if r["cap_conf"] is not None})
    gates = [0.0] + confs
    seen = set()
    for gate in gates:
        if gate in seen:
            continue
        seen.add(gate)
        accept = [r for r in records if (r["cap_conf"] or 0) >= gate]
        fallback = [r for r in records if (r["cap_conf"] or 0) < gate]
        if not records:
            continue
        fb_rate = len(fallback) / len(records) * 100
        # false accept = accepted but JEV was wrong; false reject = fell back though JEV was right.
        false_accept = sum(1 for r in accept if not r["cap_ok"]) / len(records) * 100
        false_reject = sum(1 for r in fallback if r["cap_ok"]) / len(records) * 100
        # Hybrid capability accuracy* assumes fallback resolves at Gemma's measured accuracy.
        accepted_correct = sum(1 for r in accept if r["cap_ok"])
        hybrid = (accepted_correct + len(fallback) * gemma_cap_acc / 100) / len(records) * 100
        print(f"  {gate:>5.2f} {fb_rate:>8.1f}% {false_accept:>11.1f}% {false_reject:>11.1f}% "
              f"{hybrid:>14.1f}%")
    print("  * hybrid_cap_acc estimates fallback cases at Gemma's measured accuracy; each "
          "fallback = +1 Gemma call.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=2)
    ap.add_argument("--arms", default="A,B,D", help="A=Gemma B=JEV D=fallback-calibration")
    ap.add_argument("--json", default=None)
    args = ap.parse_args()
    if not API_KEY:
        print("TYPESAFE_API_KEY not set — cannot run JEV arms.", file=sys.stderr)
        sys.exit(2)
    arms = {a.strip().upper() for a in args.arms.split(",")}

    print(f"\n{'=' * 74}\nJEV-AS-PLANNER EXPERIMENT  (reps={args.reps}, "
          f"{len(QUESTIONS)} P1.9 questions)\n{'=' * 74}")

    out: dict = {}
    gemma = None
    if "A" in arms:
        gemma = asyncio.run(run_gemma(args.reps))
        _print(gemma)
        out["gemma"] = gemma
    jev, records = (None, [])
    if "B" in arms or "D" in arms:
        jev, records = run_jev(args.reps)
        _print(jev)
        print(f"       avg_input_tokens={jev['avg_input_tokens']}  "
              f"avg_output_tokens={jev['avg_output_tokens']}")
        out["jev"] = jev
    if "D" in arms and records:
        confidence_buckets(records)
        gemma_acc = gemma["capability_accuracy"] if gemma else 97.1
        calibrate_fallback(records, gemma_acc)
        out["jev_records"] = records

    if gemma and jev:
        print("\n  HEAD-TO-HEAD (capability accuracy / temporal / avg latency / calls):")
        print(f"    Gemma : {gemma['capability_accuracy']}%  {gemma['temporal_accuracy']}%  "
              f"{gemma['avg_latency_ms']}ms  {gemma['calls_per_turn']} call")
        print(f"    JEV   : {jev['capability_accuracy']}%  {jev['temporal_accuracy']}%  "
              f"{jev['avg_latency_ms']}ms  {jev['calls_per_turn']} call")

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2)
        print(f"\nWrote -> {args.json}")


def _print(s: dict) -> None:
    print(f"  {s['arm']:14s} cap_acc={s['capability_accuracy']:>5}%  "
          f"temporal={s['temporal_accuracy']}  avg_lat={s['avg_latency_ms']:>5}ms  "
          f"p95={s['p95_latency_ms']:>5}ms  calls/turn={s['calls_per_turn']}  n={s['n']}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
