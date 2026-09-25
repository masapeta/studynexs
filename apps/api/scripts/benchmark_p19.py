"""P1.9 — blind LLM cross-school benchmark runner + multi-layer judge.

Exercises the REAL assistant entry point (AssistantService.handle_turn — the exact body the
HTTP /workspace/assistant/turn route calls) so the full pipeline runs: USER -> planner (real
LLM) -> semantic contract -> entity resolution -> conversation state -> derivation ->
SchoolPack -> temporal -> authorization -> capability -> answer (spec §1, §2).

Why in-process (not HTTP): three materially different SchoolPacks (A/B/C/MIN) must be
exercised over ONE real seeded tenant (spec §3 forbids fake production tenants), and blind
pack selection is keyed on tenant_slug (pack_for_tenant). HTTP binds one pack per tenant; the
in-process harness registers synthetic pack tenants and builds a real CurrentUser whose
tenant_slug selects the pack while school_id points at the real reference data. This is the
same blind mechanism the accepted P1.7/P1.8 DB-backed tests use, extended to the whole
pipeline. handle_turn only flush()es (the HTTP route's CommitOnSuccessRoute commits), so the
harness rolls back every conversation and never mutates demo data.

BLIND (spec §2): each turn sends only {text} + the authenticated user. No expected
capability/entity/relationship/pack terminology/routing hint is injected. Expectations live in
benchmark_p19_questions and are compared against the captured trace + block afterwards.

Usage (from apps/api, DB up, LLM reachable):
    python scripts/benchmark_p19.py            # dev set
    python scripts/benchmark_p19.py --holdout  # holdout (run ONCE, after fixes)
    python scripts/benchmark_p19.py --json out.json

Verdicts (spec §24): CORRECT / HONESTLY_UNSUPPORTED / INCORRECT. Distinguishes a query the
school configuration does not support from one the assistant answered incorrectly. Critical
failures (§23) are reported separately.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
import uuid

logging.disable(logging.INFO)  # silence SQLAlchemy echo for readable benchmark output

from benchmark_p19_questions import DEV_CONVERSATIONS, HOLDOUT_CONVERSATIONS  # noqa: E402
from sqlalchemy import select  # noqa: E402

from app.core.database import async_session_factory  # noqa: E402
from app.core.dependencies import CurrentUser  # noqa: E402
from app.db.models.school import School  # noqa: E402
from app.db.models.user import User  # noqa: E402
from app.modules.workspace.assistant.school_pack import register_tenant_pack  # noqa: E402
from app.modules.workspace.assistant.service import AssistantService  # noqa: E402

TENANT = "reference"

# Blind pack selection: synthetic tenant_slugs map to the conceptual packs. The runtime never
# receives "School B uses Form Tutor"; it reads semantics from the pack the tenant maps to.
PACK_TENANT = {"A": "p19_a", "B": "p19_b", "C": "p19_c", "MIN": "p19_min"}
PACK_SLUG = {"A": "school_a", "B": "school_b", "C": "school_c", "MIN": "school_minimal"}

# Real reference personas per role (§17).
ROLE_LOGIN = {
    "principal": "principal",
    "super_admin": "principal",
    "teacher": "teacher6",
    "class_incharge": "teacher1",
    "parent": "parent_demo",
    "student": "student_demo",
}


def _register_packs() -> None:
    for key, tslug in PACK_TENANT.items():
        register_tenant_pack(tslug, PACK_SLUG[key])


async def _load_users(db, school_id) -> dict[str, User]:
    out: dict[str, User] = {}
    for role, uname in ROLE_LOGIN.items():
        if uname in {u.username for u in out.values()}:
            continue
        u = (
            await db.execute(
                select(User).where(User.school_id == school_id, User.username == uname)
            )
        ).scalar_one_or_none()
        if u is None:
            raise SystemExit(f"Reference user missing: {uname}")
        out[role] = u
    return out


def _current_user(user: User, school_id, pack_key: str) -> CurrentUser:
    """Build a CurrentUser whose tenant_slug selects the pack, over the REAL school_id."""
    return CurrentUser(
        id=str(user.id),
        school_id=str(school_id),
        role=user.role.value,
        tenant_slug=PACK_TENANT[pack_key],
        full_name=user.full_name,
        mobile=user.mobile or "",
        is_active=True,
        jti=str(uuid.uuid4()),
    )


def _answer_text(block: dict) -> str:
    parts = [
        str(block.get("title", "")),
        str(block.get("message", "")),
        str(block.get("subtitle", "")),
    ]
    for m in block.get("metrics", []) or []:
        parts.append(f"{m.get('label', '')} {m.get('value', '')}")
    for r in block.get("rows", []) or []:
        parts.append(" ".join(str(v) for v in r.values()))
    for col in block.get("columns", []) or []:
        parts.append(str(col.get("label", "")))
    return " ".join(parts)


_UNSUPPORTED_KINDS = {"guide", "not_found", "clarify"}


def _as_list(v) -> list[str]:
    if not v:
        return []
    return [v] if isinstance(v, str) else list(v)


def judge(turn: dict, block: dict, trace: dict) -> dict:
    """Multi-layer judge (spec §22). Records each observable layer + a final verdict."""
    kind = block.get("kind")
    action = trace.get("action")
    cap = trace.get("capability")
    actual_cap = "compose" if action == "compose" else cap
    sem = trace.get("semantic_temporality")
    text_blob = _answer_text(block)
    text_low = text_blob.lower()

    layers: dict[str, bool] = {}
    reasons: list[str] = []

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
    if turn.get("derive"):
        prov = trace.get("param_provenance") or []
        layers["derivation"] = any(p.get("source") == "DERIVED" for p in prov)
        if not layers["derivation"]:
            reasons.append("expected a DERIVED parameter")
    if turn.get("kind"):
        layers["kind"] = kind in turn["kind"]
        if not layers["kind"]:
            reasons.append(f"kind {kind} not in {sorted(turn['kind'])}")

    # SchoolPack surface / calculation layer (substring checks).
    for want in _as_list(turn.get("expect_text")):
        ok = want.lower() in text_low
        layers[f"text:{want}"] = ok
        if not ok:
            reasons.append(f"missing expected text {want!r}")
    # Term-leakage guard (§7) — a forbidden pack term must never surface.
    leaked: list[str] = []
    for bad in _as_list(turn.get("forbid_text")):
        present = bad.lower() in text_low
        layers[f"noleak:{bad}"] = not present
        if present:
            leaked.append(bad)
            reasons.append(f"LEAKED forbidden text {bad!r}")

    hard = [v for v in layers.values() if v is not None]

    if turn.get("outcome") == "HONESTLY_UNSUPPORTED":
        honest = kind in _UNSUPPORTED_KINDS or (turn.get("kind") and kind in turn["kind"])
        verdict = "HONESTLY_UNSUPPORTED" if honest and all(hard) else "INCORRECT"
    else:
        if turn.get("soft") and kind in _UNSUPPORTED_KINDS:
            # An honest fallback satisfies a soft target — but a leak is still a failure.
            verdict = "INCORRECT" if leaked else "HONESTLY_UNSUPPORTED"
        else:
            verdict = "CORRECT" if all(hard) else "INCORRECT"

    return {
        "verdict": verdict, "layers": layers, "reasons": reasons,
        "actual_cap": actual_cap, "actual_kind": kind, "sem": sem,
        "leaked": leaked,
    }


async def run_conversation(conv: dict, users: dict, school_id) -> list[dict]:
    """Run one conversation on its own session under its pack, then roll back (no data change)."""
    records: list[dict] = []
    role = conv["role"]
    user = users[role]
    cu = _current_user(user, school_id, conv["pack"])
    async with async_session_factory() as db:
        service = AssistantService(db)
        sid: uuid.UUID | None = None
        for i, turn in enumerate(conv["turns"], 1):
            try:
                resp = await service.handle_turn(
                    current_user=cu, text=turn["text"], session_id=sid
                )
            except Exception as e:  # noqa: BLE001 — capture as an INCORRECT turn, keep going
                resp = {"block": {"kind": "error", "title": f"ERROR {type(e).__name__}: {e}"},
                        "trace": {}, "session_id": None}
            sid_str = resp.get("session_id")
            sid = uuid.UUID(sid_str) if sid_str else sid
            block, trace = resp.get("block", {}), resp.get("trace", {})
            v = judge(turn, block, trace)
            records.append({
                "conv": conv["id"], "pack": conv["pack"], "role": role, "turn": i,
                "text": turn["text"], "critical": bool(turn.get("critical")),
                "outcome_target": turn.get("outcome"), **v,
            })
        await db.rollback()  # never persist benchmark chat into the demo tenant
    return records


async def run(conversations: list[dict], json_out: str | None) -> None:
    _register_packs()
    async with async_session_factory() as db:
        school = (
            await db.execute(select(School).where(School.tenant_slug == TENANT))
        ).scalar_one_or_none()
        if school is None:
            raise SystemExit(f"Tenant {TENANT!r} not found — is the reference school seeded?")
        school_id = school.id
        users = await _load_users(db, school_id)

    records: list[dict] = []
    for conv in conversations:
        records.extend(await run_conversation(conv, users, school_id))

    _report(records, conversations, json_out)


def _report(records: list[dict], conversations: list[dict], json_out: str | None) -> None:
    n = len(records)
    c = sum(1 for r in records if r["verdict"] == "CORRECT")
    h = sum(1 for r in records if r["verdict"] == "HONESTLY_UNSUPPORTED")
    inc = sum(1 for r in records if r["verdict"] == "INCORRECT")
    trust = c / (c + inc) * 100 if (c + inc) else 100.0

    print(f"\n{'=' * 68}")
    print(f"P1.9 BLIND CROSS-SCHOOL BENCHMARK   (turns={n}, convos={len(conversations)})")
    print(f"{'=' * 68}")
    print(f"CORRECT {c}   HONESTLY_UNSUPPORTED {h}   INCORRECT {inc}   trust={trust:.1f}%")

    # Per-school (spec §28).
    print("\nPer-school:")
    for pk in ("A", "B", "C", "MIN"):
        sub = [r for r in records if r["pack"] == pk]
        if not sub:
            continue
        sc = sum(1 for r in sub if r["verdict"] == "CORRECT")
        sh = sum(1 for r in sub if r["verdict"] == "HONESTLY_UNSUPPORTED")
        si = sum(1 for r in sub if r["verdict"] == "INCORRECT")
        print(f"  School {pk:3s}  turns={len(sub):3d}  CORRECT {sc}  HONEST {sh}  INCORRECT {si}")

    # Per-layer (spec §22/§28).
    print("\nPer-layer:")
    layer_names = ("capability", "temporal", "entity", "derivation", "kind")
    for layer in layer_names:
        vals = [r["layers"].get(layer) for r in records if r["layers"].get(layer) is not None]
        if vals:
            print(f"  {layer:12s} {sum(1 for x in vals if x)}/{len(vals)}")
    # Aggregate the substring / no-leak layers.
    text_vals = [v for r in records for k, v in r["layers"].items() if k.startswith("text:")]
    leak_vals = [v for r in records for k, v in r["layers"].items() if k.startswith("noleak:")]
    if text_vals:
        print(f"  {'calculation':12s} {sum(1 for x in text_vals if x)}/{len(text_vals)}"
              "  (expected SchoolPack-scored values present)")
    if leak_vals:
        print(f"  {'no-leak':12s} {sum(1 for x in leak_vals if x)}/{len(leak_vals)}"
              "  (forbidden pack terms absent)")

    # Cross-school consistency: same-intent triples should be semantically equivalent (§28).
    print("\nCross-school consistency (same intent, different pack):")
    _consistency(records, "responsible", ("dev-responsible-A", "dev-responsible-B",
                                          "dev-responsible-C"))
    _consistency(records, "attendance-same-wording", ("dev-att-A", "dev-att-B"))

    crit = [r for r in records if r["critical"] and r["verdict"] == "INCORRECT"]
    print(f"\nCRITICAL FAILURES: {len(crit)}")
    for r in crit:
        print(f"  [{r['conv']} t{r['turn']} pack {r['pack']} {r['role']}] {r['text']!r}")
        print(f"      kind={r['actual_kind']} cap={r['actual_cap']} {r['reasons']}")

    incs = [r for r in records if r["verdict"] == "INCORRECT"]
    if incs:
        print("\nINCORRECT (all):")
        for r in incs:
            print(f"  [{r['conv']} t{r['turn']} pack {r['pack']} {r['role']}] {r['text']!r}")
            print(f"      kind={r['actual_kind']} cap={r['actual_cap']} sem={r['sem']} "
                  f"{r['reasons']}")

    if json_out:
        import json
        with open(json_out, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)
        print(f"\nWrote -> {json_out}")


def _consistency(records: list[dict], label: str, conv_ids: tuple[str, ...]) -> None:
    verdicts = {}
    for cid in conv_ids:
        rs = [r for r in records if r["conv"] == cid]
        if rs:
            verdicts[cid] = rs[0]["verdict"]
    if not verdicts:
        return
    equal = len(set(verdicts.values())) == 1
    caps = {r["actual_cap"] for cid in conv_ids for r in records if r["conv"] == cid}
    print(f"  {label:26s} verdicts={verdicts}  caps={sorted(c for c in caps if c)}  "
          f"{'CONSISTENT' if equal else 'INCONSISTENT'}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--holdout", action="store_true", help="run the holdout set (once, post-fix)")
    ap.add_argument("--json", default=None)
    args = ap.parse_args()
    convs = HOLDOUT_CONVERSATIONS if args.holdout else DEV_CONVERSATIONS
    label = "HOLDOUT" if args.holdout else "DEV"
    print(f"Running P1.9 {label} set ({len(convs)} conversations)...")
    asyncio.run(run(convs, args.json))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
