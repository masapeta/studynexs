# StudyNexs AI Learning Loop Verification

**Audit date:** 2026-07-21  
**Method:** Source code trace, API surface map, pytest integration suites, live HTTP smoke on `reference` tenant  
**Not in scope:** UI polish, code style, architecture documents as primary evidence  

**Verification standard:** Features classified as **Complete** only if they work **and** participate in the end-to-end academic chain. Isolated features → **Partially Integrated**.

---

## 1. Executive Summary

StudyNexs has a **real, implemented Academic Intelligence foundation** — not a documentation scaffold. An approved **CurriculumPack** triggers knowledge-spine build and vector indexing; **RAG with citations** feeds question-paper generation, lesson plans (copilot mode), and copilots; the **assessment chain** (approved paper → exam → OCR eval → teacher approve → marks → mastery → tutor/parent) is wired in code with automated tests.

**However, the full loop is not reliably closed in demo/runtime without careful seed alignment and operator discipline.** Several capabilities work in isolation or degrade to templates/demo fallbacks. The platform **cannot yet honestly claim** the complete moat sentence:

> *"Upload curriculum → struggling student gets tutor recommendation → parent gets meaningful insights — without breaking the chain."*

**It can claim:** a **partially integrated** Academic Intelligence platform with a **strong assessment spine** and **real curriculum grounding** for generation — provided packs are approved, exams are topic-tagged, concept cards exist, and outbox/mastery runs.

| Maturity | Share of loop |
|----------|----------------|
| **Complete (integrated)** | CurriculumPack approve → RAG index; QP generate (with pack) → approve → bank; exam from paper → eval → approve → marks → mastery recompute |
| **Partially Integrated** | Tutor, student/parent copilot, lesson plans, report cards, parent portal insights |
| **Partial / scaffold** | Document ingest (sync, OCR env-dependent), KG (spine not full ontology), Bloom metadata (generation only), rubrics (derived from papers) |
| **Missing / not productized** | Student practice engine, revision plans, adaptive learning, scheduled weekly parent digest, report cards on parent portal |

**Runtime (reference tenant, 2026-07-21):**
- `smoke_demo_readiness.py`: **32/32 green** (principal paths, curriculum grounding indexed, approved QP, eval list)
- Focused pytest (parent copilot, tutor, mastery handler, approve pipeline, RAG, answer-sheet eval): **32/32 passed**
- Parent copilot briefing: **200 OK** via `localhost:8000` (deterministic/LLM hybrid summary)
- Student tutor recommendations: **200 OK** but includes **demo `fractions` lesson** when chain data thin
- **Broken in local setup:** `127.0.0.1:8000` parent login **500** (stale uvicorn vs Docker — known Windows issue; not product logic)

---

## 2. AI Capability Matrix

| Capability | Implemented | Integrated in loop | Maturity | Verified |
|------------|-------------|-------------------|----------|----------|
| Curriculum upload / ingest | Yes | Partial | Partial | Unit tests; sync ingest |
| CurriculumPack CRUD + approve | Yes | Yes | Complete | Tests + smoke |
| Knowledge graph | Yes (Postgres spine) | Partial | Partial | Tests |
| Embeddings + Qdrant | Yes | Yes | Complete* | Tests (*stub embed OK in dev) |
| RAG retrieve + citations | Yes | Yes | Complete | Tests + smoke grounding |
| Lesson plan generation | Yes | Weak | Partial | Template + copilot tests |
| AI question papers | Yes | Yes | Partially Integrated | Tests + smoke |
| Exam generation | Yes (= exam entity + schema from paper) | Yes | Partially Integrated | Tests |
| Rubrics | Derived from QP | Yes (eval) | Partial | Via eval tests |
| OCR + AI evaluation | Yes | Yes | Partially Integrated | Tests |
| Gradebook | Yes | Read-only | Complete | Indirect |
| Report cards | Yes | No (parent) | Partial | Partial tests |
| Topic mastery | Yes | Yes | Complete | Tests |
| AI tutor | Yes | Partial | Partially Integrated | Tests + runtime |
| Weak topics / gaps | Yes | Yes | Complete | Tests |
| Recommendations | Yes | Partial | Hybrid | Runtime shows demo fallback |
| Practice generation | No (student) | — | Missing | — |
| Revision plans | No | — | Missing | — |
| Learning analytics (portals) | Basic stats | Partial | Partial | Portal tests |
| Parent copilot | Yes | Partial | Partially Integrated | Tests + runtime |
| Weekly summary | Label only | No | Scaffold | On-demand briefing |
| Teacher copilot | Yes | Weak | Partial | Tests; feedback-draft no UI |
| Bloom / LO alignment | QP metadata | Partial | Partial | Schema + output guard |
| Concept mapping | QP approve → links | Yes | Partial | Tests |

---

## 3. Architecture Verification Matrix

| Capability | Pack | KG | RAG | Embed | Vector | LLM | Template | Rules | OCR | HITL | Status |
|------------|:----:|:--:|:---:|:-----:|:------:|:---:|:--------:|:-----:|:---:|:----:|--------|
| Pack approve + index | ✓ | ✓ | ✓ | ✓ | ✓ | — | — | — | — | ✓ | **Complete** |
| Document ingest | ✓ | — | ✓ | ✓ | ✓ | — | — | — | Partial | ✓ | **Partial** |
| Lesson plan (template) | Opt | — | Opt | — | — | — | ✓ | ✓ | — | ✓ | **Partial** |
| Lesson plan (copilot) | ✓ | — | ✓ | ✓ | ✓ | ✓ | — | — | — | ✓ | **Partially Integrated** |
| QP generate (grounded) | ✓ | — | ✓ | ✓ | ✓ | ✓ | — | Blueprint code | — | ✓ | **Partially Integrated** |
| QP from bank | ✓ | ✓ | — | — | — | — | — | — | — | ✓ | **Partially Integrated** |
| Exam + schema | ✓ | — | — | — | — | — | — | — | — | — | **Complete** |
| Answer-sheet eval | ✓ | — | Opt | — | — | ✓ | — | ✓ obj | ✓ | ✓ | **Partially Integrated** |
| Mastery compute | — | Opt | — | — | — | — | — | ✓ | — | ✓ flags | **Complete** |
| Tutor lesson | ✓ | ✓ | — | — | — | — | ✓ | ✓ | — | ✓ cards | **Partially Integrated** |
| Student copilot | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | — | — | — | **Partial** |
| Parent copilot | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ fallback | — | — | — | **Partially Integrated** |
| Report card remark | — | — | — | — | — | ✓ | — | ✓ grades | — | ✓ | **Partial** |

---

## 4. End-to-End Academic Flow (20-step walkthrough)

| Step | Action | Status | Notes |
|------|--------|--------|-------|
| 1 | Upload SSC Class 10 Maths curriculum | **Partially works** | Pack builder UI + draft CRUD; bulk upload via document ingest (approved pack only) |
| 2 | Approve CurriculumPack | **Works** | Triggers KG spine + RAG index + audit |
| 3 | Build knowledge graph | **Works** | Postgres `KgEdge` spine; not separate graph DB |
| 4 | Generate embeddings | **Works** | On approve + ingest; stub provider in dev |
| 5 | Verify vector store | **Works** | Qdrant/in-memory; tenant-scoped; smoke checks `grounding.source_count` |
| 6 | Generate lesson plan | **Partially works** | Template (no LLM) or copilot (pack + RAG + LLM) |
| 7 | Generate question paper | **Works** | Requires pack for grounding; credits at generation |
| 8 | Review question paper | **Works** | Edit + copilot review (suggestions not persisted) |
| 9 | Approve / publish paper | **Works** | Bank ingest + concept links |
| 10 | Student takes exam | **Works** | Exam entity; online/offline marks entry |
| 11 | Teacher uploads answer sheets | **Works** | Arq job (except testing inline) |
| 12 | OCR extracts answers | **Partially works** | Vision LLM; env/provider dependent |
| 13 | AI evaluates | **Works** | Objective deterministic; subjective LLM + rubric |
| 14 | Teacher reviews | **Works** | Approve required before marks publish |
| 15 | Marks saved | **Works** | `exam_marks` + outbox event |
| 16 | Gradebook updated | **Works** | Read aggregation |
| 17 | Report card generated | **Partially works** | Staff UI; LLM remark only; **not on parent portal** |
| 18 | Topic mastery updated | **Works** | If exam has topic/schema tags; outbox worker |
| 19 | Parent copilot reflects performance | **Partially works** | Live weak topics + briefing; **not** full report card; flag must be NOTIFIED |
| 20 | Student tutor recommends next topics | **Partially works** | Chain when data aligned; else **demo fractions** fallback |

**Chain break points (ordered by severity):**
1. Exam without `question_schema` / topic tags → mastery no-op  
2. Topic titles ≠ pack topic titles → KG weak concepts empty  
3. No approved ConceptCards → tutor uses static templates  
4. Mastery flags not approved/notified → parent sees no teacher narrative  
5. Report cards never surface to parent  
6. No student practice loop after recommendation  

---

## 5. Missing Components

- Student **practice / quiz** generation and submission loop  
- **Revision plans** and adaptive learning paths  
- **Scheduled** parent weekly digest (cron + aggregation)  
- Standalone **rubric generation** product surface  
- **Semantic cache** for RAG cost reduction  
- ConceptCard **vector indexing** (cards used for rerank, not embedded)  
- Pack **activation** flag beyond `APPROVED` + latest version  
- HTTP **RAG re-index** endpoint (service method exists)  
- Teacher copilot **feedback-draft** UI  
- Parent portal **report card** delivery  
- **Topic update API** (UI calls missing endpoint)  

---

## 6. Broken Integrations

| Integration | Symptom | Root cause (code) |
|-------------|---------|-------------------|
| Marks → mastery | "Marks did nothing" | Untagged exams skipped in `recompute_class_subject` |
| Mastery → KG weak concepts | Empty graph edges | Title string mismatch pack ↔ exam |
| Mastery → parent narrative | No teacher feedback in portal | Flags stuck in PENDING or APPROVED not NOTIFIED |
| QP → eval | Cannot evaluate | Exam missing `source_paper_id` or schema |
| Report cards → parent | Parent never sees RC | No portal endpoint / UI |
| Curriculum UI → API | Topic edit fails | Missing `PUT /topics/{id}` |
| Local dev parent login | 500 on 127.0.0.1 | Stale uvicorn vs Docker routing (ops) |

---

## 7. Stubbed / Degraded Components

- **Embedding stub provider** in dev/test  
- **QP LLM stub fallback** when provider unavailable  
- **Tutor demo `fractions` recommendation** when no weak data  
- **Parent copilot deterministic briefing** when LLM JSON empty (not when LLM hard-fails)  
- **Lesson plan template mode** — no LLM, optional light RAG  
- **Portal `PRODUCT_FEATURES`** — static roadmap teasers  
- **SSC blueprint** partially hardcoded in QP service (content-as-data tension)  

---

## 8. Runtime Verification Results

| Check | Result | When |
|-------|--------|------|
| `smoke_demo_readiness.py` | 32/32 OK | 2026-07-21 |
| pytest loop suite (6 modules) | 32/32 passed | 2026-07-21 |
| Curriculum grounding indexed | source_count > 0 | smoke |
| Approved QP seeded | yes | smoke |
| Eval list for demo exam | yes | smoke |
| Parent briefing HTTP | 200 + summary | localhost:8000 |
| Student tutor recs HTTP | 200 + 3 recs (incl. demo) | localhost:8000 |
| Full 20-step manual E2E | **Not verified** in this session | Requires scripted walkthrough |

---

## 9. Demo Readiness

**Ready for guided demo** of: Curriculum pack (Class 10 Maths), grounded QP, exam eval with HITL, principal dashboard ops, student tutor shell.

**Demo risks:**
- Parent copilot failed in customer review when API routing wrong — works on correct base URL with seeded mastery  
- Tutor may show generic fractions lesson — undermines "personalized" story  
- Curriculum page jargon (see GATE1_LANGUAGE_AUDIT.md)  
- Principal dashboard historically showed false attendance KPI (Batch A fix local/uncommitted)  

**Verdict:** **Demo-ready with presenter** · **Not demo-self-serve**

---

## 10. Pilot Readiness

**Pilot-ready for:** SMS + fees + attendance + grounded QP generation + answer-sheet assisted marking + mastery heatmap (with tagged exams) + staff report cards.

**Not pilot-ready for:** Parent AI insights as primary value prop, student adaptive practice, unattended parent weekly summaries, multi-school ops at scale without outbox/RAG/index monitoring.

---

## 11. Production Readiness

Production guardrails, tenant isolation, metering, and HITL patterns exist in code. **Academic Intelligence production readiness** additionally requires:

- Live LLM + Qdrant + embedding provider provisioned and monitored  
- Outbox worker proven in target environment  
- Concept card content ops for tutor quality  
- End-to-end pilot on real marks with topic alignment verified  
- Parent copilot LLM outage strategy (student copilot has no deterministic fallback)  

**Verdict:** **Platform ops partial production** · **Academic Intelligence loop not production-complete**

---

## 12. Final Answer — Is the moat real today?

### Can StudyNexs claim Curriculum Intelligence as competitive moat?

**Partially yes — as foundation, not as closed loop.**

**Why yes (evidence):**
- Approved packs are enforced for grounded generation (`ground_approved_pack` refuses empty context).  
- RAG pipeline is real: embed → Qdrant (tenant-scoped) → hybrid retrieve → citations in QP/copilot prompts.  
- Knowledge spine persists and links questions + student struggle edges.  
- Assessment chain closes marks → mastery → misconceptions with tests.  

**Why no (full moat sentence):**
- A school cannot **reliably** go from upload → tutor next lesson → parent insight **without manual alignment** (topic tags, concept cards, flag workflow, pack title match).  
- **Parent** does not receive report cards or scheduled intelligence — copilot is on-demand and fragile to LLM/config.  
- **Student practice** — the remediation close of the loop — is **not implemented**.  
- Several surfaces **work independently** (template lesson plans, copilot review suggestions, gradebook) without feeding back into curriculum compounding.  

### The decisive question

> *Can a school start with uploading its curriculum and end with an AI tutor recommending the next lesson to a struggling student, with the parent receiving meaningful insights—all without breaking the academic chain?*

**Answer: No — not yet reliably.**

**Where the chain breaks first (typical demo school):**
1. Tutor recommendations fall back to **demo content** instead of exam-derived weak concepts.  
2. Parent insights depend on **mastery flags being notified** — extra teacher steps not obvious in UI.  
3. **No practice** step after recommendation — loop stops at consumption, not improvement.  
4. **Report cards** don't complete the parent story.  

**What would make the moat real (minimum):**
1. Enforce topic tagging on all pilot exams (or auto-tag from paper schema).  
2. Align pack topic titles with exam schema at approve/import time.  
3. Seed/serve ConceptCards for weak concepts before tutor demo.  
4. Wire parent portal to approved report cards + notified flag narratives.  
5. Ship thin student practice (even 5 MCQs from bank on weak topic).  
6. Add smoke step: parent briefing + student recs must reference **live** weak topic from seeded eval, not fractions demo.  

---

*Audit performed against `develop` workspace. Implementation is source of truth; update this doc when chain integrations change.*
