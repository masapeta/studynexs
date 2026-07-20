# Gate 2 Pilot Success Criteria

> **Baseline:** `studynexs-dev` branch `develop` · Batch 1 frozen (reconciled architecture)  
> **Pilot:** Naagarjuna Talent School · Class 10 Mathematics  
> **Review:** End of Week 6 (or at pilot close) using [GATE2_EXIT_REVIEW_TEMPLATE.md](./GATE2_EXIT_REVIEW_TEMPLATE.md)

---

## 1. Primary outcome

**Gate 2 succeeds** if the school confirms the platform is **worth continuing** as a design partner for Class 10 Maths — measured by completion, confidence, stability, and feedback — not by feature count.

---

## 2. Must-pass criteria (all required)

| ID | Criterion | Measure | Target | Evidence source |
|----|-----------|---------|--------|-----------------|
| MP-1 | **Curriculum pack approved by HOD** | At least 1 pack in `approved` state reflecting school syllabus (or validated placeholder + HOD sign-off) | 1 pack | UI + audit trail |
| MP-2 | **Grounded QP cycle complete** | Generate → edit → approve with pack provenance visible | ≥1 paper / pilot | AI Papers + audit |
| MP-3 | **HITL enforced** | Zero marks or papers published without explicit teacher approve | 0 violations | Process audit + teacher attestation |
| MP-4 | **No cross-tenant data leak** | No report of another school's data in UI/API | 0 incidents | Ops log + spot checks |
| MP-5 | **Pilot stability** | No more than **2 Sev-2** outages (>30 min unusable) during intensive phase (Weeks 1–2) | ≤2 | Daily logs |
| MP-6 | **Smoke readiness** | `smoke_pilot_readiness.py` pass rate | ≥95% of scheduled pilot days | Env validation logs |
| MP-7 | **Feedback captured** | HOD + ≥1 teacher complete feedback template | 100% of designated roles | Feedback forms |

---

## 3. Should-pass criteria (≥4 of 6)

| ID | Criterion | Measure | Target |
|----|-----------|---------|--------|
| SP-1 | **Teacher time saved on QP** | Self-reported | ≥1 teacher rates "saves time" ≥4/5 |
| SP-2 | **Teacher trust in QP** | Self-reported after edits | ≥4/5 trust after HITL |
| SP-3 | **Eval assist rate** | On objective/short questions | ≥70% where sheets collected |
| SP-4 | **Weak-topic alignment** | Teacher agrees report matches judgment | ≥1 class test cycle |
| SP-5 | **Lesson plan provenance understood** | HOD/teacher can explain provenance badge | Qualitative pass in exit interview |
| SP-6 | **Daily ops discipline** | Daily logs filed | ≥80% of pilot days |

---

## 4. Capability-specific criteria (Batch 1)

| Capability | Success signal | Not required for Gate 2 pass |
|------------|----------------|------------------------------|
| Curriculum pack CRUD + approve | HOD completes without eng assist | PDF ingestion |
| RAG index on approve | Approve succeeds; LP/QP show pack | Sub-second index |
| Grounded lesson plan | Provenance visible; teacher edits segments | Full LLM-authored prose |
| Grounded question paper | Matches blueprint roughly; teacher edits | Perfect board replica |
| Eval | Assist on neat sheets; teacher overrides | Diagrams, Telugu essays, proof grading |
| Tutor | Demo completes for 1 student flow | Pack-grounded tutor |
| Parent portal | Demo login works | Production parent rollout |

---

## 5. Quantitative scorecard (fill at exit)

| Metric | Baseline | Week 2 | Week 4 | Week 6 | Target |
|--------|----------|--------|--------|--------|--------|
| Approved packs | | | | | ≥1 |
| Approved QPs | | | | | ≥2 |
| Answer sheets processed | | | | | ≥5 (stretch 10) |
| Teacher feedback avg (1–5) | | | | | ≥3.5 |
| HOD confidence (1–5) | | | | | ≥4 |
| P0/P1 open issues | | | | | Trend down |
| LLM spend (INR) | | | | | Within budget |

---

## 6. Explicit non-goals (do not fail pilot for these)

- Polished marketing UI / dashboard glass redesign
- Batch 2 eval pack alignment
- Pack-grounded tutor
- Multi-subject rollout
- Payment gateway
- Mobile native apps
- 100% automated grading

---

## 7. Decision matrix (exit)

| Result | Condition | Next step |
|--------|-----------|-----------|
| **Strong pass** | All MP + ≥5 SP | Propose commercial pilot extension + Batch 2 planning |
| **Pass** | All MP + ≥4 SP | Continue 8-week plan; address SP gaps |
| **Conditional pass** | All MP; SP 2–3 | 4-week remediation; re-review |
| **Fail** | Any MP missed | Pause; root-cause + [rollback](./GATE2_ROLLBACK_PLAN.md) if needed |

---

## 8. Sign-off

| Role | Pass / Conditional / Fail | Comments | Date |
|------|---------------------------|----------|------|
| Product owner | | | |
| HOD (school) | | | |
| Pilot lead | | | |
