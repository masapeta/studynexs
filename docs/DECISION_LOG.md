# StudyNexs — Decision Log, Tradeoffs & Discussion Record

> Owner: Avinash Reddy Masapeta (ARM) · Status: **Living record v1.0** · Last updated: 2026-06-18
> Purpose: capture *what was decided and why*, the tradeoffs weighed, what's still open, and the
> working agreements — so decisions aren't re-litigated and the reasoning survives.
> Companions: [PRODUCT.md](./PRODUCT.md) · [STATUS.md](./STATUS.md) · [BACKLOG.md](./BACKLOG.md)

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

**D7 — Ownership = Noustriks; founder Avinash Reddy Masapeta (ARM) only.** StudyNexs is a Noustriks product. Never reference HCL/employer; never add AI-authorship attribution ("Co-Authored-By Claude", etc.) to any artifact. *Status: standing rule; baseline commit scrubbed of attribution.*

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
- ~~RAG grounding timing (Phase 1 vs. 1.5)~~ → **Decided:** CurriculumPack in Phase 1.5; QP/grading/mastery attach to pack, not free-text topics.
- Subjective-grading depth in P1.
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

## 7. Decision — CurriculumPack as core object (2026-06-16)

**The call:** Introduce `CurriculumPack` as the versioned source of truth for each school's class × subject × academic year curriculum (book edition, chapter → topic → concept hierarchy). All academic AI — question papers, answer-sheet evaluation, rubrics, question bank, mastery, tutor RAG — runs against an approved pack. Never overwrite packs; create new versions per year and diff changes (Curriculum Change Tracker). Cross-year concept mapping preserves longitudinal history when books change.

**Why:** Schools use different publishers and editions; generic "Class 7 Science" prompts produce wrong papers and unreliable grading. Pack-scoped intelligence is the moat — it connects QP generation, evaluation, mastery, and institutional memory into one compounding data model.

**Alternatives considered:** (a) free-text topic list at QP time (current P1 approach); (b) central board-only content packs without per-school book mapping; (c) hardcoded SSC blueprints in code.

**Tradeoff:** More onboarding work upfront (but minimal inputs + AI draft + one HOD approval). Pays off in evaluation accuracy, change tracking, and switching cost.

**Status:** Documented in [PRODUCT.md](./PRODUCT.md) §4–§8. Not yet implemented — [STATUS.md](./STATUS.md) 8-week plan.

### Decision — No textbook warehousing (2026-06-17)

**The call:** Store structured curriculum (metadata, chapter/topic/concept map, approved Concept Cards, rubrics, references) — not full copyrighted textbooks. Raw uploads only for temporary ingestion, deduped, retention-limited. Use NCERT/ePathshala with reuse-rights checks.

**Why:** Copyright risk under Indian law; operational cost of maintaining book copies; structured maps are sufficient for QP, evaluation, and tutor.

**Status:** Documented in [PRODUCT.md](./PRODUCT.md) §4.8–§4.11.

### Decision — Mistake Recovery Tutor as MVP (2026-06-17)

**The call:** First tutor experience is post answer-sheet evaluation on weak concepts, powered by pre-approved Concept Cards — not open-ended chat requiring per-response approval.

**Why:** Tighter scope, connects to exam loop, builds reusable content layer via Content Review Queue.

**Status:** Week 8 of [STATUS.md](./STATUS.md) 8-week plan.

### Decision — Question-level intelligence (2026-06-18)

**The call:** Unit of memory is the **question item**, not the paper PDF. Split papers into `QuestionBankItem` + `RubricBankItem` with full pack metadata; similarity checker; post-gen quality checker; difficulty calibration from answer-sheet eval; structured approval/rejection memory; exam security layer; tiered reuse modes. Build order: papers saved → split items → reject reasons → bank → from-bank gen → quality check → eval linkback.

**Why:** Every exam makes the next exam smarter — academic moat inside the QP wedge.

**Status:** [PRODUCT.md](./PRODUCT.md) §7.5. Steps 1 + partial 3 live in repo.

### Decision — Exam intelligence enhancements (2026-06-18)

**The call:** Twelve extensions documented in §7.6 — blueprint intelligence, paper versioning (Set A/B…), teacher style memory, multi-layer HOD workflow, leakage prevention, answer-key confidence, misconception library, auto remedial packs, benchmarking (later), curriculum drift alerts, inspection pack, PTA pack. **Top 5 build priority:** question bank, blueprint intelligence, eval→question analytics, remedial worksheets, inspection/PTA pack.

**Compounding story:** Generate better papers → correct faster → understand weakness → remediate → prove improvement.

**Status:** Documented only — not implemented.

### Decision — School question bank architecture (2026-06-18)

**The call:** Generated QPs are **not** cache-only. **Both approved and rejected papers are assets.** Approved → trusted bank (auto-compose). Rejected → audit trail **and** manual reuse (edit, clone, resubmit → re-approve enters bank). Only approved items auto-index for `qp_from_bank`.

**Why:** Cost saver (retrieve items, not whole papers), quality improver (trusted approved blocks), moat (compounding school data).

**Status:** Documented in [PRODUCT.md](./PRODUCT.md) §7.4. `QuestionBankItem` entity not built — Phase 1.5 after CurriculumPack.

### Decision — Pricing tier structure (2026-06-18)

**The call:** Four public tiers — **Free** (controlled demo), **Pro** (exam starter), **Pro+** (main growth plan), **Enterprise** (chains / custom). No unlimited AI in any tier. Credits charge at generation, not approval. Add-ons (extra credits, WhatsApp pack, tutor pack, Finance Command Center) stay separate from base plans.

**Sales motion (first 3–5 schools):** Publicly show all tiers; sell **Paid Pilot = Pro+ scoped to one class + one subject**. Don't push four equal choices.

**Why:** Free creates interest without letting schools run production on it. Pro closes small schools. Pro+ is where exam intelligence + parent value live. Enterprise protects high-usage and multi-branch deals. Rupee prices still deferred until pilot WTP validation.

**Status:** Documented in [PRICING.md](./PRICING.md). Razorpay SKUs and API plan gates not built yet.

### Decision — Learning Companion beside textbooks (2026-06-18)

**The call:** StudyNexs Learning Companion (school-customized smart workbooks) sits **beside** NCERT/private textbooks — never replaces or rewrites them. Content is curriculum-aligned and originally written from CurriculumPack + Concept Cards + exam data. Entry formats: chapter companions, revision booklets, practice workbooks, mistake recovery sheets, exam prep packs. Full living textbook is 1–2 year horizon. Layer 4 in build sequence — after QP, eval, mastery, tutor.

**Why:** Copyright protects expression; schools trust physical books; revision workbooks are easier to sell than "replace your textbook."

**Wow line:** *"Your school's book gets smarter every exam."*

**Status:** [PRODUCT.md](./PRODUCT.md) §8.

### Decision — Global Enrichment Studio (2026-06-18)

**The call:** **Global Learning Inspiration Layer** shipped as product feature **Global Enrichment Studio**. Schools submit international sources or descriptions; platform classifies license risk (Green/Yellow/Red); extracts **pedagogical pattern only**; generates **original** content mapped to CurriculumPack; teacher/HOD approves. CC BY allowed with attribution; CC-NC and CC-ND block expression adaptation in commercial SaaS. Year 2 premium — after smart workbooks.

**Rule:** International content can inspire. It must not be copied.

**Sticky note:** *StudyNexs does not copy textbooks. It helps schools turn the world's best teaching ideas into their own approved learning material.*

**Status:** [PRODUCT.md](./PRODUCT.md) §8.8.

### Decision — Admin bypass of school AI hard cap (2026-06-15)

**The call:** `admin` and `super_admin` roles **skip the school monthly credit hard cap** in `check_ai_credits`. Teachers and class incharges remain subject to the school pool and per-user quotas. Principal **emergency override** (`override_until` in school settings) lifts the cap for everyone for up to 72 hours.

**Why:** Exam week and pilot demos cannot deadlock because the school hit 100/100 credits on day 28. The principal is the economic owner; blocking them blocks the whole school. Teacher/incharge quotas still prevent runaway individual spend.

**Tradeoff:** A compromised principal account could generate without school-level brake. Mitigations: usage dashboard, operator metering, optional admin soft ceiling in Phase 1.5 if needed.

**Not in scope yet:** ~~Atomic credit ledger (TOCTOU)~~ — row-locked check + charge-time enforcement (2026-06-15). IST month boundary via `school.settings.timezone` (default `Asia/Kolkata`).

**Status:** Implemented in `ai_credits.py` + `metering.py`.

---

*This is a living record — update it as decisions are made or revisited.*
