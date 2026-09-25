"""Planner scalability experiment — flat catalog vs hierarchical routing (audit Part 2).

Measures, EMPIRICALLY, whether the current single-planner architecture degrades as the
capability catalog grows (16 -> 150), BEFORE any orchestration layer (JEV/Strands/router) is
considered. No production code is changed and no new framework is added — this is measurement.

Method:
  - Synthetic catalogs are built from the REAL contract shape (varied entity/operation/params),
    NOT fake production tools (spec §8). Realistic distractors are included so routing is tested
    under genuine confusability (spec §10). The 16 real capabilities are always present as the
    "targets"; synthetic capabilities pad the catalog to 32/50/75/100/150.
  - The planner prompt is built with the REAL `_system_prompt(tools)` and answered by the REAL
    gateway (`generate_llm`, gemma4:cloud) — so token counts, latency, cost, and behavior match
    production. Blind: the model sees only the catalog + question (spec §16).
  - A fixed question set (spec §15, §9: same questions across all sizes) with a private expected
    capability + temporal presence. Each question is repeated (spec §19) to separate stable
    behavior from LLM nondeterminism; we report mean and range.
  - Two experiments: A = flat catalog at each size; B = a deterministic domain router that first
    picks a domain, then shows the planner ONLY that domain's (smaller) catalog (spec §11, §27).
    A cost comparison accounts for the extra router call (spec §20).
  - Optional (§22): a COMPACT structured catalog (entity/operation/params/scope/temporal) instead
    of prose, to see whether prompt size drops without hurting accuracy.

Usage (from apps/api, LLM reachable):
    python scripts/benchmark_planner_scale.py                 # full sweep, 3 reps
    python scripts/benchmark_planner_scale.py --sizes 16,32   # subset
    python scripts/benchmark_planner_scale.py --reps 2 --json out.json
    python scripts/benchmark_planner_scale.py --compact       # add the §22 compact-catalog run
    python scripts/benchmark_planner_scale.py --router        # add the hierarchical experiment
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import statistics
import sys
import time

logging.disable(logging.INFO)  # quiet stdlib logging

# The LLM gateway emits per-call telemetry via structlog, which bypasses logging.disable and
# floods stdout (hundreds of lines that bury the result table). Route structlog to a no-op so
# the benchmark output stays readable; metrics are still returned in-band from generate_llm.
import structlog  # noqa: E402

structlog.configure(
    processors=[], wrapper_class=structlog.make_filtering_bound_logger(logging.CRITICAL),
    logger_factory=structlog.ReturnLoggerFactory(),
)

from app.modules.ai.gateway.base import LLMMessage  # noqa: E402
from app.modules.ai.gateway.invoke import generate_llm  # noqa: E402
from app.modules.ai.gateway.pricing import estimate_cost_usd  # noqa: E402
from app.modules.workspace.assistant.planner import (  # noqa: E402
    _catalog_text,
    _parse_decision,
    _system_prompt,
)
from app.modules.workspace.assistant.tools import ASSISTANT_TOOLS, AssistantTool  # noqa: E402

_STAFF = frozenset({"admin", "super_admin", "class_incharge", "teacher", "operations"})


# ── Synthetic catalog generation (from the real contract shape; realistic distractors) ────

# Semantic building blocks mirror the real entity/operation vocabulary so synthetic tools are
# realistically confusable (§8, §10) rather than obviously unrelated.
_SYNTH_ENTITIES = [
    ("library", ["book", "member", "loan"], ["book_title", "member", "isbn"]),
    ("transport", ["route", "stop", "vehicle"], ["route_name", "student", "vehicle_no"]),
    ("hostel", ["room", "resident", "block"], ["room_no", "student", "block_name"]),
    ("payroll", ["salary", "payslip", "deduction"], ["staff", "month", "component"]),
    ("inventory", ["item", "stock", "supplier"], ["item_name", "category", "supplier"]),
    ("event", ["event", "participant", "venue"], ["event_name", "date", "venue"]),
    ("notice", ["notice", "circular", "audience"], ["notice_id", "audience", "date"]),
    ("admission", ["applicant", "seat", "interview"], ["applicant", "class_label", "status"]),
    ("health", ["record", "checkup", "immunization"], ["student", "date", "type"]),
    ("discipline", ["incident", "sanction", "merit"], ["student", "date", "category"]),
    ("cocurricular", ["activity", "club", "achievement"], ["student", "activity", "level"]),
    ("timetable", ["period", "slot", "substitution"], ["class_label", "day", "teacher"]),
]
_SYNTH_OPS = ["lookup", "list", "aggregate", "filter", "rank"]


def _synthetic_tools(n_extra: int) -> list[AssistantTool]:
    """Build n_extra realistic-but-non-production capabilities from the contract vocabulary.

    Names are unique (domain x noun x op enumerated; a numeric suffix guards the tail) so a
    large catalog has genuine semantic diversity, not duplicated identical tools (§8).
    """
    out: list[AssistantTool] = []
    seen: set[str] = set()
    i = 0
    while len(out) < n_extra:
        domain, nouns, params = _SYNTH_ENTITIES[i % len(_SYNTH_ENTITIES)]
        noun = nouns[(i // len(_SYNTH_ENTITIES)) % len(nouns)]
        op = _SYNTH_OPS[(i // (len(_SYNTH_ENTITIES) * 3)) % len(_SYNTH_OPS)]
        name = f"{domain}_{noun}_{op}"
        if name in seen:
            name = f"{name}_{i}"
        seen.add(name)
        pkey = params[i % len(params)]
        desc = (
            f"{op.title()} {domain} {noun}s. Use for questions about {domain} {noun}s "
            f"(e.g. '{op} {noun} for ...'). Returns a table or metrics."
        )
        out.append(AssistantTool(name=name, description=desc,
                                 params={pkey: f"string — the {pkey}"},
                                 roles=_STAFF, handler=ASSISTANT_TOOLS[0].handler))
        i += 1
    return out


# Explicit close distractors for the attendance domain (§10): plausible, near-synonym tools
# the planner must NOT pick when the user asks for one student's attendance.
_ATTENDANCE_DISTRACTORS = [
    ("class_attendance", "aggregate class attendance for a day"),
    ("teacher_attendance", "staff attendance records"),
    ("attendance_summary", "school-wide attendance summary metrics"),
    ("attendance_history", "historical attendance trend for a class"),
    ("attendance_report", "printable attendance report export"),
]


def _distractor_tools() -> list[AssistantTool]:
    out = []
    for name, desc in _ATTENDANCE_DISTRACTORS:
        out.append(AssistantTool(
            name=name, description=f"{desc}.", params={"class_label": "string — a class"},
            roles=_STAFF, handler=ASSISTANT_TOOLS[0].handler))
    return out


def build_catalog(size: int) -> list[AssistantTool]:
    """A catalog of `size` capabilities: the 16 real targets + distractors + synthetic pad."""
    real = list(ASSISTANT_TOOLS)  # 16 real (the answerable targets)
    distractors = _distractor_tools()  # 5 close distractors
    base = real + distractors
    if size <= len(base):
        return base[:size] if size >= len(real) else real[:size]
    return base + _synthetic_tools(size - len(base))


# ── Fixed blind question set (same across all sizes; §15) ──────────────────────────────────
# Each: text, expected capability (any of a set), expected temporal presence (or None to skip).
QUESTIONS = [
    # simple lookups
    ("show ARM0242's profile", {"student_profile"}, None),
    ("what is ARM0242's fee balance?", {"student_fees"}, None),
    ("list the students in Class 10 A", {"class_roster"}, None),
    ("give me the school overview", {"school_overview"}, None),
    ("list all staff", {"staff_directory"}, None),
    # closely-related / distractor-prone (attendance family, §10)
    ("what is ARM0242's attendance percentage?", {"student_attendance"}, None),
    ("how many students are absent today in Class 10 A?", {"class_attendance_today"}, None),
    ("which students have attendance below 75%?", {"low_attendance_students"}, None),
    # fees
    ("how much fee did we collect in August?", {"fee_collection_period"}, "PAST"),
    ("show overall fee collection status", {"fee_collection"}, None),
    ("which students have fees pending over 50%?", {"students_fee_pending_over"}, None),
    # exams
    ("show ARM0242's marks", {"student_marks"}, None),
    ("top 5 students in Class 10 A", {"class_results"}, None),
    ("who scored highest in Mathematics in Class 10 A?", {"subject_toppers"}, None),
    # teachers / relationships
    ("who is the class teacher of Class 10 A?", {"teachers_for_class"}, None),
    ("what does Kiran Naidu teach?", {"teacher_assignments"}, None),
    # derivation (indirect class via student)
    ("who teaches the class ARM0242 is in?", {"teachers_for_class"}, None),
    # temporal
    ("ARM0242 attendance this month", {"student_attendance"}, "CURRENT"),
    ("ARM0242 attendance last month", {"student_attendance"}, "PAST"),
    ("fee collected today", {"fee_collection_period"}, "CURRENT"),
    # multi-domain phrasing
    ("Class 10 A results and who teaches them", {"class_results", "teachers_for_class"}, None),
    # negatives / unsupported (should NOT match a target; honest clarify/other)
    ("what's the weather tomorrow?", set(), None),
    ("book a cab for the principal", set(), None),
    # security-sensitive (still a capability choice; authz is enforced elsewhere)
    ("show me every student's home address and phone", set(), None),
    # follow-up-style single turns
    ("how many receipts did we issue in August?", {"fee_collection_period"}, "PAST"),
    ("attendance for ARM0218", {"student_attendance"}, None),
    ("profile of ARM0218", {"student_profile"}, None),
    ("fee balance for ARM0218", {"student_fees"}, None),
    ("marks of ARM0218 in Science", {"student_marks"}, None),
    ("roster of Class 9 B", {"class_roster"}, None),
    ("lowest performers in Class 9 B", {"class_results"}, None),
    ("staff in the Science department", {"staff_directory"}, None),
    ("teachers and their classes", {"teachers_for_class"}, None),
    ("attendance below 60% in Class 10 A", {"low_attendance_students"}, None),
    ("fee collection this year", {"fee_collection_period"}, "CURRENT"),
]


def _compact_catalog_text(catalog: list[AssistantTool]) -> str:
    """A compact STRUCTURED catalog (entity/operation/params/scope/temporal) instead of prose
    descriptions (spec §22). Semantics are identical to the contract; only the representation is
    denser, to test whether prompt size drops without hurting tool-selection accuracy."""
    from app.modules.workspace.assistant.contracts import get_contract

    lines = []
    for t in catalog:
        c = get_contract(t.name)
        params = ",".join(t.params) or "-"
        if c is not None:
            derivable = ",".join(
                f"{p.name}<-{'/'.join(p.derive_from)}" for p in c.derivable_params()
            )
            meta = f"{c.entity}|{c.operation}|{c.scope}|{c.temporal_mode}|params:{params}"
            if derivable:
                meta += f"|derivable:{derivable}"
            lines.append(f"- {t.name}: {meta}")
        else:
            lines.append(f"- {t.name}: params:{params}")
    return "\n".join(lines)


def _compact_system_prompt(catalog: list[AssistantTool]) -> str:
    """The real system prompt with the prose catalog swapped for the compact structured one."""
    full = _system_prompt(catalog)
    prose = _catalog_text(catalog)
    return full.replace(prose, _compact_catalog_text(catalog))


async def _run_one(catalog: list[AssistantTool], text: str, *, compact: bool = False) -> dict:
    system = _compact_system_prompt(catalog) if compact else _system_prompt(catalog)
    messages = [LLMMessage(role="system", content=system),
                LLMMessage(role="user", content=text)]
    t0 = time.perf_counter()
    try:
        result = await generate_llm(
            messages, temperature=0.0, max_tokens=600, json_mode=True,
            feature="planner_scale_bench", caller="bench.planner_scale",
        )
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e), "latency_ms": int((time.perf_counter() - t0) * 1000)}
    decision = _parse_decision(result.text)
    return {
        "ok": True,
        "decision": decision,
        "malformed": decision is None,
        "tokens_in": result.tokens_in,
        "tokens_out": result.tokens_out,
        "latency_ms": result.latency_ms,
        "model": result.model,
    }


def _judge(decision, expected_caps: set[str], expected_temporal: str | None) -> dict:
    if decision is None:
        return {"cap_ok": False, "temporal_ok": expected_temporal is None, "chosen": None}
    chosen = decision.tool if decision.action in ("tool", "mixed") else f"[{decision.action}]"
    if not expected_caps:
        # A negative/unsupported question: correct = NOT choosing a real target tool.
        real_targets = {t.name for t in ASSISTANT_TOOLS}
        cap_ok = decision.action != "tool" or decision.tool not in real_targets
    else:
        cap_ok = decision.action in ("tool", "mixed") and decision.tool in expected_caps
    temporal_ok = True
    if expected_temporal is not None:
        pres = getattr(getattr(decision, "temporal", None), "presence", "NONE")
        temporal_ok = pres == expected_temporal
    return {"cap_ok": cap_ok, "temporal_ok": temporal_ok, "chosen": chosen}


async def run_flat(
    sizes: list[int], reps: int, json_out: str | None = None, *, compact: bool = False
) -> list[dict]:
    rows = []
    for size in sizes:
        catalog = build_catalog(size)
        actual_size = len(catalog)
        cap_scores, temp_scores, lat, tin, tout, malformed, errors = [], [], [], [], [], 0, 0
        cost = 0.0
        for _ in range(reps):
            for text, exp_caps, exp_temp in QUESTIONS:
                r = await _run_one(catalog, text, compact=compact)
                if not r["ok"]:
                    errors += 1
                    continue
                if r["malformed"]:
                    malformed += 1
                j = _judge(r["decision"], exp_caps, exp_temp)
                cap_scores.append(1 if j["cap_ok"] else 0)
                if exp_temp is not None:
                    temp_scores.append(1 if j["temporal_ok"] else 0)
                lat.append(r["latency_ms"])
                tin.append(r["tokens_in"])
                tout.append(r["tokens_out"])
                cost += float(estimate_cost_usd(r["model"], r["tokens_in"], r["tokens_out"]))
        n = len(cap_scores)
        rows.append({
            "size": size, "actual_size": actual_size, "n": n,
            "prompt_tokens": round(statistics.mean(tin)) if tin else 0,
            "output_tokens": round(statistics.mean(tout)) if tout else 0,
            "cap_accuracy": round(sum(cap_scores) / n * 100, 1) if n else 0,
            "temporal_accuracy": round(sum(temp_scores) / len(temp_scores) * 100, 1)
                if temp_scores else None,
            "avg_latency_ms": round(statistics.mean(lat)) if lat else 0,
            "p95_latency_ms": round(_p95(lat)) if lat else 0,
            "cost_per_turn_usd": round(cost / n, 6) if n else 0,
            "malformed_rate": round(malformed / (n + malformed) * 100, 1) if (n + malformed) else 0,
            "errors": errors,
        })
        _print_row(rows[-1])
        if json_out:  # write incrementally so an interruption never loses completed sizes
            import json
            with open(json_out, "w", encoding="utf-8") as f:
                json.dump({"flat": rows, "hierarchical": None}, f, indent=2)
    return rows


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    idx = min(len(s) - 1, int(round(0.95 * (len(s) - 1))))
    return s[idx]


def _print_row(r: dict) -> None:
    print(
        f"  size={r['size']:>3} (actual {r['actual_size']:>3})  "
        f"prompt_tok={r['prompt_tokens']:>5}  cap_acc={r['cap_accuracy']:>5}%  "
        f"temporal={r['temporal_accuracy']}  "
        f"lat_avg={r['avg_latency_ms']:>5}ms  p95={r['p95_latency_ms']:>5}ms  "
        f"cost/turn=${r['cost_per_turn_usd']:.6f}  malformed={r['malformed_rate']}%  "
        f"errors={r['errors']}"
    )


# ── §11/§27 hierarchical routing experiment (deterministic domain router) ──────────────────

# Map each real target capability's domain -> its capabilities, for a per-domain sub-catalog.
def _domain_catalogs() -> dict[str, list[AssistantTool]]:
    from app.modules.workspace.assistant.contracts import domain_for_capability

    by_domain: dict[str, list[AssistantTool]] = {}
    for t in ASSISTANT_TOOLS:
        d = domain_for_capability(t.name) or "other"
        by_domain.setdefault(d, []).append(t)
    return by_domain


async def _route_domain(text: str, domains: list[str]) -> tuple[str | None, dict]:
    """A lightweight domain-selection LLM call (the router in a hierarchical design)."""
    system = (
        "You are a domain router for a school assistant. Choose the single best DOMAIN for the "
        "user's question from this list, or 'none' if unsupported. Reply with ONLY the domain "
        "word.\nDomains: " + ", ".join(domains) + "\n"
    )
    messages = [LLMMessage(role="system", content=system),
                LLMMessage(role="user", content=text)]
    result = await generate_llm(
        messages, temperature=0.0, max_tokens=10, json_mode=False,
        feature="planner_scale_router", caller="bench.router",
    )
    word = result.text.strip().split()[0].lower().strip(".,:") if result.text.strip() else "none"
    return (word if word in domains else None), {
        "tokens_in": result.tokens_in, "tokens_out": result.tokens_out,
        "latency_ms": result.latency_ms, "model": result.model,
    }


async def run_hierarchical(reps: int) -> dict:
    """B: domain router -> domain sub-catalog -> planner. Compared to flat at the SAME 16 targets
    but as if embedded in a large catalog (the router shrinks what the planner sees)."""
    dcats = _domain_catalogs()
    domains = sorted(dcats)
    cap_scores, lat, cost = [], [], 0.0
    router_correct = 0
    router_total = 0
    from app.modules.workspace.assistant.contracts import domain_for_capability

    for _ in range(reps):
        for text, exp_caps, exp_temp in QUESTIONS:
            r_dom, rmeta = await _route_domain(text, domains + ["none"])
            router_total += 1
            expected_domain = None
            if exp_caps:
                expected_domain = domain_for_capability(next(iter(exp_caps)))
            if (expected_domain is None and r_dom in (None, "none")) or r_dom == expected_domain:
                router_correct += 1
            router_lat = rmeta["latency_ms"]
            router_cost = float(estimate_cost_usd(rmeta["model"], rmeta["tokens_in"],
                                                  rmeta["tokens_out"]))
            if r_dom in (None, "none") or r_dom not in dcats:
                # Router declined; count as correct only for negatives.
                cap_scores.append(1 if not exp_caps else 0)
                lat.append(router_lat)
                cost += router_cost
                continue
            sub = dcats[r_dom]
            pr = await _run_one(sub, text)
            if not pr["ok"]:
                continue
            j = _judge(pr["decision"], exp_caps, exp_temp)
            cap_scores.append(1 if j["cap_ok"] else 0)
            lat.append(router_lat + pr["latency_ms"])
            cost += router_cost + float(
                estimate_cost_usd(pr["model"], pr["tokens_in"], pr["tokens_out"])
            )
    n = len(cap_scores)
    return {
        "router_accuracy": round(router_correct / router_total * 100, 1) if router_total else 0,
        "cap_accuracy": round(sum(cap_scores) / n * 100, 1) if n else 0,
        "avg_latency_ms": round(statistics.mean(lat)) if lat else 0,
        "p95_latency_ms": round(_p95(lat)) if lat else 0,
        "cost_per_turn_usd": round(cost / n, 6) if n else 0,
        "n": n,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sizes", default="16,32,50,75,100,150")
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--router", action="store_true", help="also run the hierarchical experiment")
    ap.add_argument("--compact", action="store_true",
                    help="also run the §22 compact structured-catalog experiment")
    ap.add_argument("--json", default=None)
    args = ap.parse_args()
    sizes = [int(s) for s in args.sizes.split(",") if s.strip()]

    print(f"\n{'=' * 78}\nPLANNER SCALABILITY — FLAT CATALOG  (reps={args.reps}, "
          f"{len(QUESTIONS)} questions/size)\n{'=' * 78}")
    flat = asyncio.run(run_flat(sizes, args.reps, json_out=args.json))

    compact = None
    if args.compact:
        print(f"\n{'=' * 78}\nCOMPACT STRUCTURED CATALOG (§22 — same semantics, denser prompt)\n"
              f"{'=' * 78}")
        compact = asyncio.run(run_flat(sizes, args.reps, compact=True))
        for cr in compact:
            fr = next((r for r in flat if r["size"] == cr["size"]), None)
            if fr:
                dtok = fr["prompt_tokens"] - cr["prompt_tokens"]
                print(f"  size={cr['size']:>3}  prose_tok={fr['prompt_tokens']:>5} -> "
                      f"compact_tok={cr['prompt_tokens']:>5}  (-{dtok})  "
                      f"cap {fr['cap_accuracy']}% -> {cr['cap_accuracy']}%")

    hierarchical = None
    if args.router:
        print(f"\n{'=' * 78}\nHIERARCHICAL ROUTING  (domain router -> sub-catalog -> planner)\n"
              f"{'=' * 78}")
        hierarchical = asyncio.run(run_hierarchical(args.reps))
        h = hierarchical
        print(f"  router_accuracy={h['router_accuracy']}%  cap_accuracy={h['cap_accuracy']}%  "
              f"lat_avg={h['avg_latency_ms']}ms  p95={h['p95_latency_ms']}ms  "
              f"cost/turn=${h['cost_per_turn_usd']:.6f}  n={h['n']}")
        flat16 = next((r for r in flat if r["size"] == 16), None)
        if flat16:
            print("\n  FLAT(16) vs HIERARCHICAL:")
            print(f"    cap_accuracy   {flat16['cap_accuracy']}%  vs  {h['cap_accuracy']}%")
            print(f"    avg_latency    {flat16['avg_latency_ms']}ms  vs  {h['avg_latency_ms']}ms")
            print(f"    cost/turn      ${flat16['cost_per_turn_usd']:.6f}  vs  "
                  f"${h['cost_per_turn_usd']:.6f}")

    if args.json:
        import json
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump({"flat": flat, "hierarchical": hierarchical, "compact": compact}, f,
                      indent=2)
        print(f"\nWrote -> {args.json}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
