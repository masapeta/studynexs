# Gate 1 — Educator Language Audit (Demo V1)

**Purpose:** Inventory customer-facing copy that reads as engineering, AI, or platform jargon — and recommend educator-safe alternatives **without implementing changes in this batch**.

**Scope:** Admin / teacher / parent / student surfaces in `apps/admin-web` that appear in Demo V1 walkthroughs. Marketing pages are noted but deferred (not pilot-blocking).

**Method:** Code review + alignment with `DEMO_V1_CUSTOMER_REVIEW.md` and Gate 1 UX review. Each row: location, current string, issue, recommended copy, priority, persona.

**Priority key**

| Priority | Meaning |
|----------|---------|
| **P0** | Principal/parent sees this in demo; erodes trust or requires presenter translation |
| **P1** | Teacher/HOD daily path; jargon slows adoption |
| **P2** | Secondary, settings, or power-user; fix after walkthrough |

**Implementation rule (Batch A):** Document only. Code changes deferred to a terminology batch after persona walkthrough confirms priority.

---

## Executive summary

| Category | P0 count | P1 count | P2 count |
|----------|----------|----------|----------|
| Curriculum & grounding | 8 | 4 | 3 |
| AI credits & metering | 5 | 6 | 2 |
| Copilot naming | 4 | 3 | 1 |
| Assessment / exams | 3 | 4 | 2 |
| Mastery & learning | 2 | 3 | 1 |
| Platform / engineering | 2 | 1 | 5 |
| Tutor & voice | 2 | 1 | 0 |
| Navigation & labels | 3 | 2 | 2 |

**Top themes to fix (recommended order after walkthrough):**

1. Replace **RAG / vectors / knowledge spine / institutional memory** with *approved syllabus* language.
2. Rename **Copilot** surfaces to role outcomes (*Teaching assistant*, *Parent weekly summary*) where product allows.
3. Replace **AI credits** with *monthly AI allowance* or *generation uses* with plain cost preview.
4. Hide **pack UUIDs** and raw status enums from principals; show book/class/subject + approval date.
5. Remove **Vision OCR / async grading** from subtitles; use *AI-suggested marks — you approve before publishing*.

---

## 1. Curriculum & grounding

| File | Current | Issue | Recommended | Pri | Persona |
|------|---------|-------|-------------|-----|---------|
| `teaching/curriculum/page.tsx` subtitle | "Build draft curriculum packs, approve for institutional memory, and manage the knowledge spine." | Triple jargon | "Set up your board syllabus once — every AI paper and lesson uses the approved version." | P0 | Principal |
| `teaching/curriculum/page.tsx` | "Curriculum pack" (label) | Acceptable if explained | "Syllabus (class × subject × year)" in headings; keep "pack" in help text only | P1 | HOD |
| `teaching/curriculum/page.tsx` | `${m.vector_count ?? 0} vectors indexed` | Meaningless to educators | "Ready for AI search: {n} topics indexed" or hide behind "Advanced" | P0 | Principal |
| `teaching/curriculum/page.tsx` | "Grounding preview" | Engineer term | "What AI will use from this syllabus" | P0 | Principal |
| `teaching/curriculum/page.tsx` | Audit events like `kg_spine_succeeded` | Raw event names | Map to "Syllabus structure saved", "Topics indexed" | P0 | Principal |
| `CurriculumGroundingBadge.tsx` | "Curriculum grounding" | Jargon | "Based on your approved syllabus" | P1 | Teacher |
| `CurriculumGroundingBadge.tsx` | "Grounded / Not grounded" | Binary tech speak | "Uses approved syllabus / Not linked to syllabus yet" | P1 | Teacher |
| `CurriculumGroundingBadge.tsx` | `Pack {uuid}…` | Exposes internal ID | "Class 10 · Mathematics · 2026–27" (resolve from API) | P0 | Principal |
| `teaching/ai-papers/page.tsx` | "With curriculum grounding, topics steer RAG retrieval from the approved pack." | RAG | "Questions are drawn from chapters in your approved syllabus." | P0 | Teacher |
| `teaching/ai-papers/page.tsx` | Label "Curriculum grounding" (toggle) | Jargon | "Use approved syllabus" | P1 | Teacher |
| `teaching/ai-papers/page.tsx` | "Curriculum pack" (select) | OK with context | "Syllabus source" | P2 | Teacher |
| `teaching/document-ingest/page.tsx` title | "Document Intelligence" | Product/engineering | "School documents" or "Upload teaching materials" | P1 | Teacher |
| `teaching/document-ingest/page.tsx` subtitle | "extend pack grounding for AI papers and lesson plans" | Jargon | "Add worksheets and notes so AI papers and lesson plans can reference them." | P1 | Teacher |
| `teaching/lesson-plans/page.tsx` | "Template + curriculum grounding" | Jargon | "Standard template from syllabus" | P1 | Teacher |
| `LessonPlanDocument.tsx` | Uses `CurriculumGroundingBadge` | Inherited jargon | Same as badge recommendations | P1 | Teacher |

---

## 2. AI credits & metering

| File | Current | Issue | Recommended | Pri | Persona |
|------|---------|-------|-------------|-----|---------|
| `teaching/ai-papers/page.tsx` | "AI credits are charged when you generate…" | "Credits" feels SaaS | "Each generation uses part of your school's monthly AI allowance (charged when you generate, not when you approve)." | P0 | Principal |
| `teaching/ai-papers/page.tsx` | "Not enough AI credits remaining this month." | OK-ish | "Your monthly AI allowance is used up. Ask your principal to review the plan." | P1 | Teacher |
| `teaching/ai-papers/page.tsx` confirm dialog | "This will use {n} AI credits." | Abstract | "This will use {n} of your monthly generations." | P1 | Teacher |
| `teaching/ai-papers/page.tsx` | "AI credits used for this paper: {n}" | Technical | "Generations used for this paper: {n}" | P2 | Teacher |
| `teaching/report-cards/page.tsx` | "AI Credits Remaining" banner | Jargon | "AI generations left this month" | P1 | Teacher |
| `teaching/mastery/page.tsx` | Same insufficient-credits message | Shared pattern | Align with allowance wording | P2 | Teacher |
| `(marketing)/pricing/page.tsx` | "100 AI credits / month" | Marketing | "100 AI generations / month" (pricing page — post-pilot) | P2 | Buyer |

---

## 3. Copilot naming

| File | Current | Issue | Recommended | Pri | Persona |
|------|---------|-------|-------------|-----|---------|
| `teaching/ai-papers/page.tsx` | "Teacher Copilot review" | "Copilot" over-used | "Quality check (AI suggestions)" | P1 | Teacher |
| `teaching/ai-papers/page.tsx` | "Not enough AI credits for Teacher Copilot review." | Double jargon | "Not enough allowance left for quality check." | P1 | Teacher |
| `teaching/lesson-plans/page.tsx` | "Teacher Copilot (AI credits)" mode | Jargon | "AI draft from syllabus" | P1 | Teacher |
| `teaching/lesson-plans/page.tsx` | "Select an approved curriculum pack for Teacher Copilot generation." | Jargon | "Choose the approved syllabus to generate from." | P1 | Teacher |
| `parent/child/[studentId]/page.tsx` | "Parent Copilot" | Brand vs outcome | "Weekly summary & ask a question" | P0 | Parent |
| `parent/page.tsx` | "Parent Copilot — weekly summary" | Same | "This week's summary" | P0 | Parent |
| `student/tutor/tutor-page.tsx` | "Ask Student Copilot" | Same | "Ask about this topic" | P1 | Student |

*Note:* Backend routes (`/parent-copilot/`) stay unchanged for API stability; UI labels only in terminology batch.

---

## 4. Assessment & exams

| File | Current | Issue | Recommended | Pri | Persona |
|------|---------|-------|-------------|-----|---------|
| `teaching/exams/.../evaluate/page.tsx` subtitle | "Vision OCR + async grading" (if present) | Engineer speak | "AI suggested marks — review and publish when ready." | P0 | Teacher |
| `teaching/exams/.../evaluate/page.tsx` title area | "Evaluate answer sheets" | OK | Keep; add subline on trust | P2 | Teacher |
| `MorningBriefing.tsx` quick link | "AI marking" | Vague | "Review suggested marks" | P1 | Principal |
| `MorningBriefing.tsx` | "QP" badge on incharge rows | Abbreviation | "Papers" | P1 | Incharge |
| `teaching/ai-papers/page.tsx` title | "AI Question Paper Generator" | AI-forward | "Question papers" + subtitle mentions AI assist | P1 | Teacher |
| `teaching/exams/corrections/page.tsx` | "misconceptions & weak-topic signals" | Clinical | "Common mistakes & topics to revisit" | P2 | Teacher |

---

## 5. Mastery & learning

| File | Current | Issue | Recommended | Pri | Persona |
|------|---------|-------|-------------|-----|---------|
| `teaching/mastery/page.tsx` title | "Topic Mastery — Weakness Flags" | Harsh + jargon | "Topics to revisit" | P1 | Teacher |
| `teaching/mastery/page.tsx` subtitle | "Raised by score rules, never by AI." | Good trust; "score rules" odd | "Based on exam marks only — nothing goes to parents without your approval." | P1 | Teacher |
| `parent/.../page.tsx` empty briefing | "mastery data from marked exams" | OK | "results from marked exams" | P2 | Parent |
| Marketing / product visual | "Topic mastery heatmap" | OK for marketing | Defer | P2 | — |

---

## 6. Tutor & voice

| File | Current | Issue | Recommended | Pri | Persona |
|------|---------|-------|-------------|-----|---------|
| `TutorLessonPlayer.tsx` | Was: uvicorn / 127.0.0.1 / edge-tts errors | Dev leakage | **Fixed in Batch A** — customer-safe copy | — | Student |
| `TutorLessonPlayer.tsx` | "Neerja" / "Microsoft Neural" in UI hint | Vendor detail | "Teacher voice" / "Read aloud" (Batch A partial fix) | P1 | Student |
| `api.ts` | `Could not check Neerja voice status` (internal throw) | Not user-facing if sanitized | Ensure never surfaces raw | P2 | — |

---

## 7. Navigation & dashboard

| File | Current | Issue | Recommended | Pri | Persona |
|------|---------|-------|-------------|-----|---------|
| `MorningBriefing.tsx` QUICK_LINKS | "AI papers" | OK short | "Question papers" | P1 | Principal |
| `MorningBriefing.tsx` | "AI marking" | Unclear | "Mark reviews" or "Suggested marks" | P1 | Principal |
| `nav-groups.ts` | Engineering (platform_operator only) | **Fixed Batch A** — hidden from principals | — | — | — |
| `permissions.ts` | Legacy route comments | Internal | No user impact | P2 | — |
| Principal dashboard KPI | Was: 0% when no rolls | Misleading | **Fixed Batch A** — "Not recorded yet" | — | — |

---

## 8. Platform / engineering (must not appear in customer demo)

| File | Current | Issue | Recommended | Pri | Persona |
|------|---------|-------|-------------|-----|---------|
| `dashboard/platform/engineering/page.tsx` | "LLM default", "Vector DB" | Correct for operators | Keep; ensure nav gate (Batch A) | P0 | Principal |
| `customer-errors.ts` | Sanitizes localhost/uvicorn | **Batch A** | — | — | — |
| `lib/api.ts` dev comments | 127.0.0.1 rationale | Dev-only comments OK | Never in UI strings | P2 | — |

---

## 9. Notice & audience labels

| File | Current | Issue | Recommended | Pri | Persona |
|------|---------|-------|-------------|-----|---------|
| `format.ts` `noticeAudienceLabel` | Maps to "Parents & Students" etc. | **Improved in dashboard batch** | Verify all enum values covered | P2 | Admin |
| Notices list | Raw audience enum | If any remain | Human labels only | P1 | Admin |

---

## 10. Consistency glossary (target state)

Use one term per concept across portals:

| Concept | Avoid | Prefer |
|---------|-------|--------|
| Approved syllabus per class/subject/year | Curriculum pack, pack ID, grounding | **Approved syllabus** (help: "Curriculum pack" in docs) |
| AI retrieval | RAG, vectors, indexed | **Ready for AI** / **topics indexed** |
| Monthly limit | AI credits | **AI generations** / **monthly allowance** |
| AI draft features | Copilot (unless brand decision) | **AI draft**, **suggested**, **for your review** |
| Marking workflow | OCR, async, Vision | **Suggested marks**, **you publish** |
| Weak areas | Weakness flags, mastery_pct in UI | **Topics to revisit**, **needs practice** |

---

## 11. Suggested implementation batches (post-walkthrough)

**Terminology Batch B (copy-only, no layout):**

- P0 strings in curriculum hub, parent copilot labels, evaluate subtitle.
- `CurriculumGroundingBadge` — syllabus line instead of UUID.
- Credits banner wording shared component (`sn-credits-banner`).

**Terminology Batch C:**

- P1 teacher flows (AI papers, lesson plans, mastery titles).
- Copilot rename policy (product decision: keep "Copilot" brand vs outcome labels).

**Do not change without walkthrough:**

- Nav structure, tab count, dashboard layout.
- New features (academic story widgets, approval queue on home).

---

## 12. Verification checklist (when terminology batch ships)

- [ ] Principal can read Curriculum page headline without presenter.
- [ ] No UUIDs visible on grounded artifacts in demo paths.
- [ ] No "RAG", "vector", "grounding", "institutional memory" in P0 surfaces.
- [ ] Parent/student errors never mention hosts, ports, or stack traces.
- [ ] Credits/allowance explained once consistently on generate confirm dialogs.

---

*Audit completed for Gate 1 Batch A. Implementation intentionally deferred per product direction.*
