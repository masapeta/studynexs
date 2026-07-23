# Pilot Closure Backlog — Academic Intelligence Loop

**Ordered by chain impact** (fix what breaks the loop first).  
**Source:** [`AI_LEARNING_LOOP_VERIFICATION.md`](./AI_LEARNING_LOOP_VERIFICATION.md) (2026-07-21).

Each item states: **what breaks**, **fix**, **effort**, **verification**.

---

## Tier 0 — Chain integrity (do before pilot narrative)

| # | Item | What breaks | Fix | Effort | Verify |
|---|------|-------------|-----|--------|--------|
| 0.1 | **Exam topic propagation** | Marks → mastery no-op | When exam created from approved paper, copy `question_schema` topics; block eval publish if schema empty | S | Exam with schema → recompute → mastery row |
| 0.2 | **Topic title alignment** | KG weak concepts empty | Normalize topic keys on pack approve + exam import (casefold/slug); validation warning in UI | M | Weak concept edge after eval approve |
| 0.3 | **Remove tutor demo fallback in pilot** | "Personalized" tutor shows fractions | Gate demo `fractions` lesson behind `ENVIRONMENT=development` or empty-state only | S | Tutor recs reference seeded weak topic |
| 0.4 | **Smoke: parent + student AI paths** | Demo fails silently on wrong host | Extend `smoke_demo_readiness.py`: parent login, briefing, student recs; assert no demo lesson key when mastery exists | S | 35+ checks green |
| 0.5 | **ConceptCard seed for demo weak topics** | Tutor has no grounded lesson | Seed approved ConceptCards for Class 10 Maths weak topics in reference school | M | Tutor lesson from card, not template |

---

## Tier 1 — Close the loop for parent + student

| # | Item | What breaks | Fix | Effort | Verify |
|---|------|-------------|-----|--------|--------|
| 1.1 | **Mastery flag → parent visibility** | Parent never sees teacher narrative | Auto-notify on flag approve (config) OR surface APPROVED flags in portal with clear UX | M | Parent portal shows feedback after approve |
| 1.2 | **Parent report card surface** | Report cards staff-only | `GET /portal/child/{id}/report-cards` + parent UI (approved only) | M | Parent sees issued RC PDF/list |
| 1.3 | **Student practice (thin slice)** | Loop stops at recommendation | 5-question MCQ from question bank on weak topic; no new module — reuse bank + mastery topic | L | Student completes practice → optional mastery refresh |
| 1.4 | **Parent copilot hard-fail fallback** | 500 when LLM down | Deterministic briefing/ask on gateway failure (parity with JSON-empty path) | S | Kill LLM → parent still gets summary |

---

## Tier 2 — Demo / pilot reliability

| # | Item | What breaks | Fix | Effort | Verify |
|---|------|-------------|-----|--------|--------|
| 2.1 | **Principal dashboard truth** | False 0% attendance | Ship Gate 1 Batch A (attendance state machine) | Done* | KPI "Not recorded yet" |
| 2.2 | **Curriculum topic update API** | UI edit fails | `PUT /curriculum/packs/{id}/topics/{topic_id}` | S | Edit topic in curriculum UI |
| 2.3 | **RAG re-index HTTP** | Ops can't recover failed index | Expose `POST /packs/{id}/retry-rag-index` (admin) | S | Retry after forced error |
| 2.4 | **Async document ingest** | Timeouts on large PDFs | Arq job + poll (pattern: answer-sheet eval) | M | Upload 20-page PDF without 504 |
| 2.5 | **127.0.0.1 vs localhost** | Parent login 500 on Windows | Document + smoke default; admin-web already uses 127.0.0.1 — align Docker publish or kill stale uvicorn | S | Both hosts work or single canonical |

*Batch A local; commit when approved.

---

## Tier 3 — Moat depth (post-pilot)

| # | Item | What breaks | Fix | Effort |
|---|------|-------------|-----|--------|
| 3.1 | Terminology Batch B | Principal trust / jargon | P0 strings from GATE1_LANGUAGE_AUDIT | M |
| 3.2 | Teacher copilot feedback UI | Feedback API unused | Wire `/copilot/feedback-draft` in eval UI | M |
| 3.3 | Weekly parent digest | "Weekly summary" is marketing | Scheduled job + notification (optional pilot) | L |
| 3.4 | ConceptCard vector index | Weaker RAG for cards | Embed approved cards into pack-scoped collection | L |
| 3.5 | Semantic cache | AI cost at scale | Per-tenant semantic cache on RAG queries | L |
| 3.6 | Blueprint as data | Hardcoded SSC sections | Move blueprint rules to pack/board data | L |

---

## Recommended pilot sequence (4 batches)

```
Batch P0 (1 week)  → 0.1, 0.2, 0.3, 0.4, 0.5, 2.1 commit
Batch P1 (1 week)  → 1.1, 1.4, 2.2, 2.3
Batch P2 (2 weeks) → 1.2, 1.3
Batch P3 (ongoing) → Tier 3 + terminology
```

---

## Definition: loop closed for pilot

Pilot can claim the Academic Intelligence Loop when **all** pass on `reference`:

1. Approved Class 10 Maths pack with indexed grounding (`source_count > 0`)
2. Approved QP → exam with topic schema
3. Eval approve → marks → mastery updated for weak topic
4. Tutor recommendation references **that** topic (not `fractions` demo)
5. Tutor lesson loads from **approved ConceptCard**
6. Parent briefing mentions weak topic + attendance (200, non-empty)
7. Optional: parent sees report card or notified flag narrative

---

*Update when items ship; link PRs in CHANGELOG.*
