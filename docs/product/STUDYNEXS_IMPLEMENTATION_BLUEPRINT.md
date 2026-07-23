# StudyNexs Implementation Blueprint

**Purpose:** Map the current repository and product coverage against the StudyNexs Product Blueprint.

This document is a companion to `STUDYNEXS_PRODUCT_BLUEPRINT.md`.

It is **not** release authorization. It does not assign Release 0.4 scope, create engineering tasks, estimate effort, or modify the roadmap. Candidate focus areas below are hypotheses only, pending pilot evidence and ARM authorization.

Baseline used for this map:

- Certified baseline: `v0.3.1`
- Certified pilot slice: Principal + Teacher
- Source of truth: current repository surface, Release 0.1–0.3 completion evidence, and Release 0.3.1 certification

---

## 1. Status Legend

| Status | Meaning |
|---|---|
| Already implemented | Exists in Release 0.3.1 and is materially usable or proven. |
| Partially implemented | API/UI/data path exists, but is incomplete, not fully certified, or not yet a smooth executive-demo journey. |
| Not implemented | Required for the full Product Blueprint, but no complete current workflow exists. |

Criticality labels:

| Label | Meaning |
|---|---|
| Demo Critical | Required to tell the complete executive demonstration story. |
| Pilot Critical | Required for a real pilot school to succeed without engineering assistance. |

---

## 2. Current Repository Coverage by Intelligence Domain

The percentages below are product-coverage estimates, not engineering effort estimates.

| Intelligence domain | Coverage | Current repository coverage |
|---|---:|---|
| Curriculum Intelligence | 100% | Curriculum source, draft extraction, HITL review, approval, KG, RAG, readiness, same-pack grounding. |
| Teaching Intelligence | 80% | Teacher hub, grounded lesson plans, grounded question papers, class/subject scoping. Learning materials are present but not yet a complete polished journey. |
| Assessment Authoring Intelligence | 80% | AI question papers, citations, review/approval surfaces, exam creation path. Needs stronger cohesive authoring-to-exam UX. |
| Principal Intelligence | 70% | Dashboard, Academic Intelligence Ready, grounding evidence, certified Principal walkthrough. Weekly operating rhythm is not complete. |
| Admissions Intelligence | 65% | Candidate pipeline, stages, document extraction, admission pages. Full admission-to-enrollment journey needs cohesion. |
| Student Records Intelligence | 65% | Student lists, profiles, guardians, class assignment. Longitudinal history and progression are partial. |
| Assessment Evaluation Intelligence | 80% | Answer-sheet upload, OCR/vision, grounded AI suggestions, HITL approval, marks propagation, recovery checks, browser evidence strip, and deterministic evidence ledger are runtime/browser proven. |
| Learning Intelligence | 60% | Gradebook, mastery, misconceptions, weak-topic updates, and assessment-to-mastery propagation are runtime-proven. Needs stronger school-facing learning narrative. |
| Student Intelligence | 50% | Student portal, tutor, recommendations, concept-card grounding. Not yet certified as the primary pilot journey. |
| Parent Intelligence | 45% | Parent portal, child summary, Parent Copilot briefing/ask, fees/notices. Needs teacher-controlled parent journey maturity. |
| School Operations Intelligence | 45% | Attendance, timetable, notices, events, transport, library, residential, fees, payroll, expenses exist in pieces. Needs unified operating story. |
| Staff Intelligence | 40% | Staff directory, onboarding, payroll, teacher mappings. Needs complete HR lifecycle. |
| Finance Intelligence | 35% | Fees, receipts, expenses, payroll, summary surfaces. Needs management-grade finance intelligence. |
| Alumni Intelligence | 10% | Foundations through student records only. Alumni lifecycle is not implemented. |

---

## 3. Expanded Capability Matrix

| Domain | Capability | Status | Demo Critical | Pilot Critical | Dependencies | Notes |
|---|---|---|---:|---:|---|---|
| Admissions | Candidate pipeline | Partially implemented | Yes | Medium | School ops, student records | Real surfaces exist; executive journey needs cohesion. |
| Admissions | Stage movement | Partially implemented | Yes | Medium | Admissions candidate model | Supports pipeline story but not yet a full polished intake workflow. |
| Admissions | Document extraction | Partially implemented | Medium | Medium | File upload, OCR/document extraction | Exists for document number extraction. |
| Admissions | Admission-to-student conversion | Partially implemented | Yes | High | Student records, guardians, class setup | Needed for full lifecycle story. |
| Admissions | AI admission readiness / fit summary | Not implemented | Medium | Low | Admissions data, policy rules | Vision capability, not required for certified v0.3.1 pilot. |
| Student Records | Student list/profile | Already implemented | Yes | High | Academic module | Core school identity surface. |
| Student Records | Guardian links | Partially implemented | Yes | High | Parent users, student profile | Needed for parent journey confidence. |
| Student Records | Class/section/year assignment | Already implemented | Yes | High | Academic year, classes | Foundation for all academic workflows. |
| Student Records | Longitudinal history | Partially implemented | Yes | Medium | Gradebook, mastery, report cards | Needed for full operating-system narrative. |
| Student Records | Promotion/graduation/alumni transition | Not implemented | Medium | Low | Academic years, student history | Required for admission-to-alumni story. |
| Curriculum | Curriculum source upload/paste | Already implemented | Yes | High | File upload, onboarding | Runtime-proven in Release 0.2 evidence. |
| Curriculum | AI extraction to draft CurriculumPack | Already implemented | Yes | High | LLM gateway, credits | Core product differentiator. |
| Curriculum | Teacher/HOD review | Already implemented | Yes | High | CurriculumPack, RBAC | Human-in-the-loop academic authority. |
| Curriculum | CurriculumPack approval | Already implemented | Yes | High | Pack readiness | Required before academic memory becomes authoritative. |
| Curriculum | KG spine generation | Already implemented | Yes | High | Knowledge graph | Part of Academic Intelligence Ready. |
| Curriculum | RAG indexing | Already implemented | Yes | High | Vector store | Part of downstream grounding. |
| Curriculum | Academic Intelligence Ready | Already implemented | Yes | High | Approved pack, KG, RAG | Certified leadership proof point. |
| Teaching | Teaching hub | Already implemented | Yes | High | Teacher auth/RBAC | Certified in browser walkthrough. |
| Teaching | Grounded lesson plans | Already implemented | Yes | High | Approved pack, RAG, LLM gateway | Certified same-pack grounding. |
| Teaching | Learning materials | Partially implemented | Yes | Medium | Lesson plan, pack grounding | Runtime evidence exists; full UX story needs completion. |
| Teaching | Class/subject scoping | Already implemented | Yes | High | Teacher mappings, RBAC | Certified for teacher pilot journey. |
| Teaching | Content review queue | Partially implemented | Medium | Medium | Concept cards, teacher approval | Supports HITL but not central v0.3.1 demo path. |
| Assessment Authoring | AI question paper generation | Already implemented | Yes | High | Approved pack, RAG, LLM gateway | Certified same-pack grounding. |
| Assessment Authoring | Question citations / grounding | Already implemented | Yes | High | RAG sources | Critical trust surface. |
| Assessment Authoring | Question paper review/approval | Partially implemented | Yes | High | Question paper lifecycle, teacher/HOD approval | Exists but needs smoother executive journey. |
| Assessment Authoring | Exam creation from question paper | Partially implemented | Yes | High | Exams module, question paper | Runtime path exists; browser story not fully certified. |
| Assessment Evaluation | Answer-sheet upload | Already implemented | Yes | High | Files, exam roster | Runtime/browser-proven in Assessment Evaluation Intelligence vertical. |
| Assessment Evaluation | OCR / vision extraction | Already implemented | Yes | High | Vision model, upload service | Runtime-proven through answer-sheet evaluation path. |
| Assessment Evaluation | AI scoring suggestions | Already implemented | Yes | High | Evaluation service, LLM gateway, RAG grounding | Suggestions preserve grounded citation evidence and remain teacher-reviewed. |
| Assessment Evaluation | Teacher HITL approval | Already implemented | Yes | High | Evaluation service, exam marks | Teacher approval records approving teacher and timestamp in the evidence ledger. |
| Assessment Evaluation | Marks saved to gradebook | Already implemented | Yes | High | Exams, gradebook, mastery | Runtime-proven through marks and mastery propagation. |
| Assessment Evaluation | Academic evidence ledger | Already implemented | Yes | High | CurriculumPack, QuestionPaper, Exam, AnswerSheet, Evaluation | Deterministically links tenant, pack, paper, exam, student, answer sheet, evaluation, approving teacher, timestamp, grounded status, and citations. |
| Learning | Gradebook | Partially implemented | Yes | High | Exam marks | Exists as a surface/path, needs stronger end-to-end clarity. |
| Learning | Mastery recomputation | Partially implemented | Yes | High | Marks, concepts, misconceptions | Runtime-proven for same academic loop. |
| Learning | Misconception tracking | Partially implemented | Yes | Medium | Evaluation details | Useful for tutor/parent/principal insight. |
| Learning | Class-level weak-topic summary | Partially implemented | Yes | Medium | Mastery, exam analytics | Needed for leadership/action narrative. |
| Student | Student portal | Partially implemented | Yes | Medium | Student account, portal context | Exists but not certified for pilot walkthrough. |
| Student | AI Tutor recommendations | Partially implemented | Yes | Medium | Mastery, concept cards | Runtime-proven but not yet full executive browser story. |
| Student | Concept-card grounded lesson | Partially implemented | Yes | Medium | Concept cards, tutor | Important trust mechanism. |
| Student | Personalized next activity | Partially implemented | Yes | Medium | Mastery, tutor content | Needs clearer user journey. |
| Parent | Parent portal | Partially implemented | Yes | Medium | Parent-child links | Exists but not certified as a pilot journey. |
| Parent | Child summary/progress | Partially implemented | Yes | Medium | Portal, mastery, fees/notices | Needs safe, clear parent narrative. |
| Parent | Parent Copilot briefing | Partially implemented | Yes | Medium | Mastery, approved pack, parent context | Runtime-proven for same-pack grounding. |
| Parent | Home support suggestions | Partially implemented | Yes | Medium | Parent Copilot, mastery gaps | Needs teacher-control clarity. |
| Principal | Principal dashboard | Already implemented | Yes | High | Dashboard services | Certified. |
| Principal | Academic readiness visibility | Already implemented | Yes | High | Curriculum intelligence status | Certified. |
| Principal | Grounding evidence visibility | Already implemented | Yes | High | KG/RAG sources | Certified. |
| Principal | Weekly operating rhythm | Partially implemented | Yes | Medium | Teacher activity, mastery, operations | Needed for long-term school use. |
| Operations | Attendance | Partially implemented | Medium | Medium | Academic classes, students | Exists but not central certified path. |
| Operations | Timetable | Partially implemented | Medium | Medium | Classes, teachers | Exists as a school-ops surface. |
| Operations | Notices | Partially implemented | Medium | Medium | Communications | Useful for parent/student/admin lifecycle. |
| Operations | Events | Partially implemented | Medium | Medium | School ops | v0.3.1 includes event-time certification fix. |
| Operations | Transport | Partially implemented | Medium | Medium | Students, routes | Exists but not full operations intelligence. |
| Operations | Library | Partially implemented | Medium | Low | Books, issues, returns | Exists; executive value lower than academic loop. |
| Operations | Residential / hostel | Partially implemented | Low | Low | Students, blocks | Exists as operations surface. |
| Staff | Staff directory | Partially implemented | Medium | Medium | Users/staff profiles | Needs complete HR lifecycle for full product story. |
| Staff | Staff onboarding | Partially implemented | Medium | Medium | User/staff profile creation | Exists in ops APIs. |
| Staff | Payroll | Partially implemented | Medium | Medium | Staff, finance | Exists but needs finance/HR clarity. |
| Finance | Fees | Partially implemented | Medium | Medium | Students, parents | Exists for school/parent surfaces. |
| Finance | Receipts | Partially implemented | Medium | Medium | Fee records | Exists. |
| Finance | Expenses | Partially implemented | Medium | Low | Vendors/uploads | Exists. |
| Finance | Management finance intelligence | Partially implemented | Yes | Medium | Fees, payroll, expenses | Needed for trustee-level operating story. |
| Alumni | Alumni records | Not implemented | Low | Low | Student history, graduation | Required for complete lifecycle, not for current pilot. |
| Alumni | Alumni outcomes / engagement | Not implemented | Low | Low | Alumni records | Future lifecycle capability. |

---

## 4. Missing Capabilities

These are gaps against the Product Blueprint, not approved tasks.

- Seamless admission-to-enrollment flow.
- Complete admin setup journey.
- Broader assessment UX polish beyond the proven evidence-chain review path.
- Student remediation journey visible end-to-end.
- Parent communication journey with explicit teacher control.
- Principal weekly operating rhythm.
- Management/trustee executive operating view.
- Alumni lifecycle.
- Unified operations intelligence across attendance, timetable, transport, library, events, notices, staff, finance, and academics.
- Management-grade finance intelligence.

---

## 5. Partial Capabilities That Need Completion

These capabilities exist but should be treated carefully in executive demonstrations until pilot evidence and ARM authorization clarify scope.

| Capability area | Current partial state | Completion signal |
|---|---|---|
| Admissions | Pipeline and stages exist, but not a seamless school intake journey. | Admin can take a candidate from inquiry to enrolled student without operational ambiguity. |
| Assessment evaluation | Runtime and browser proof now cover upload, OCR/vision, grounded AI suggestions, teacher approval, marks, mastery, and evidence ledger. | Wider UX polish and operational hardening can be considered only after ARM authorization. |
| Student Tutor | Recommendations and concept-card grounding exist. | Student can understand and complete a next learning activity tied to approved evidence. |
| Parent Copilot | Briefing/ask exists and same-pack grounding is proven. | Parent receives clear, safe guidance with teacher-control expectations visible. |
| Principal operating rhythm | Principal can see readiness and dashboard data. | Principal can run a weekly academic review from StudyNexs without manual report assembly. |
| Operations modules | Many modules exist separately. | Admin staff can run daily school operations through one understandable flow. |
| Finance | Fees/receipts/expenses/payroll exist in parts. | Management can understand financial position and actions without spreadsheet reconstruction. |
| Alumni | Only foundations through student records exist. | Graduated student history becomes a durable alumni record. |

---

## 6. Executive Demonstration Readiness by Domain

| Domain | Readiness | How to present today |
|---|---|---|
| Curriculum Intelligence | Strong | Safe to present as the center of the product. |
| Teaching Intelligence | Strong | Safe to present through Principal + Teacher flow. |
| Assessment Authoring | Strong / Medium | Safe to present question-paper generation; avoid overpromising full exam-cycle polish. |
| Principal Intelligence | Medium / Strong | Safe to present readiness and dashboard; frame weekly rhythm as emerging. |
| Assessment Evaluation | Strong / Medium | Safe to present as a traceable academic evidence chain; keep the live walkthrough focused on the proven teacher review path. |
| Learning Intelligence | Medium | Present as connected evidence chain, not a complete student-success product yet. |
| Student Intelligence | Medium | Show carefully if needed; not the primary certified pilot story. |
| Parent Intelligence | Medium | Show carefully if needed; emphasize teacher control and safe explanation. |
| Admissions Intelligence | Medium | Present as operational surface, not complete admissions intelligence. |
| School Operations Intelligence | Medium / Low | Present as breadth, not as the main value proof. |
| Staff Intelligence | Low / Medium | Present only if asked. |
| Finance Intelligence | Low / Medium | Present only as existing operations support, not executive-grade finance intelligence. |
| Alumni Intelligence | Low | Do not present as implemented. |

---

## 7. Candidate Vertical Build Order Hypotheses

This section is intentionally non-authorizing. It does not define release scope or approved tasks.

Recently completed vertical:

- Assessment Evaluation Intelligence
  - Completed the assessment-to-mastery evidence chain with deterministic provenance, teacher HITL approval, marks/mastery propagation, browser proof, and same-pack runtime verification.

Candidate focus areas pending pilot evidence and ARM authorization:

1. Learning Intelligence
   - Hypothesis: Once marks and mastery are trusted, students need a clearer next-learning experience.

2. Parent Intelligence
   - Hypothesis: Parent trust becomes valuable only after teacher-reviewed assessment evidence is reliable.

3. Principal Intelligence
   - Hypothesis: Principal weekly rhythm becomes compelling once enough academic signals exist across teacher, assessment, mastery, and intervention paths.

4. School Operations Intelligence
   - Hypothesis: Operational modules become more valuable when connected to the academic operating rhythm rather than shown as isolated ERP features.

5. Finance Intelligence
   - Hypothesis: Finance becomes leadership-critical after operational usage is real and schools ask for management-grade visibility.

6. Alumni Intelligence
   - Hypothesis: Alumni belongs after the student lifecycle and year-to-year progression are mature.

These are hypotheses only. They must be validated through pilot evidence, internal review, and explicit ARM authorization before becoming implementation scope.

---

## 8. Non-Authorization Rule

This document must not be treated as:

- Release 0.4 authorization;
- sprint scope;
- an implementation plan;
- an engineering task list;
- a roadmap change;
- a governance update.

Its job is to keep engineering aligned with the Product Blueprint while preserving ARM control over what becomes authorized work.
