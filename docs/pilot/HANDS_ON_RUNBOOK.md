# Hands-On Demo Runbook

> **Gate 1 only** — synthetic school data, school staff *drive* the product.  
> **School:** Sri Saraswathi High School (tenant `test`) · 288 students, Classes 1–10  
> **Companions:** [PILOT_DISCOVERY.md](../PILOT_DISCOVERY.md) · [BACKLOG.md](../BACKLOG.md) · [PILOT_OUTCOME_SHEET.md](./PILOT_OUTCOME_SHEET.md)

---

## 1. Frame the meeting (30 seconds)

Say this before anyone logs in:

> *"Everything you see today is **demo data** — a sample school we built for evaluation. The yellow banner means it's not your real parent or student records. After today, if we move forward, we run a **small pilot** — one class, one subject, parents who opt in — with consent and your real syllabus. Today is hands-on practice, not go-live."*

| Phase | Real data? | What school does |
|-------|------------|------------------|
| **Today (Gate 1)** | No — synthetic | Explore all four portals; you ask questions |
| **Pilot (Gate 2)** | Yes — bounded | One class × subject; weekly feedback |
| **Production (Gate 3)** | Yes — full school | Hardening, scale, compliance |

---

## 2. Before they arrive (you)

### 2.1 Seed demo data (fresh machine or stale DB)

From repo root, API must have Postgres running and migrations applied.

```powershell
cd apps\api

# Core chain (idempotent — safe to re-run)
python scripts\seed_demo_ssc.py
python scripts\patch_demo_ssc_rbac.py
python scripts\seed_demo_extras.py
python scripts\seed_exam_marks.py
python scripts\seed_parents.py
python scripts\patch_demo_portal_logins.py
python scripts\seed_teacher_dashboard.py
python scripts\seed_working_session.py
```

### 2.2 Start servers

**Terminal 1 — API (port 8000)**

```powershell
cd apps\api
# Ensure .env has DB + at least one AI key (Gemini recommended for demo)
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — Admin web (port 3000)**

```powershell
cd apps\admin-web
npm run dev
```

For a deployed demo, use your **HTTPS URL** instead of localhost ([G1-07](../BACKLOG.md)).

### 2.3 Smoke checks (optional but recommended)

```powershell
cd apps\api
python scripts\smoke_demo_readiness.py

cd ..\admin-web
npm run e2e-smoke
```

Both need servers running. E2E screenshots land in `%TEMP%\sn-e2e\`.

### 2.4 Pre-approve one question paper (AI backup)

If live AI generation is slow or fails, pre-generate and **Approve** one Class 10 Maths paper before the meeting (`Teaching → AI Papers`). Mention: *"We can also use a pre-approved paper if the network is slow."*

---

## 3. Demo logins (give them this card)

Open **Login** → choose portal tab → credentials auto-fill → **Sign in**.

| Portal | Who to hand the device to | Username | Password |
|--------|---------------------------|----------|----------|
| **Staff / Principal** | Principal or office admin | `principal` | `Demo@1234` |
| **Teacher** | Maths teacher (Class 10) | `teacher6` | `Demo@1234` |
| **Parent** | Parent representative | `parent_demo` | `Demo@1234` |
| **Student** | Class 10 student | `student_demo` | `Demo@1234` |

Direct links (same creds):

- Staff: `/login?portal=staff`
- Teacher: `/login?portal=teacher`
- Parent: `/login?portal=parent`
- Student: `/login?portal=student`

**Mobile:** responsive web / PWA — no separate app install for today. Add to home screen works on phones.

---

## 4. Suggested hands-on flow (~45–60 min)

**You facilitate; they click.** Rotate devices or use a projector for one portal at a time.

### A. Principal (10 min) — `principal`

1. **Dashboard** — school snapshot (students, attendance, fees).
2. **Students** → open any Class 10 student — profile, guardians, attendance.
3. **Staff** — teacher list.
4. **Classes** → **Class 10-A** — roster, subjects.
5. **Settings** — school name, theme (optional live tweak).

*Talking point:* *"One login for the whole school — role-based menus."*

### B. Teacher (15 min) — `teacher6`

1. Lands on **Dashboard** (teacher view).
2. **Teaching → AI Papers** — Class 10, Maths, pick 2–3 topics → **Generate** → scroll paper → edit one question → **Approve**.
3. **Teaching → Exams** — existing exam + marks.
4. **Teaching → Report Cards** — pick class → generate (or show existing).
5. **Teaching → Topic Mastery** — weak topics heatmap.

*Talking point:* *"Teacher approves everything before it goes to parents or print."*

### C. Parent (10 min) — `parent_demo`

1. **Parent home** — linked child(ren) overview.
2. **My Children** — progress, weak topics.
3. **Fees** — due / paid (demo amounts).
4. **Notices** — school announcements.

*Talking point:* *"In a real pilot, only opt-in parents get accounts — after consent."*

### D. Student (10 min) — `student_demo`

1. **Student home** — today's context.
2. **Mastery** — topic progress.
3. **AI Tutor** — ask one syllabus-style question (keep it short).

*Talking point:* *"Tutor is guided practice, not answer-key cheating — teacher visibility in pilot."*

### E. Wrap — discovery (10 min)

Switch to [PILOT_DISCOVERY.md](../PILOT_DISCOVERY.md) questions. Fill [PILOT_OUTCOME_SHEET.md](./PILOT_OUTCOME_SHEET.md) before you leave the building.

---

## 5. What to show vs skip

### Show confidently

| Area | Where |
|------|--------|
| Students, staff, classes, attendance | Dashboard |
| AI question papers | Teaching → AI Papers |
| Exams, marks, corrections | Teaching → Exams |
| Report cards | Teaching → Report Cards |
| Topic mastery / digest | Teaching → Mastery |
| Parent & student portals | `/parent`, `/student` |
| Fees (read-only stats) | Finance → Fees |
| Timetable, notices, transport | Respective modules |

### Label as preview or skip if asked

| Area | Honest line |
|------|-------------|
| **Online fee payment** | *"Receipts and dues tracking work; Razorpay checkout is next pilot phase."* |
| **SMS / WhatsApp alerts** | *"In-app notifications work; SMS/email providers wire in during pilot."* |
| **Library / Events pages** | *"API ready; full UI polish in backlog — not wedge for exam pilot."* |
| **Flutter native apps** | *"Phase 2 — mobile web works today."* |
| **Full-school go-live** | *"We start one class × one subject, prove value, then expand."* |

---

## 6. “Not live yet” talking points

Use if they ask about privacy, storage, or parent rollout:

1. **Data today** — synthetic demo only; yellow **Demo data** banner is intentional.
2. **Real pilot** — separate tenant; CSV/onboarding for one class; DPDP consent before parent accounts.
3. **Files** — demo uses local storage; pilot/production moves to cloud blob + scan on upload.
4. **AI** — human-in-the-loop (approve papers, review report remarks); no auto-publish to parents.
5. **Your keys** — school data never trains public models; API keys are yours / ours under contract.

---

## 7. Troubleshooting

| Symptom | Fix |
|---------|-----|
| Blank page / 401 | Re-login; confirm API on `:8000` and `X-Tenant-Slug: test` |
| AI generate hangs | Use pre-approved paper; check Gemini/OpenAI key in API `.env` |
| `e2e-smoke` connection refused | Start both servers first |
| Parent/student login fails | Re-run `patch_demo_portal_logins.py` |
| No Class 10 data | Re-run `seed_demo_ssc.py` + `seed_exam_marks.py` |
| Rate limit on login | Wait 1 min; smoke scripts share principal login |

---

## 8. After the meeting

1. Save outcome: `docs/pilot/<school-slug>/outcome-YYYY-MM-DD.md` (copy from [PILOT_OUTCOME_SHEET.md](./PILOT_OUTCOME_SHEET.md)).
2. Update [BACKLOG.md](../BACKLOG.md) if they committed to Gate 2 scope.
3. If **REAL INTEREST** — collect pack inputs ([TRACK_AB_EXECUTION.md](../TRACK_AB_EXECUTION.md) § A2): book edition, syllabus, one sample paper, HOD contact.
4. If **POLITE NO** — log and move on; don't over-invest in custom demo data.

---

## Quick reference — one page to print

```
StudyNexs hands-on demo — DEMO DATA ONLY

URL:     http://localhost:3000  (or your HTTPS demo URL)
School:  Sri Saraswathi High School (sample)

principal  / Demo@1234  → Admin dashboard
teacher6   / Demo@1234  → Teacher (Class 10 Maths)
parent_demo / Demo@1234 → Parent portal
student_demo / Demo@1234 → Student portal

Try: AI Papers → Generate → Approve → Report Cards → Parent view
```
