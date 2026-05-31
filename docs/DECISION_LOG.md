# StudyNexs — Decision Log, Tradeoffs & Discussion Record

> Owner: Avinash Reddy Masapeta (ARM) · Status: **Living record v1.0** · Last updated: 2026-06-01
> Purpose: capture *what was decided and why*, the tradeoffs weighed, what's still open, and the
> working agreements — so decisions aren't re-litigated and the reasoning survives.
> Companions: [PRODUCT_PLAN.md](./PRODUCT_PLAN.md) · [MASTER_PLAN.md](./MASTER_PLAN.md) · [IMPLEMENTATION_PLAN_P0_P1.md](./IMPLEMENTATION_PLAN_P0_P1.md)

---

## 0. How to read this
- **§1** — the journey so far (chronological).
- **§2** — decisions made (each: the call · why · alternatives · tradeoff · status).
- **§3** — the deeper tradeoff debates and the conclusions.
- **§4** — standing rules / working agreements.
- **§5** — issues found in the existing code (and what happened to them).
- **§6** — open questions still to be discussed/decided.

---

## 1. Journey So Far (chronological)
1. **Reviewed the existing codebase** end-to-end — a multi-tenant FastAPI SMS + a Next.js admin web. Found it solid at the core but with real gaps and bugs (see §5).
2. **ARM shared the product vision** — an AI-native school platform: per-module AI, a phased tutor bot (text→voice→image→video), strict 1:1 teacher/parent/student chat, predictive risk, gamification, parent intelligence, sold on subscription to schools + parents, India-first.
3. **Strategic decisions taken** — evolve vs. greenfield, team, timeline, mobile stack, AI provider (see §2).
4. **Renamed** Academix → StudyNexs (domain availability).
5. **Set ownership + working rules** — ARM-only attribution, no AI attribution, brutally-honest advisor mode, human communication style.
6. **Initialised git**; wrote the Master Plan and the Phase 0/1 implementation plan.
7. **Built & verified Phase 0** — fixed audit/money bugs, added the async job queue, the provider-agnostic LLM gateway, metering. Verified live (OpenAI).
8. **Discovery vs. build debate** — agreed to validate, then ARM produced AI-*generated* "school responses" (not real); we treated them as hypotheses, not validation (see §3.10).
9. **A real school surfaced** — interested, but wants to see a complete working product before finalising. Scope pivoted accordingly (see §2 D13).
10. **Built & proved the Teacher-AI question-paper demo** end-to-end (login → generate → export → approve), seeded a realistic SSC school, curated the web nav.
11. **Documented** the product plan and this decision log.

---

## 2. Decisions Made

**D1 — Evolve the existing codebase; do NOT greenfield.**
- *Why:* the expensive, risky-to-get-wrong parts (multi-tenant isolation, auth/session, fee concurrency) already exist and work; AI features are additive on top; Python/FastAPI is ideal for AI.
- *Alternatives:* full greenfield restart; hybrid harvest.
- *Tradeoff:* inherit some legacy decisions (modular monolith, shared-DB tenancy) — both fine to start, extractable later. Greenfield would have burned the timeline re-deriving undifferentiated plumbing.
- *Status:* **Decided + validated** — the existing suite passes 29/29 tests; the foundation is real, not a facade.

**D2 — Team = solo (ARM + Claude).** Plan favours automation and tight scope. *Status: current reality.*

**D3 — Timeline = ASAP (weeks) to a first pilot.** Implication: full vision is a multi-quarter roadmap; build one thin, real slice at a time. *Status: decided.*

**D4 — Mobile = Flutter** (one codebase iOS+Android). Introduced at the tutor phase (P2), not now. *Status: decided.*

**D5 — AI provider = provider-agnostic gateway; keep options open and benchmark before committing (option B).** Use **OpenAI gpt-4o-mini for the demo** only (proven: ~₹0.13/paper). Do NOT default to Gemini despite the old planning docs. *Tradeoff:* a benchmark is owed (cost/quality across Gemini/Claude/OpenAI) before locking a provider. *Status: decided; benchmark pending.*

**D6 — Renamed Academix → StudyNexs** (the `academix.com` domain was unavailable).
- *Alternatives weighed:* StudyVix (cleaner spelling, but "Vix" is meaningless/edgy) vs. StudyNexs (better meaning — nexus/next — but "Nexs" has spelling friction).
- *Status: decided — StudyNexs.* Full-depth rename done (code, db, configs, docs). Root folder rename pending (manual; see §6).

**D7 — Ownership = Avinash Reddy Masapeta (ARM) only.** Never reference HCL/employer; never add AI-authorship attribution ("Co-Authored-By Claude", etc.) to any artifact. *Status: standing rule; baseline commit scrubbed of attribution.*

**D8 — Communication style = plain/human, not formatted "AI" output — while keeping brutal honesty.** *Status: standing rule.*

**D9 — Phase-1 flagship = Teacher-AI question-paper generator,** with subjective grading included in P1 (teacher-approved). *Why:* fastest to ship, reuses existing stack + exam data, strong school buy-in ("saves teachers hours"). *Status: demo built + proven.*

**D10 — Boards = SSC + CBSE, engine scalable to others.** *Key distinction:* multi-board engine is cheap (board/syllabus/blueprint = data); per-board *content* is costly — so lead with ONE board's content first (CBSE default, or whichever school commits; pilot school is SSC). *Status: decided.*

**D11 — Demo target = SSC, Class 10, Mathematics** (high-stakes board year where papers clearly matter). *Status: built.*

**D12 — Pricing = deferred + segment-dependent** (local vs. premium vs. multi-branch), set from real school conversations. Subscription billing = bought off-the-shelf (Razorpay) later, not built pre-revenue. *Status: decided to defer; unit-economics model owed.*

**D13 — Scope = a complete pilot-ready product, not a one-feature demo** — because a real interested school wants a working product before finalising. *Reframe:* the backend for most core modules already works; the gap is mostly the half-built front end + the AI feature. *Guardrail:* pin "full product" to a finite **written checklist** from the school. *Status: pivot accepted; checklist pending.*

**D14 — Git initialised** on branch `phase-0-foundation`; commit only on ARM's explicit ask. *Status: Phase-0 committed (clean, no attribution); the Teacher-AI demo code is currently uncommitted pending ARM's go-ahead.*

**D15 — Async job queue = Arq** (Redis-backed), replacing the dead outbox. *Status: built + proven (enqueue→worker→done).*

---

## 3. Key Tradeoff Debates (and conclusions)

**3.1 Greenfield vs. evolve.** ~80% of the existing code's value is the invisible foundation (tenancy/auth/money) — the riskiest, least-differentiating work — and ~100% of the AI vision is additive. Conclusion: evolve. The "facade risk" (looks-done-but-broken) was real and checked by running the tests (they pass).

**3.2 Validate-first vs. build-first.** Default is validate-first (talk to schools before building more). Build-first becomes legitimate only when a real school wants a demo to evaluate — which is now the case. So: build the demo *as a tool to validate/close*, not as a substitute for validation.

**3.3 "Zero rework" is the wrong goal.** Chasing zero upfront rework causes over-engineering and analysis-paralysis. Target *avoidable, expensive* rework only — and the cheap insurance against it is fast validation, not perfect upfront architecture.

**3.4 AI is not the differentiator.** Schools "rarely buy because it's AI"; they buy time saved, better academics, easier inspections, happier parents. Lead with outcomes. The moat is board-grounding + workflow integration + human-in-the-loop trust, not "we use AI."

**3.5 Pricing reality risk.** Schools (esp. outside metros) are very price-sensitive — possibly "a few rupees/student/month," far below the old plan's ₹99–149. Because AI cost scales with *usage*, the gap between cost-to-serve and price IS the business. Unit economics must be modelled before pricing is locked.

**3.6 Objective grading should be deterministic, not an LLM.** MCQ/fill-in grading is exact key-matching — cheaper, faster, no hallucination. Reserve AI for generation and subjective grading.

**3.7 Content sourcing & freshness.** Hybrid model: ingest *standard board textbooks* once centrally (same for every school on a board — cost amortised), and have schools upload only their *own* material (question banks, notes). Yearly syllabus changes = versioned content data (RAG packs per board/grade/subject/year); the model never retrains. For pilots, white-glove the content (we do it) rather than building OCR/upload tooling. Capture-error worries (blur/missing pages) mostly vanish because standard content comes from clean PDFs, not photos.

**3.8 Multi-board scope.** The engine should be board-agnostic from day one (cheap), but populating + validating content is per-board and costly — so don't build two boards' content before a single sale.

**3.9 Scope creep.** The demo kept growing each turn (one feature → + mobile tutor → + Ollama fallback → "full product"). Named explicitly and fenced: a demo is a sharp slice on a real backdrop, not the whole product; the AI hook built early so it's never cut.

**3.10 The generated-validation episode (important lesson).** ARM brought back highly polished "school responses" that turned out to be AI-*generated*, not real interviews. Conclusion: founder conviction and synthesised answers are NOT validation — they're confirmation bias in a convincing voice. They're useful hypotheses; only real humans validate. (The episode itself showed how convincing fake validation feels.)

**3.11 Ollama+fallback vs. OpenAI for the demo.** Rejected Ollama-Gemma-4B-primary for the demo: a 4B model risks weaker output for the one demo that must impress, and the fallback plumbing adds work for pennies of saving at demo scale. Ollama remains a strong *production* idea (cost + India data residency) for the later benchmark.

**3.12 Demo shape.** Not a standalone question-paper toy, not the full product — one hero feature (question papers) on a credible, seeded real-school backdrop, with stub pages hidden.

---

## 4. Standing Rules / Working Agreements
- **Brutally-honest advisor mode** — name flaws, risks, blind spots, wishful thinking; don't validate to please; include self-criticism.
- **Plain, human communication** — minimal robotic formatting in conversation; substance unchanged.
- **No AI attribution** in any artifact; **ARM is the sole owner**; never reference any employer.
- **Validate before building**; **human-in-the-loop** for anything consequential.
- **Content as data**; **integrate, don't silo**; **cost-aware AI**; **compliance-first**.
- **Commit only when ARM asks.**

---

## 5. Issues Found in the Existing Code
| Issue | Resolution |
|---|---|
| Audit logging silently broken in prod (wrote a non-existent `user_agent` column) | **Fixed** (column + migration + regression test) |
| Outbox/event system was dead code (never called) | **Replaced** by the Arq job queue |
| Money cast Decimal→float before persisting | **Fixed** (Decimal end-to-end) |
| Notifications not school-scoped | Noted (defense-in-depth; user_id is globally unique) — to harden later |
| README overstated scope (claimed 5 portals; only admin-web + api existed) | Documented honestly in the plans |
| `ai`/`analytics` modules empty; several admin-web pages are stubs | Documented; stubs hidden from demo nav; to be finished per the school checklist |

---

## 6. Open Questions — To Be Discussed / Decided
**Highest leverage:**
- The pilot school's **written must-have-modules checklist** + decision timeline. (Blocks scoping the rest of "full product.")
- Has the school actually *seen* the current build, or is "it's breaking" an assumption? (Fix their real objections, not guessed ones.)
- **Unit-economics / provider benchmark** (Gemini vs. Claude vs. OpenAI on real tasks) → informs pricing + final provider.
- **SSC paper blueprint authenticity** — verify generated papers against a real SSC sample (ideally obtain one).

**Product / build:**
- Final AI provider + model (post-benchmark).
- RAG grounding timing (Phase 1 vs. 1.5); subjective-grading depth in P1.
- Real PDF (install WeasyPrint, with Windows system deps) vs. current HTML print-to-PDF.
- Which core SMS UIs to finish first (exams/marks, report cards, timetable, settings) — driven by the checklist.
- Multi-language (Telugu) timing.

**Compliance / ops:**
- DPDP implementation: parental consent flows, data residency, encryption, retention — before real student data goes live.

**Business / process:**
- Commit the Teacher-AI demo code (pending ARM's go-ahead).
- Whether to keep the `avinash-data/` archive in the repo.
- Root folder rename `academix-platform` → `studynexs-platform` (manual; then update `.claude/settings.local.json` + memory working-dir path).
- A second engineer at Phase 2+ to keep timelines realistic.

---

*This is a living record — update it as decisions are made or revisited.*
