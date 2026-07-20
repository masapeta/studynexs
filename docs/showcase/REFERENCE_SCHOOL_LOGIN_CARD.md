# Reference School Login Card

**StudyNexs Reference School** · **ARM International School**

Give this card to prospects so they can log in and explore the full platform.

---

## Access

| Setting | Value |
|---------|-------|
| **Tenant slug** | `reference` |
| **Display name** | ARM International School |
| **Admin web** | Set `NEXT_PUBLIC_TENANT_SLUG=reference` in `apps/admin-web/.env.local` |
| **Password (all accounts)** | `Demo@1234` |

---

## Accounts

| Role | Username | What to show |
|------|----------|--------------|
| **Principal** | `principal` | Dashboard — school health, attendance, fees, insights |
| **Class 10 incharge** | `teacher1` | Curriculum pack approvals |
| **Maths teacher** | `teacher6` | Teaching hub — AI papers, exams, lesson plans, gradebook |
| **Parent** | `parent_demo` | Parent portal — child attendance, fees, AI copilot |
| **Student** | `student_demo` | Student portal — tutor, exams, attendance |

---

## Seed (operators)

```powershell
cd D:\Projects\studynexs-platform\studynexs-dev\apps\api
python scripts/seed_reference_school.py
python scripts/smoke_reference_school.py   # API must be running
```

---

## Customer lifecycle

| Stage | Environment |
|-------|-------------|
| **Discovery / demo** | Reference School (`reference`) — shared showcase |
| **Customer signs** | New tenant — their slug, their school name |
| **Onboarding** | Import their data into their tenant |
| **Pilot** | Their tenant only — never Reference School |

Reference School is a **product asset**, not a customer production environment.
