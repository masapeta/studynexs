# StudyNexs — Decision Log

> **Canonical location:** `docs/decisions/DECISION_LOG.md`  
> Owner: Avinash Reddy Masapeta (ARM) · **Living record** — never delete entries.

This file is the **authoritative Decision Log** in the governance hierarchy.  
See [`../README.md`](../README.md) for document precedence.

---

## 2026-08-24 — Verification standard: "reproduce in the running product, or it isn't fixed"

**Decision:** For Gate S production-trust remediation, an item may only be marked fixed when
the failure was **reproduced in the running product first** and the fix **re-verified there**.
Unit tests are necessary but never sufficient evidence. Each fix additionally ships a
regression test proven to fail before it and pass after (red→green demonstrated, not assumed).

**Reason:** The Production Trust Audit found a 970-test green suite coexisting with every P1
still reproducible by hand. Phase 0 then produced a concrete mechanism for that gap: pytest
inserts its rootdir (`apps/api`) at `sys.path[0]`, and a real directory outranks an
editable-install finder — so **pytest always imported the local `app/` even while the editable
install pointed at the archived `academix-platform` repo**, which is what `uvicorn` actually
served. The obvious guard (`assert "academix-platform" not in app.__file__`) was verified to
*pass while the bug was active*. Test-suite green is therefore not evidence of runtime health.

**Consequence:** guards for environment-class defects must assert on the **installed
distribution record**, not the imported module. `tests/test_canonical_runtime.py` is a hard CI
gate. Any future "certified" claim in `STATUS.md` requires a live-verification column entry.

**Alternatives considered:** (a) trust the existing suite — rejected, empirically disproven;
(b) assert a route *count* (182) — rejected, breaks on every new endpoint, so pinned five
canary routes instead.

**Rollback:** none needed; additive test + docs only.

---

## 2026-08-25 — Attendance upserts must move the row to the marking class (P1-DATA-001)

**Decision:** `mark_bulk`'s `ON CONFLICT … set_` now updates `class_id`. Whenever a uniqueness
constraint deliberately collapses a fact to one row, **every column that identifies the
context of that fact must appear in the update clause** — otherwise the row silently keeps a
stale context.

**Reason:** `uq_attendance_student_date` is `(school_id, student_id, date)` — one row per
student per day, by design. `class_id` was omitted from the update, so a student who changed
class mid-day kept the row on the *old* class. Verified live: the receiving teacher marked the
student present, got *"Attendance marked for 1 students"*, and their register showed nothing —
while the class the student had left still counted them. Two teachers' screens contradicted
each other with no error anywhere.

**Why this class of bug is dangerous:** it is a **silent** data-correctness failure on a daily
workflow. Attendance feeds report cards and parent communication, so a wrong row propagates.
No exception, no log, no user-visible signal.

**Scope checked:** the two sibling upserts are correct — `mastery_service` already updates
`class_id`, and `ExamMark` has no `class_id` (class is reached via the exam). `mark_bulk` is
also the only attendance write path, so this was an isolated oversight, not a policy.

**Prevention:** `tests/test_attendance_class_change.py` asserts on the **register and summary a
teacher sees**, not merely the stored row — the row alone would not have revealed the
double-counting. A third test pins the same-class correction path (update in place, never a
duplicate) so the fix cannot over-correct.

**Rollback:** drop `"class_id": stmt.excluded.class_id` — this reopens silent corruption.

---

## 2026-08-24 — One tolerant LLM JSON parser; raw model output is never logged (P1-AI-001/002)

**Decision:** All LLM structured output is parsed by exactly one utility,
`app/modules/ai/gateway/json_parse.py::parse_llm_json`. Bare `json.loads(<llm result>.text)`
is banned in `app/` and enforced by an AST-based test. The parser recovers well-formed JSON
from decoration (markdown fences, surrounding prose) but **never repairs malformed JSON**.
Separately: **raw model output must not be logged** — only a structural fingerprint.

**Reason:** Nine call sites each parsed provider text by hand, and the configured provider
(`gemma4:cloud`) returns markdown-fenced JSON for structured prompts. The result was a 100%
failure rate on the Student Tutor, question-paper generation and Teacher Copilot, reproduced
live at 10-of-14 probes failing — while the unit suite stayed green, because no test exercised
a realistic provider payload. Students were shown the developer string
`"Copilot returned invalid JSON"`.

**Why not repair malformed JSON:** a silently "fixed" exam paper or grade is worse than a
clean failure, so truncated/invalid JSON raises `LLMJsonError` and the feature declines.
Grounded-and-absent beats confidently-wrong (§109.1).

**Why raw output is not logged:** consolidating nine sites onto one parser would have widened
two pre-existing `raw=(result.text)[:400]` log lines to *all* AI surfaces — including tutor,
parent-copilot and evaluation replies, which contain student names, mobiles, answers and marks
(§31, §43, §62.5). The parser logs `feature`, `raw_len` and a content-free shape
(`starts=… fence=yes braces=1/0 …`), which is sufficient to spot a provider regression.

**Tradeoff accepted:** losing the raw text costs some debuggability on novel provider quirks.
Mitigated by the shape fingerprint and by `llm_json_recovered` telemetry, which reveals a
format drift *before* it becomes a failure.

**Prevention:** call-site-level tests (a utility-only test would not have caught the original
bug) — `test_llm_json_call_sites.py` (AST guard + per-module feature tags),
`test_llm_json_parse.py` (27, incl. a verbatim captured provider payload), and
`test_llm_json_no_leak_endpoint.py` (hostile payloads never reach users; PII never reaches
logs). The last file also carries a **guard-the-guard** test: structlog writes to stdout, so a
`caplog`-based leak assertion silently passes against an empty string — it false-passed on the
first attempt and now uses `capsys`.

**Rollback:** revert the nine call sites to `json.loads`; this reintroduces total failure
against the current provider.

---

## 2026-08-24 — Fee aggregates are admin-only (P0-SEC-001)

**Decision:** School-wide fee aggregate endpoints (`/fees/recent`, `/fees/roster`,
`/fees/stats`) are restricted to `admin` and `super_admin`. `teacher` was removed from
`GET /fees/recent`. Teaching roles read a single child's fees only via
`/fees/student/{id}`, which is object-authorized by `assert_can_access_student`.

**Reason:** `require_roles("admin", "super_admin", "teacher")` let any subject teacher
enumerate every family's payment history — verified live at 50 receipts across 49 households
(₹125,000), including student name, class, amount, mode, and receipt number. Under DPDP that
is a reportable disclosure of guardians' financial data. `/stats` and `/roster` already omitted
`teacher`, so this was a copy-paste slip, not a policy choice; `class_incharge` was already
correctly denied.

**Tradeoff accepted:** none material. The only caller
(`admin-web/src/components/briefing/DashboardWidgets.tsx`) already gates the request behind
`isAdmin`, so the change is additive-safe with no UI regression.

**Prevention:** `tests/test_fee_authorization_matrix.py` asserts **every** `UserRole` against
every fee aggregate on **seeded real payment data** (a `200` with `[]` is explicitly rejected
as an authorization pass), plus a static guard that fails if any fee route ever names a
teaching/portal role in `require_roles`.

**Rollback:** re-add `"teacher"` to the decorator — but this would reopen the disclosure.

---

## 2026-08-04 — AEI v1.0 pilot activation Stages 1–2 authorized

**Decision:** ARM authorizes enabling the certified AEI v1.0 Stage 1 and
Stage 2 capabilities for the pilot school:

- Stage 1: `AEI_V1_MATH_NORMALIZATION_ENABLED`, `AEI_V1_REVIEW_POLICY_ENABLED`
- Stage 2: `AEI_V1_EVIDENCE_LEDGER_METADATA_ENABLED`,
  `AEI_V1_LANGUAGE_OCR_ASSIST_ENABLED`, `AEI_V1_VISUAL_SCIENCE_ASSIST_ENABLED`

**Reason:** All five capabilities are certified, published, default-off, and
additive: Stage 1 is deterministic normalization plus review-posture labels;
Stage 2 is metadata on the same teacher workflow. Marks behavior, teacher
authority, and the certified product-claim boundary are unchanged. Activating
them requires nothing collected from the school and starts producing real
teacher-trust evidence immediately.

**Procedure:** [`../runbooks/aei-pilot-activation.md`](../runbooks/aei-pilot-activation.md)
— set the flags in the pilot deployment environment, restart API + worker,
run the post-stage verification. Rollback is flags-off + restart.

**Scope boundary:** This decision does not authorize Stage 3 (manual-review
acknowledgement enforcement), Stage 4 (handwriting OCR), the Track-A live
benchmark run start (its contract prerequisites must still be confirmed), any
production OCR routing change, or any product-claim expansion. Each requires
separate ARM authorization.

**Status:** Active

---

## 2026-07-28 — Production Safety Gate 1 accepted

**Decision:** Accept and authorize publication of Stabilization Gate 1 —
Production Safety.

**Reason:** The scoped implementation closes the validated direct-dependency,
production CORS, notification tenancy, teacher pagination, Decimal arithmetic,
and truthful PDF defects. Changed-scope and adjacent regression validation,
independent review, a final production-image build, and multilingual PDF runtime
proof passed. The bounded repository-wide test run limitation is recorded in
the certification report rather than misrepresented as a pass.

**Scope boundary:** This decision does not authorize Operational Proof, AEI
activation, topic-ID/mastery work, or Teacher Evaluation UX-D.

**Acceptance evidence:**
[`../product/PRODUCTION_SAFETY_BATCH_CERTIFICATION_REPORT.md`](../product/PRODUCTION_SAFETY_BATCH_CERTIFICATION_REPORT.md)

**Status:** Active

---

## 2026-07-28 — Stabilization sequence supersedes UX-D as the next gate

**Decision:** Reconcile the operational governance sources and execute the
following order: Production Safety, Operational Proof, AEI Activation/Trust,
topic-ID/mastery spine unification design, then Teacher Evaluation UX-D.

**Reason:** Independent validation of the July 2026 war-room audit confirmed
production-safety and operational-proof gaps that must be closed before more
teacher-facing assist UI is added. Certified AEI capabilities also require a
controlled activation and trust proof before UX-D can truthfully expose their
supported-scope metadata.

**Authorization:** Production Safety is the single active implementation gate
after governance reconciliation. Operational Proof, AEI Activation/Trust,
topic-ID/mastery work, and UX-D are ordered future gates only; none is
authorized by this decision.

**Historical preservation:** Release 0.1 through Release 0.3 and published
AEI/EUI milestones remain accepted and frozen. Earlier statements naming UX-D
as the immediate next milestone are superseded, not deleted.

**Status:** Superseded by the Production Safety acceptance entry above.

**References:** [`../product/PRODUCT_EXECUTION_PLAN.md`](../product/PRODUCT_EXECUTION_PLAN.md) · [`../product/CURRENT_BATCH.md`](../product/CURRENT_BATCH.md) · [`../STATUS.md`](../STATUS.md)

---

## 2026-07-23 — Batch 3 School Pilot Experience accepted and frozen

**Decision:** Accept **Release 0.3 / Batch 3 — School Pilot Experience** and freeze its architecture and implementation.

**Reason:** Batch 3 proves that the existing Principal and Teacher pilot journeys can complete successfully without engineering assistance during the walkthrough. The batch validated login, tenant scope, curriculum readiness, Academic Intelligence readiness, teacher class/subject scope, same-pack grounded lesson-plan generation, same-pack grounded question-paper generation, and focused browser walkthroughs.

**Acceptance evidence:**

- [`../product/BATCH_03_COMPLETION_REPORT.md`](../product/BATCH_03_COMPLETION_REPORT.md)
- commit `649d835` — `feat(pilot): complete Batch 3 principal teacher proof`
- runtime proof pack `1bdfffc6-933d-4780-9de4-b7d6c92201bb`

**Known pilot preflight:** Reference tenant AI credits were exhausted by repeated validation runs. The existing principal emergency override path is validated and should be part of pilot preflight when needed.

**Freeze rule:** Do not modify Batch 3 except for production defects, security fixes, or critical regressions.

**Status:** Active

---

## 2026-07-23 — Batch 2 Academic Onboarding accepted and frozen

**Decision:** Accept **Release 0.2 / Batch 2 — Academic Onboarding** and freeze its architecture and implementation.

**Reason:** Batch 2 proves that a newly uploaded curriculum source can become a human-approved `CurriculumPack`, reach KG/RAG readiness, and ground downstream lesson plans, learning materials, question papers, assessment evaluation, mastery, Student Tutor/Copilot, and Parent Copilot through the same approved academic memory.

**Acceptance evidence:**

- [`../product/BATCH_02_COMPLETION_REPORT.md`](../product/BATCH_02_COMPLETION_REPORT.md)
- commit `469c0f8` — `feat(onboarding): complete Batch 2 academic onboarding proof`
- runtime proof pack `1bdfffc6-933d-4780-9de4-b7d6c92201bb`

**Known operational limitation:** Production async evaluation worker parity remains an operational hardening task. This is not a Batch 2 product blocker because the existing evaluation service behavior is validated through runtime proof.

**Freeze rule:** Do not modify Batch 2 except for production defects, security fixes, or critical regressions.

**Status:** Active

---

## 2026-07-23 — Batch 1 Curriculum Intelligence accepted and frozen

**Decision:** Accept **Batch 1 — Curriculum Intelligence** as Release 0.1 and freeze its architecture and implementation.

**Reason:** Batch 1 now has curriculum ownership, approval governance, tenant-scoped `CurriculumPack`, KG/RAG grounding, same-pack grounding across multiple AI capabilities, teacher-owned workflow, runtime validation, explicit limitations, and a fixed completion artifact.

**Acceptance evidence:**

- [`../product/BATCH_01_COMPLETION_REPORT.md`](../product/BATCH_01_COMPLETION_REPORT.md)
- commit `63a5584` — `feat(curriculum): complete Batch 1 intelligence closure`

**Freeze rule:** Do not modify Batch 1 except for production defects, security fixes, or critical regressions.

**Status:** Active

---

## 2026-07-23 — Batch 2 renamed to Academic Onboarding

**Decision:** Rename the next product execution batch to **Batch 2 — Academic Onboarding**.

**Reason:** The next capability is not merely textbook ingestion. It is the first curriculum-first experience a school has with StudyNexs: create/select school context, provide syllabus/TOC/curriculum source, AI extracts structure, human reviews, approval triggers KG/RAG, and the product reaches **Academic Intelligence Ready**.

**Architecture constraints:** Batch 2 must reuse `CurriculumPack`, Document Intelligence, `CurriculumExtractionService`, the existing approval workflow, `PackService.approve_pack()`, KG, RAG, the LLM gateway, and downstream AI grounding. It must not create a parallel curriculum engine or ingestion stack.

**Out of scope:** Full textbook warehousing, complete OCR automation, advanced report cards, rich student practice engine, and Batch 3 assessment automation.

**Status:** Superseded by Batch 2 authorization entry below.

**References:** [`../product/PRODUCT_EXECUTION_PLAN.md`](../product/PRODUCT_EXECUTION_PLAN.md) · [`../product/RELEASE_HISTORY.md`](../product/RELEASE_HISTORY.md)

---

## 2026-07-23 — Batch 2 Academic Onboarding authorized

**Decision:** Authorize **Release 0.2 / Batch 2 — Academic Onboarding** to begin implementation.

**Scope:** Build the curriculum-first onboarding experience that lets a school provide a syllabus / TOC / curriculum source, creates a draft `CurriculumPack`, supports human review, approves through the existing governance workflow, triggers KG/RAG indexing, reaches **Academic Intelligence Ready**, and proves downstream lesson-plan and question-paper generation ground on the same newly approved pack.

**Constraints:** Reuse `CurriculumPack`, Document Intelligence, `CurriculumExtractionService`, the existing approval workflow, `PackService.approve_pack()`, KG, RAG, the LLM gateway, AI credits, RBAC, and downstream grounding. Do not build a second curriculum engine, parallel ingestion service, full textbook warehousing, complete OCR automation, advanced report cards, rich student practice engine, or Batch 3 assessment expansion.

**Operational rule:** During Batch 2, do not create intermediate planning/governance documents. Update governance only when Batch 2 is complete or when ARM explicitly requests it.

**Status:** Superseded by Batch 2 acceptance entry above.

**References:** [`../product/CURRENT_BATCH.md`](../product/CURRENT_BATCH.md) · [`../product/PRODUCT_EXECUTION_PLAN.md`](../product/PRODUCT_EXECUTION_PLAN.md)

---

## 2026-07-22 — Stage 2A: Production Academic Onboarding Core (authorized)

**Decision:** Ship **Academic Onboarding** for permanent paid-school tenants first — admin/HOD supplies board/class/subject/textbook metadata plus permitted curriculum inputs (TOC, syllabus, chapter list); AI proposes a draft CurriculumPack; HOD/principal reviews/edits and approves; approval triggers existing KG spine + RAG indexing via `PackService.approve_pack`; UI shows **Academic Intelligence Ready** only after both KG and RAG audit events succeed.

**Reason:** Schools must teach StudyNexs their curriculum once before lesson plans, question papers, and tutor surfaces can be grounded and trustworthy. Stage 1 localhost validation is accepted; Gate 1A HTTPS remains a separate deployment gate. This slice reuses the existing platform — no parallel curriculum, graph, RAG, or AI stacks.

**Alternatives:** (1) Manual-only pack builder (Slice 1) — rejected for paid onboarding scale; (2) Full textbook warehousing — rejected (copyright + constitution §39.1); (3) Public self-guided demo tenants in same slice — deferred to later stage.

**Out of scope (Stage 2A):** Public signup, tenant cloning, TTL cleanup, digital student assessment, parent automation.

**Implementation seams (reuse, do not duplicate):**

- `CurriculumExtractionService` → LLM gateway + credits (`curriculum_extraction`, 3 credits)
- `PackService.populate_draft_structure` / `approve_pack` → KG + RAG side effects
- `GET /packs/{id}/intelligence-status` → readiness gate for UI banner
- Admin UI: `/dashboard/teaching/curriculum/onboarding` wizard + `AcademicIntelligenceBanner` on curriculum, lesson-plans, ai-papers

**Status:** Active (Stage 2A shipped — ARM accepted 2026-07-22)

**References:** [`../product/PRODUCT_EXECUTION_PLAN.md`](../product/PRODUCT_EXECUTION_PLAN.md) · [`../showcase/DEMO_EXPERIENCE_GAP_ANALYSIS.md`](../showcase/DEMO_EXPERIENCE_GAP_ANALYSIS.md)

---

## 2026-07-17 — Product Execution Phase begins

**Decision:** Close Platform Foundation Phase; adopt Product Execution Constitution v1.0 and governance hierarchy.

**Reason:** Platform, governance, and Design System v1 are complete. Engineering priority shifts to educational capabilities (Batch 1: Curriculum Intelligence).

**Alternatives:** Continue platform polish (Phase 3B UI); parallel batch work — rejected per scope discipline.

**Status:** Active

**References:**

- [`../product/PRODUCT_EXECUTION_CONSTITUTION.md`](../product/PRODUCT_EXECUTION_CONSTITUTION.md)
- [`../product/PRODUCT_EXECUTION_PLAN.md`](../product/PRODUCT_EXECUTION_PLAN.md)
- [`../design/PLATFORM_DESIGN_SYSTEM_V1.md`](../design/PLATFORM_DESIGN_SYSTEM_V1.md)

---

## Prior decisions

Historical decisions from the Platform Foundation Phase and earlier product work are preserved in the archive:

**[`../DECISION_LOG_ARCHIVE.md`](../DECISION_LOG_ARCHIVE.md)**

(New entries from 2026-07-17 onward are appended to this file.)

---

## Entry template

```text
## YYYY-MM-DD — Title

**Decision:**

**Reason:**

**Alternatives:**

**Status:** Active | Superseded | Deferred
```
