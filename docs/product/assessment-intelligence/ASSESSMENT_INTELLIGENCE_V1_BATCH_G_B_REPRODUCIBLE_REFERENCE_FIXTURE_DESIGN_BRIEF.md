# Assessment Intelligence v1.0 Batch G-B Reproducible Reference Fixture Design Brief

> Owner: Avinash Reddy Masapeta (ARM)
> Date: 2026-07-29
> Status: Accepted
> Implementation: Authorized only by the paired Batch G-B implementation contract
> Batch: G-B - Reproducible Reference Fixture + Browser Proof Closure

---

## 1. Purpose

Assessment Intelligence v1.0 Batch G-A added the browser proof harness for the
supported teacher assessment workflow. The remaining gap is reproducibility:
the harness can fail when the Reference tenant lacks the exact supported-scope
question paper and linked/evaluable exam prerequisite.

Batch G-B closes that gap by defining a deterministic Reference tenant fixture
for:

- SSC / Telangana reference material;
- Class 6 / Science;
- Unit Test;
- English;
- approved question paper;
- linked exam with question schema.

The fixture makes the browser proof repeatable. It does not create product
behavior, curriculum authority, grading authority, or new user-visible features.

---

## 2. Relationship to Batch G-A

Batch G-A is the browser proof foundation.

Batch G-B is the reproducible fixture closure.

Together they allow the project to truthfully run:

```text
cd apps/api
python scripts/seed_reference_school.py
python scripts/seed_assessment_browser_proof_fixture.py

cd ../admin-web
npm run e2e-assessment-v1
```

without relying on manually-created local data.

---

## 3. Design scope

Batch G-B may define:

- an idempotent Reference tenant fixture seed script;
- a deterministic Grade 6 Science approved question paper body;
- a linked Unit Test exam with question schema;
- fixture-focused tests proving deterministic schema and governance posture;
- browser harness guidance telling developers how to seed the prerequisite;
- certification evidence for reproducibility.

Batch G-B should not modify production services, routes, schemas, UI pages,
AEI behavior, EUI behavior, marks, evidence-ledger behavior, or public product
claims.

---

## 4. Fixture posture

The fixture is:

- Reference tenant only;
- manually executed by developers or CI smoke setup;
- idempotent;
- deterministic;
- local/dev proof data;
- non-authoritative;
- not a curriculum claim;
- not wired into application startup.

The fixture may create or repair:

- one approved question paper;
- one linked exam with question schema.

It must not create:

- student marks;
- answer-sheet evaluations;
- teacher review decisions;
- evidence ledger records;
- mastery updates;
- parent/student-visible evidence.

---

## 5. Supported browser-proof scope

The fixture supports the Batch G browser-proof primary scope:

```text
board: SSC
curriculum: Telangana reference material
grade: 6
subject: Science
paperType: Unit Test
language: English
```

This is a proof fixture for the Reference tenant. It does not expand the
declared production-supported scope beyond existing Assessment Intelligence
v1.0 declarations.

---

## 6. Non-goals

Batch G-B is not attempting to:

- generate question papers;
- import PDFs;
- run OCR;
- grade answers;
- create answer-sheet evaluations;
- approve teacher decisions;
- publish evidence;
- update mastery;
- migrate consumers;
- add product-facing UI;
- change APIs;
- change schema;
- change Assessment Intelligence runtime behavior.

---

## 7. Acceptance criteria

Batch G-B can be accepted only if:

- the fixture seed is idempotent;
- the fixture creates or repairs the supported-scope approved paper;
- the fixture creates or repairs the linked/evaluable exam;
- the question schema is deterministic and sums to the paper total;
- focused tests validate fixture invariants;
- the browser proof passes after running the fixture;
- no schema/API/UI/runtime behavior changes are introduced;
- no marks, evidence-ledger, AEI, or EUI behavior changes are introduced.

