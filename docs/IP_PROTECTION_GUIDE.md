# StudyNexs — Intellectual Property (IP) Protection Guide

> Owner: Avinash Reddy Masapeta (ARM)  
> Product: StudyNexs / Academix Platform  
> Jurisdiction focus: **India** (with notes for international expansion)  
> Last updated: 2026-06-26  

**Disclaimer:** This document is operational guidance for founders and engineers. It is **not legal advice**. Engage a qualified IP lawyer and company secretary before filings, contracts, or investor diligence.

---

## Table of contents

1. [What IP means for StudyNexs](#1-what-ip-means-for-studynexs)
2. [IP inventory — what you actually own](#2-ip-inventory--what-you-actually-own)
3. [Step-by-step protection roadmap](#3-step-by-step-protection-roadmap)
4. [Copyright](#4-copyright)
5. [Trademark & brand](#5-trademark--brand)
6. [Trade secrets](#6-trade-secrets)
7. [Patents](#7-patents)
8. [Contracts & ownership](#8-contracts--ownership)
9. [Open-source & dependency compliance](#9-open-source--dependency-compliance)
10. [Edtech-specific IP risks (content)](#10-edtech-specific-ip-risks-content)
11. [GitHub & repository hygiene](#11-github--repository-hygiene)
12. [Customer & school agreements](#12-customer--school-agreements)
13. [Investor / acquirer due diligence checklist](#13-investor--acquirer-due-diligence-checklist)
14. [Cost & timeline estimates (India)](#14-cost--timeline-estimates-india)
15. [Action checklist (printable)](#15-action-checklist-printable)

---

## 1. What IP means for StudyNexs

StudyNexs is a **commercial SaaS product** — not open source. IP protection ensures:

| Goal | Why it matters |
|------|----------------|
| **You own the code** | Founders, employees, and contractors cannot claim the platform |
| **Schools license use** | You grant access; you do not give away the product |
| **Brand is defensible** | Competitors cannot trade on “StudyNexs” confusion |
| **Investors trust clean cap table** | IP sits in the company, not individuals |
| **Content risk is managed** | You don’t infringe publisher/NCERT copyrights |

**Current repo state (as of push to GitHub):**

- README states: *Proprietary — © 2026 StudyNexs. All rights reserved.*
- **`LICENSE` file** at repo root — proprietary, all rights reserved
- GitHub repo: `https://github.com/masapeta/academix-platform` — prefer **Private** until legal pack is complete

---

## 2. IP inventory — what you actually own

### 2.1 Copyright (automatic, but document it)

| Asset | Examples in this repo | Owner should be |
|-------|----------------------|-----------------|
| **Source code** | `apps/api/`, `apps/admin-web/` | StudyNexs legal entity (Pvt Ltd) |
| **Database schemas** | Alembic migrations, SQLAlchemy models | Company |
| **UI/UX** | Next.js pages, CSS, components | Company |
| **Documentation** | `docs/PRODUCT.md`, API docs, runbooks | Company |
| **Marketing copy** | `(marketing)/` pages, pricing | Company |
| **AI prompts & rubrics** | Gateway prompts, eval rubrics, SSC blueprints | Company (trade secret + copyright) |
| **Grafana dashboards** | `infra/observability/grafana/` | Company |

### 2.2 Trademark

| Asset | Status to secure |
|-------|------------------|
| **StudyNexs** word mark | File in India (Class 42 software, Class 41 education) |
| **Logo** | Device mark filing |
| **Domain** | `studynexs.com`, `studynexs.in` — register early |
| **Taglines** | Only if used consistently in marketing |

### 2.3 Trade secrets (do not publish)

- LLM system prompts and evaluation logic
- AI credit pricing and unit economics
- Customer pipeline and pilot terms
- Unreleased roadmap and pricing floors
- Security architecture details

### 2.4 What you do **not** own

| Item | Notes |
|------|-------|
| **NCERT / publisher textbook text** | Expression is copyrighted — store structure only ([PRODUCT.md](./PRODUCT.md) §4) |
| **Open-source libraries** | MIT/Apache/etc. — you have a **license to use**, not own |
| **Third-party APIs** | OpenAI, Ollama, Azure, Razorpay — governed by their ToS |
| **School-uploaded content** | School warrants they have rights; you hold a **license** via contract |

---

## 3. Step-by-step protection roadmap

**Order matters.** Do not file trademarks before fixing ownership.

```
Phase 1 (Week 1–2)     → Entity + founder/contractor IP assignment
Phase 2 (Week 2–4)     → LICENSE file + school SaaS agreement template + Privacy Policy
Phase 3 (Week 3–6)     → Trademark application (StudyNexs + logo)
Phase 4 (Week 4–8)     → Copyright registration (software + literary work)
Phase 5 (Ongoing)      → OSS audit, secret hygiene, employee onboarding pack
Phase 6 (Optional)     → Patent consultation if novel technical invention identified
```

---

## 4. Copyright

### 4.1 How it works in India

- Copyright exists **automatically** when you create original work.
- **Registration** (Copyright Office, India) is optional but strengthens disputes and investor diligence.
- Software is registered as **literary work** (source code excerpts + manual).

### 4.2 What to register

1. **StudyNexs Platform** — representative source files + description of modules
2. **Product documentation** — `PRODUCT.md` summary + architecture (optional bundle)

### 4.3 Practical steps

1. Incorporate company (if not done): e.g. **StudyNexs Technologies Pvt Ltd**
2. Ensure **all authors assign** rights to company (see §8)
3. Prepare application via IP attorney or online filing:
   - Title of work
   - Author(s) + year of creation
   - NOC from author to company (if author ≠ company)
   - Source code extract (first/last 25 pages or MD5-hashed tarball per counsel advice)
4. Keep **version tags** in git (`v0.1.0-pilot`, etc.) as creation timeline evidence

### 4.4 Code headers (optional but useful)

Add to key files:

```text
Copyright (c) 2026 StudyNexs Technologies Pvt Ltd. All rights reserved.
Proprietary and confidential. Unauthorized copying or distribution is prohibited.
```

Do not over-clutter every file — `LICENSE` at root + employment contracts are enough for most startups.

### 4.5 Root `LICENSE` file (recommended text)

Create `/LICENSE` in repo:

```text
Copyright (c) 2026 StudyNexs Technologies Pvt Ltd. All rights reserved.

This software and associated documentation files (the "Software") are proprietary
and confidential. No part of the Software may be copied, modified, merged, published,
distributed, sublicensed, sold, or used to create derivative works without express
written permission from the copyright holder.

THE SOFTWARE IS PROVIDED FOR INTERNAL AND LICENSED CUSTOMER USE ONLY.
```

---

## 5. Trademark & brand

### 5.1 Why trademark ≠ domain

| | Trademark | Domain |
|--|-----------|--------|
| **Protects** | Brand name/logo in commerce | URL only |
| **Register with** | IP India | Registrar (GoDaddy, etc.) |
| **Stops** | Similar names in same class | Only exact domain squatting |

**You need both.**

### 5.2 Recommended filings (India)

| Mark | Class | Goods/Services |
|------|-------|----------------|
| **STUDYNEXS** (word) | **42** | Software as a service, platform |
| **STUDYNEXS** (word) | **41** | Education services, school management |
| **Logo** (device) | 42 + 41 | Same |

### 5.3 Process overview

1. **Trademark search** — check conflicts (TM agent, ~₹2k–5k)
2. **File application** — Form TM-A, applicant = company
3. **Examination** — 6–18+ months; respond to objections if any
4. **Use ™ immediately** after filing; **®** only after registration

### 5.4 Domains & handles

Register and park:

- `studynexs.com` (primary)
- `studynexs.in` (India trust)
- Social: LinkedIn, X, YouTube — consistent naming

### 5.5 Subdomain model (product IP separate from brand)

School tenants: `{slug}.studynexs.com` — document in school contract that subdomain is **licensed**, not owned by school.

---

## 6. Trade secrets

### 6.1 What to classify as confidential

| Category | Examples |
|----------|----------|
| **AI** | Prompts, rubric templates, fallback routing, credit formulas |
| **Business** | Pilot pricing, school pipeline, unit economics |
| **Security** | Architecture, incident playbooks, pen-test results |
| **Operations** | On-call, backup keys location (not the keys themselves) |

### 6.2 Controls

- Mark docs: `CONFIDENTIAL — StudyNexs Internal`
- NDA before sharing deck with schools/investors
- Never commit: `.env`, API keys, `seed_credentials.json` (already gitignored)
- Rotate keys if ever exposed (see `CODE_REVIEW.md` C1)
- Limit GitHub collaborators; use **private repo**

### 6.3 Employee / contractor onboarding

Every person with repo access signs:

1. **IP Assignment Agreement** — all work product belongs to company
2. **Confidentiality (NDA)**
3. **Conflict of interest** disclosure

---

## 7. Patents

### 7.1 When patents matter for StudyNexs

Patents protect **novel technical inventions**, not “school ERP with AI.”

**Probably not patentable (common features):**

- Attendance, fees, timetable CRUD
- Generic “AI generates question paper”
- Multi-tenant `school_id` filtering

**Maybe worth a consultation:**

- Unique **CurriculumPack cross-year concept lineage** algorithm (if novel vs prior art)
- Specific **HITL exam evaluation pipeline** with defined technical method
- **Institutional memory** architecture with auditable purpose tags (if implemented as novel system)

### 7.2 Recommendation

**Defer patents** until Phase 2 unless attorney identifies clear claim after prior-art search. Prioritize **copyright + trademark + contracts** first.

### 7.3 If filing later

- India: Indian Patent Office (provisional → complete specification within 12 months)
- PCT for international if expanding US/UAE
- Budget: **₹2L–₹10L+** with attorney over 2–3 years

---

## 8. Contracts & ownership

### 8.1 Founder agreement (Day 0)

Must include:

- All past and future IP on StudyNexs assigned to **company**
- Vesting schedule (standard 4-year, 1-year cliff if co-founders)
- Who owns what if someone leaves

### 8.2 Employee agreement (India)

Standard clauses:

- **Assignment of inventions** — even ideas conceived during employment
- **Work made for hire** — code written on company time/equipment
- **Return of materials** on exit
- **Non-solicit** (reasonable, counsel-drafted — not overbroad non-compete)

### 8.3 Contractor / freelancer agreement

**Critical:** If a developer built features without a signed contract, **you may not own that code**. Fix retroactively with:

- IP assignment deed
- List of deliverables / repo commits covered

### 8.4 Git as evidence

- Commits under company email / GitHub org account
- `masapeta/academix-platform` — transfer repo to **company GitHub org** when entity exists

---

## 9. Open-source & dependency compliance

### 9.1 Your stack uses OSS

| Component | License (typical) | Risk |
|-----------|-------------------|------|
| FastAPI, SQLAlchemy | MIT | Low |
| Next.js, React | MIT | Low |
| PostgreSQL | PostgreSQL License | Low |
| **GPL/AGPL deps** | Copyleft | **High** — audit required |

### 9.2 Actions

1. Run license scan: `pip-licenses`, `license-checker` (npm)
2. Maintain `THIRD_PARTY_NOTICES.md` in repo
3. **Block AGPL** in production dependencies without legal review
4. Document OSS in school contract (“includes open-source components under their licenses”)

---

## 10. Edtech-specific IP risks (content)

### 10.1 The rule (from PRODUCT.md)

> **StudyNexs does not copy textbooks.** It stores **structure** (chapters, topics, concepts) and generates **original** school-approved content.

### 10.2 Indian copyright (practical)

- Copyright protects **expression**, not ideas
- Storing full NCERT/publisher PDFs in RAG = **high risk**
- Teacher uploading scanned worksheets → school must warrant rights in **SaaS agreement**

### 10.3 CurriculumPack IP model

| Layer | Who owns | Notes |
|-------|----------|-------|
| **Platform code** | StudyNexs | Always |
| **School-approved pack content** | School licenses to you for service delivery | Define in contract |
| **AI-generated drafts** | Policy: school owns approved outputs OR joint — **define explicitly** |
| **Student data** | School is data fiduciary; you are processor under DPDP | Privacy Policy + DPA |

### 10.4 AI output clause (school contract)

Suggested principle:

- AI drafts are **assistive** until teacher/admin **approves**
- Approved content becomes **school instructional material**
- Platform retains right to improve models using **anonymized aggregates only** if consented

---

## 11. GitHub & repository hygiene

### 11.1 Before / after push checklist

| Check | Status |
|-------|--------|
| `.env` in `.gitignore` | ✅ |
| `apps/api/.env` never committed | Verify: `git log -p -- apps/api/.env` |
| OpenAI/Ollama keys rotated if ever leaked | See CODE_REVIEW C1 |
| Repo visibility | **Private** recommended |
| `LICENSE` file added | ✅ Done |
| No secrets in `CODE_REVIEW.md` snippets | Redact if publishing docs |
| GitHub org under company name | ⬜ When incorporated |

### 11.2 Secret scanning

- Enable GitHub **secret scanning** (private repos on paid plans)
- Add **gitleaks** pre-commit hook
- Never paste live keys in issues, PRs, or Cursor chats

### 11.3 Contributor License Agreement (CLA)

If accepting external contributions later:

- CLA assigning IP to company, or
- Policy: **no external contributions** (solo product) — simpler for now

---

## 12. Customer & school agreements

Minimum legal pack before paid pilot with real student data:

| Document | Purpose |
|----------|---------|
| **Master SaaS Agreement** | License grant, term, termination, liability cap |
| **Data Processing Agreement (DPA)** | DPDP Act 2023 — school = fiduciary, you = processor |
| **Privacy Policy** | Parent-facing, purpose limitation, retention |
| **Acceptable Use Policy** | AI usage, upload rules, no abuse |
| **SLA** (optional pilot) | Uptime targets, support hours |
| **Order Form** | Per-school pricing, modules enabled |

### 12.1 Key IP clauses in SaaS agreement

1. **License, not sale** — non-exclusive, non-transferable, revocable
2. **Reservation of rights** — all IP in platform stays with StudyNexs
3. **School data ownership** — school owns student/staff data
4. **Feedback license** — you may use anonymized feedback to improve product
5. **No reverse engineering**
6. **Termination** — data export window, then deletion per retention policy

---

## 13. Investor / acquirer due diligence checklist

Prepare a **Data Room** folder:

```
/ip/
  ├── COMPANY_INCORPORATION.pdf
  ├── FOUNDER_IP_ASSIGNMENT.pdf
  ├── EMPLOYEE_CONTRACTOR_IP_LIST.xlsx
  ├── TRADEMARK_APPLICATION_RECEIPT.pdf
  ├── COPYRIGHT_REGISTRATION.pdf (when available)
  ├── LICENSE (repo root)
  └── THIRD_PARTY_NOTICES.md
/contracts/
  ├── TEMPLATE_MSA.docx
  ├── TEMPLATE_DPA.docx
  └── PILOT_SCHOOL_SIGNED/ (redacted)
/tech/
  ├── ARCHITECTURE.pdf (from PRODUCT.md §15)
  ├── OSS_LICENSE_REPORT.pdf
  └── SECURITY_SUMMARY.pdf (no secrets)
```

Investors will ask:

- “Does the company own all code?” → Founder + contractor assignments
- “Any GPL contamination?” → OSS audit
- “Trademark conflicts?” → Search report
- “Content copyright risk?” → CurriculumPack policy + no textbook warehouse

---

## 14. Cost & timeline estimates (India)

| Item | Approx. cost (INR) | Timeline |
|------|-------------------|----------|
| Pvt Ltd incorporation | ₹15k–₹40k | 2–4 weeks |
| Founder + template employment IP docs | ₹25k–₹75k (lawyer) | 1–2 weeks |
| Trademark (1 class, word mark) | ₹8k–₹15k govt + agent | 12–24 months to register |
| Trademark (logo, extra class) | +₹8k–₹15k per class | Same |
| Copyright (software) | ₹5k–₹15k | 3–6 months certificate |
| Patent provisional (optional) | ₹50k–₹2L+ | 12-month priority window |
| Domain `.com` + `.in` | ₹1k–₹3k/year | Immediate |

**Bootstrap total (essentials):** ~₹75k–₹2L for entity + trademark + copyright + templates.

---

## 15. Action checklist (printable)

### Immediate (this week)

- [ ] Confirm company entity name matches brand (StudyNexs Technologies Pvt Ltd)
- [x] Add `LICENSE` file to repo root
- [ ] Set GitHub repo to **Private** (if public, assess exposure)
- [ ] Rotate any API keys ever in `.env` on disk or review context
- [ ] Signed IP assignment for all code authors (including yourself → company)

### Short term (this month)

- [ ] File trademark: STUDYNEXS (Class 42 + 41)
- [ ] Register `studynexs.com` / `studynexs.in` if not owned
- [ ] Draft Privacy Policy + school SaaS template (lawyer review)
- [ ] Run OSS license audit → `THIRD_PARTY_NOTICES.md`
- [ ] Move repo to company GitHub organization

### Before first paid school / real PII

- [ ] Signed MSA + DPA with pilot school
- [ ] DPDP consent flows implemented in product (see PRODUCT.md §14)
- [ ] Copyright registration filed
- [ ] Data retention + deletion policy documented

### Ongoing

- [ ] Annual trademark renewal monitoring
- [ ] Review new dependencies for copyleft licenses
- [ ] Update IP assignment for every new hire/contractor **before** they commit code

---

## Related internal documents

- [PRODUCT.md](./PRODUCT.md) — product definition, content/copyright stance
- [STATUS.md](./STATUS.md) — what is built today
- [WAR_ROOM_REVIEW.md](./WAR_ROOM_REVIEW.md) — full product/engineering diligence
- [CODE_REVIEW.md](../CODE_REVIEW.md) — security findings (rotate keys per C1)

---

*Document owner: ARM · Review annually or before fundraising / first paid contract.*
