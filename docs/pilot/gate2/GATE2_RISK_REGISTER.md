# Gate 2 Pilot Risk Register

> **Baseline:** `v0.1.0-batch1`  
> **Review cadence:** Weekly (Monday) + ad hoc on incidents  
> **Last updated:** 2026-07-20

**Legend:** L=Low M=Medium H=High C=Critical · P=Probability I=Impact

---

## Active risks

| ID | Risk | Cat | P | I | Score | Owner | Mitigation | Status |
|----|------|-----|---|---|-------|-------|------------|--------|
| R-01 | **API image missing `[rag]`** — pack approve / grounded AI 500 | Tech | M | H | H | Eng | Dockerfile `.[ai,rag,observability]`; import check in env validation | Open |
| R-02 | **Ghost listener on 127.0.0.1:8000** — login 500 | Env | M | H | H | Eng | Force `NEXT_PUBLIC_API_URL=http://localhost:8000`; document in runbooks | Open |
| R-03 | **LLM timeout / quota** during live QP demo | Tech | M | M | M | Eng | Pre-approve backup QP; narrate wait; credit monitoring | Open |
| R-04 | **School syllabus incomplete** — pack not representative | Product | M | M | M | PO/HOD | Placeholder seed; weekly chapter validation | Open |
| R-05 | **Teacher expects full LLM lesson plans** — disappointment | Expectation | M | M | M | PO | Demo script wording; provenance not prose | Open |
| R-06 | **Eval over-promised** — diagrams/Telugu/proofs | Expectation | M | H | H | PO | CLASS_10_MATHS eval limits one-pager; HITL messaging | Open |
| R-07 | **Handwriting OCR poor** on real sheets | Product | H | M | H | Eng | Teacher override; collect 10-sheet tuning set | Open |
| R-08 | **Cross-tenant leak** | Security | L | C | H | Eng | Tenant slug header; smoke tests; Sev-1 rollback | Open |
| R-09 | **No production backups** — data loss on failure | Ops | M | H | H | Eng | Snapshot before pilot; document restore gap | Open |
| R-10 | **Qdrant down** — approve fails | Tech | L | H | M | Eng | Health check T-0; block approve until restored | Open |
| R-11 | **Copyright — textbook PDF upload** | Legal | L | C | H | PO | Structured maps only; HOD briefing | Open |
| R-12 | **Teacher skips pack selection** — ungrounded AI | Product | M | M | M | Pilot lead | Training; UI defaults where safe | Open |
| R-13 | **School network blocks API** | Ops | M | H | H | Ops | Hotspot; pre-download screenshots; offline script | Open |
| R-14 | **Pilot code drift** — unapproved changes during pilot | Process | M | M | M | PO | Freeze tag; fixes need evidence + log | Open |
| R-15 | **CI does not install `[rag]`** — regressions undetected | Tech | M | M | M | Eng | Add rag to CI install (post-pilot recommendation) | Open |
| R-16 | **Migration chain gap** on fresh DB | Tech | M | H | H | Eng | `alembic upgrade head` or schema patch before seed | Open |
| R-17 | **Demo password exposure** | Security | M | M | M | Ops | Rotate post-pilot; secure channel delivery | Open |
| R-18 | **Single engineer bus factor** | Ops | M | M | M | PO | On-call roster; runbooks in gate2 package | Open |

---

## Risk categories

| Category | Description |
|----------|-------------|
| Tech | Software, infra, dependencies |
| Env | Local/staging/prod configuration |
| Product | Feature gaps vs school needs |
| Expectation | Messaging / training gaps |
| Security | Auth, tenant isolation, data |
| Legal | Copyright, DPDP, consent |
| Ops | Network, support, backups |
| Process | Governance, scope creep |

---

## Escalation thresholds

| Severity | Definition | Action |
|----------|------------|--------|
| **Sev-1** | Cross-tenant leak; credential breach; widespread data corruption | Immediate rollback; notify PO + school within 1 h |
| **Sev-2** | Core wedge unusable >30 min (login, QP, approve) | On-call eng; workaround or rollback |
| **Sev-3** | Degraded (slow LLM, single user issue) | Log in feedback; fix next window |
| **Sev-4** | Cosmetic / doc | Backlog |

---

## Closed / accepted risks

| ID | Risk | Resolution |
|----|------|------------|
| — | Tutor not pack-grounded | Accepted — Batch 2; set expectations |
| — | Eval not LO-aligned | Accepted — Batch 2; HITL only |
| — | Manual pack entry | Accepted — seed + HOD entry |

---

## Weekly review log

| Week | Reviewer | New risks | Closed | Actions |
|------|----------|-----------|--------|---------|
| | | | | |

Update mitigations in [PILOT_FEEDBACK_LOG.md](../../product/PILOT_FEEDBACK_LOG.md) when incidents occur.
