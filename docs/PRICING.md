# StudyNexs — Pricing & Plans

> Owner: Avinash Reddy Masapeta (ARM) · Last updated: 2026-06-18  
> **Commercial packaging** — tiers, feature gates, AI credit pools, add-ons, and sales guidance.  
> Product vision: [PRODUCT.md](./PRODUCT.md) · Build status: [STATUS.md](./STATUS.md) · Pilot script: [PILOT_DISCOVERY.md](./PILOT_DISCOVERY.md)

> **Status:** Tier structure defined; **rupee prices not locked** — validate willingness-to-pay in pilot meetings before publishing final numbers. Subscription billing via Razorpay is planned, not built yet.

---

## Strategy (how the tiers work together)

| Plan | Role | Main purpose |
|------|------|--------------|
| **Free** | Demo / trial school | Create interest — let them experience QP quality |
| **Pro** | Small school / first paid pilot | Close small schools — exam starter |
| **Pro+** | Serious school adoption | **Main growth plan** — exam intelligence + parent value |
| **Enterprise** | Multi-branch / premium group | Protect custom / high-usage schools |

**Hard rule:** Do **not** make AI unlimited in any plan. Every generation attempt consumes credits (see [AI credit rules](#ai-credit-rules)).

**Sales recommendation (first 3–5 schools):** Don't push all four plans equally. Sell only:

1. **Free Demo** — controlled trial  
2. **Paid Pilot** — scoped Pro+ for one class + one subject  
3. **Pro+** — Exam Intelligence (main conversion target)  
4. **Enterprise Custom** — chains and premium groups only  

Publicly you can show Free / Pro / Pro+ / Enterprise. In conversation say:

> *"For your school, the right pilot is **Pro+ Exam Intelligence** for one class and one subject."*

That keeps the buying decision simple.

---

## Free

**Controlled trial — not a production plan.**

| Include | Limit |
|---------|-------|
| School admin accounts | 1 |
| Teacher accounts | 2 |
| Scope | 1 class + 1 subject |
| Curriculum | Sample pack only |
| AI question papers | 3 / month |
| Marking scheme | Basic |
| Teacher dashboard | Preview only |
| Answer-sheet evaluation | None, or max 5 sample sheets |
| WhatsApp | No |
| AI tutor | No |
| Finance | No |
| Parent communication | No |
| Export | Watermark / export limitation |

**Purpose:** Let the school see quality. Do **not** let them run the school on free.

---

## Pro — Exam Starter

**Best buyer:** School wants paper generation + teacher time saving; not ready for full AI operations.

| Include | Notes |
|---------|-------|
| 1 school, limited users | — |
| Teacher dashboard | Full (not preview) |
| Weekly timetable | — |
| Staff / school notices | — |
| Curriculum pack builder | — |
| Active curriculum packs | 3–5 |
| QP generation + marking scheme | HOD approval workflow |
| School-private question bank | — |
| Student progress by subject | Basic |
| Lesson plan AI | Limited |
| Answer-sheet evaluation | Add-on or small quota |
| Support | Email / chat |

**Example AI limits (not unlimited):**

| Pool | Limit |
|------|-------|
| Monthly AI credits | 50 |
| Full QP generations | 10 / month |
| Question / section regenerations | 30 / month |
| Answer-sheet evaluations | 20 trial quota |

---

## Pro+ — Exam Intelligence (main growth plan)

**Best buyer:** School wants measurable academic improvement, faster correction, and parent-facing value.

Everything in **Pro**, plus:

| Include | Notes |
|---------|-------|
| Answer-sheet evaluator | Full |
| Teacher HITL correction screen | — |
| Batch answer-sheet upload | — |
| Weak concept detection | — |
| Class / student progress analysis | — |
| AI lesson plan from weak concepts | — |
| AI worksheet / homework generation | — |
| Parent-ready student summary | — |
| WhatsApp fee / attendance / academic alerts | Charged separately or capped |
| Tutor review queue + mistake recovery tutor | — |
| Curriculum rollover wizard | — |
| Difficulty calibration from past exams | — |
| Inspection / compliance pack basics | — |
| Finance visibility basics | Fee dashboard + reminders (FC Phase 1) |
| Support | Priority |

**Example AI limits:**

| Pool | Limit |
|------|-------|
| Monthly AI credits | 250 |
| Full QP generations | 50 / month |
| Answer-sheet evaluations | 300 / month |
| Tutor / student-help interactions | 1,000 / month (pooled) |
| WhatsApp | Separate pack or cap |

---

## Enterprise

**Best buyer:** Management wants control, reporting, compliance, and multi-branch standardization.

Everything in **Pro+**, plus:

| Include | Notes |
|---------|-------|
| Multi-branch management | — |
| Custom roles and permissions | — |
| Custom curriculum packs per branch | — |
| Custom book / publisher mapping | — |
| Dedicated curriculum setup support | — |
| Advanced answer-sheet evaluation quotas | Negotiated |
| AI tutor at scale | — |
| School-private memory graph | — |
| Principal co-pilot | — |
| Management dashboard | — |
| Finance Command Center | Salary / expense / transport visibility |
| Advanced audit logs | — |
| SSO / custom login | — |
| API integrations | — |
| Custom reports + data retention rules | — |
| Dedicated success manager + SLA | — |
| AI credit pool | Negotiated (never unlimited) |

---

## Feature gate table

| Feature | Free | Pro | Pro+ | Enterprise |
|---------|------|-----|------|------------|
| QP generation | Limited (3/mo) | Yes | Yes | Yes |
| Marking scheme | Limited | Yes | Yes | Yes |
| HOD approval | No | Yes | Yes | Yes |
| Curriculum packs | Sample | Limited (3–5) | Full | Custom per branch |
| Answer-sheet evaluation | Sample only (≤5) | Add-on / low quota | Yes | High quota |
| Teacher dashboard | Preview | Yes | Yes | Advanced |
| Lesson plan AI | No | Limited | Yes | Advanced |
| Weak concept reports | No | Basic | Yes | Advanced |
| AI tutor | No | No / very limited | Yes | Custom scale |
| Parent communication | No | Basic notices | WhatsApp + summaries | Advanced |
| Finance | No | No / basic fees view | Fee reminders | Full Command Center |
| Multi-branch | No | No | No | Yes |
| Custom integrations | No | No | Limited | Yes |

Engineering should enforce these gates in `school.settings.plan` + `ai_budget` — see [STATUS.md](./STATUS.md) for what's built today (pilot defaults only).

---

## AI credit rules

**Credits charge at generation time**, not at approval. Rejected drafts still consume credits. Full policy: [PRODUCT.md §7.4–§7.5](./PRODUCT.md#75-question-level-intelligence).

| Action | Credits |
|--------|---------|
| Fresh full QP | 5 |
| Balanced from question bank / chapter test / remedial / mock | 2 |
| Previous paper variant (clone & edit) | 0 |
| Regenerate full paper | 4 |
| Regenerate section | 2 |
| Regenerate one question | 1 |
| Paper quality check | 1 |
| Marking scheme generation | 2 (or bundled) |
| Export / edit | 0 |
| Answer-sheet evaluation | 1–3 per sheet |
| Lesson plan | 1 |
| Student summary | 1 |
| Tutor interactions | Pooled / capped per plan |

Plan tiers set the **monthly credit pool** and per-feature caps — never "unlimited."

---

## Add-ons (keep separate so base pricing stays clean)

| Add-on | Purpose |
|--------|---------|
| **Extra AI credits** | Burst usage without plan upgrade |
| **Answer-sheet evaluation pack** | Pro schools needing more eval quota |
| **WhatsApp message pack** | Parent alerts beyond plan cap |
| **AI tutor pack** | Extra tutor interactions |
| **Finance Command Center** | Management finance snapshot (Pro+ includes basics; full module is upsell) |
| **Custom curriculum setup** | White-glove pack onboarding |
| **Smart workbook / textbook generation** | Learning Companion premium |

---

## Pilot packaging (what to actually sell now)

| Offer | What it is | Price |
|-------|------------|-------|
| **Free Demo** | 2-week quality trial — Free tier limits | ₹0 |
| **Paid Pilot** | Pro+ scoped to **1 class + 1 subject** for one term | Discounted; validate WTP |
| **Pro+ annual** | Full school after pilot proves value | TBD after 3–5 pilots |
| **Enterprise** | Custom quote only | Negotiated |

**Pilot discovery:** Use [PILOT_DISCOVERY.md](./PILOT_DISCOVERY.md) Q6 for willingness-to-pay. Record outcomes in `docs/pilot/<school>/`.

---

## Open items (before public pricing page)

- [ ] Rupee price per student / per school for Pro and Pro+
- [ ] Unit-economics benchmark (provider cost vs credit pools)
- [ ] Razorpay subscription SKUs
- [ ] Feature-gate enforcement in API (plan field on `school.settings`)
- [ ] Public pricing page on marketing site

---

## Related documents

| Document | Purpose |
|----------|---------|
| [PRODUCT.md](./PRODUCT.md) | Full product vision |
| [PRODUCT.md §14](./PRODUCT.md#14-finance-command-center-optional-module) | Finance Command Center (Enterprise upsell) |
| [PILOT_DISCOVERY.md](./PILOT_DISCOVERY.md) | Demo + WTP questions |
| [DECISION_LOG.md](./DECISION_LOG.md) | Pricing decisions history |
