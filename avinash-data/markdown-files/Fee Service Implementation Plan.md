# Fee Service Implementation Plan

## Overview
The `fee-service` will manage the complete fee lifecycle for a school:
define fee structures → assign to students → record payments → track dues.

It will run on **port `8004`**, sharing the same PostgreSQL database and Redis instance as the other services.

---

## Data Model Design

### Core Entities

```
FeeCategory        → "Tuition Fee", "Transport Fee", "Exam Fee"
    ↓
FeeStructure       → The actual amount for a class/year
    e.g., Grade 5, 2024-25 → Tuition = ₹5000/month
    ↓
StudentFeeRecord   → One record per student per fee per term
    e.g., Ravi Kumar → Tuition → April 2025 → Due: ₹5000
    ↓
FeePayment         → Actual payment recorded against a record
    e.g., Ravi Kumar paid ₹5000 on 10-Apr-2025 via UPI
```

### Key Design Decisions
- **Term-based**: Fees are assigned per month or per term (configurable).
- **Partial payments**: A student can pay ₹3000 against a ₹5000 due → balance ₹2000 remains.
- **Overpayment allowed**: If they pay extra, the balance goes negative (credit).
- **Waiver support**: Admin can waive a fee with a reason.

---

## Open Questions

> [!IMPORTANT]
> **1. Fee Frequency?**
> Should the system support `monthly`, `quarterly`, `annually`, or `one-time` fees?
> Or just start with `monthly` for simplicity?

> [!IMPORTANT]
> **2. Payment Methods?**
> For now, record offline payment methods: `cash`, `UPI`, `bank_transfer`, `cheque`.
> Online payment gateway (Razorpay) will come in a later phase — agree?

> [!NOTE]
> **3. Late Fee / Penalty?**
> Should overdue fees automatically add a late fee after a due date passes?
> Or keep it manual for now (admin can manually adjust)?

---

## Proposed Changes

### 1. Database Models (`auth-service/app/models/fee.py`) [NEW]

#### Models to create:
- **`FeeCategory`** — `name`, `description`, `school_id` (e.g., "Tuition", "Transport")
- **`FeeStructure`** — `category_id`, `class_id`, `academic_year_id`, `amount`, `frequency` (monthly/quarterly/annual/one_time), `due_day` (e.g., 10th of each month)
- **`StudentFeeRecord`** — `student_id`, `fee_structure_id`, `term_label` (e.g., "April-2025"), `due_date`, `amount_due`, `amount_paid`, `status` (PENDING/PARTIAL/PAID/WAIVED/OVERDUE)
- **`FeePayment`** — `fee_record_id`, `amount`, `payment_date`, `payment_method`, `transaction_ref`, `collected_by_id`, `remarks`

#### Alembic Migration:
Generate and apply migration for the 4 new tables.

---

### 2. Service Scaffolding (`services/fee-service/`) [NEW]
- Copy boilerplate from `academic-service` (Dockerfile, requirements.txt, core/, etc.)
- Set `APP_NAME=SMS Fee Service`, port `8004`
- Add to `docker-compose.dev.yml`

---

### 3. API Endpoints (`fee-service`)

#### Fee Categories & Structures (Admin only)
- `POST /api/v1/fees/categories` — Create fee category
- `GET /api/v1/fees/categories` — List categories
- `POST /api/v1/fees/structures` — Create fee structure for a class
- `GET /api/v1/fees/structures` — List structures (filter by class/year)

#### Student Fee Records (Admin only)
- `POST /api/v1/fees/records/generate` — Bulk-generate monthly fee records for all students in a class for a given month
- `GET /api/v1/fees/records` — List fee records (filter by student/class/status/month)
- `PATCH /api/v1/fees/records/{id}/waive` — Waive a fee with reason

#### Payments (Admin / Operations)
- `POST /api/v1/fees/payments` — Record a payment against a fee record
- `GET /api/v1/fees/payments` — List payments (filter by student/date range)

#### Student & Parent View
- `GET /api/v1/fees/my-dues` — Student/parent sees their own pending dues
- `GET /api/v1/fees/my-payments` — Student/parent sees payment history

---

## Verification Plan

### Manual Testing via Swagger (`:8004/docs`)
1. Login as admin → create a `FeeCategory` (e.g., "Tuition Fee")
2. Create a `FeeStructure` for Grade 5, 2024-25 → ₹5000/month
3. Generate fee records for all Grade 5 students for April 2025
4. Record a partial payment of ₹3000 → verify status = `PARTIAL`, balance = ₹2000
5. Record remaining ₹2000 → verify status = `PAID`
6. Login as parent → verify they can see their child's dues and payment history
7. Attempt to create a fee structure as a teacher → verify `403 Forbidden`
