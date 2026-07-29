# Assessment Intelligence v1.0 Batch G-B Reproducible Reference Fixture Certification Report

> Owner: Avinash Reddy Masapeta (ARM)
> Date: 2026-07-29
> Status: Certified / Browser proof passed
> Authorization: ASSESSMENT-V1-BATCH-G-B-AUTH-001
> Batch: G-B - Reproducible Reference Fixture + Browser Proof Closure
> Runtime behavior: Unchanged
> Recommendation: Accept Batch G-B for commit, tag, and publication

---

## 1. Certification scope

Batch G-B certifies the reproducible Reference tenant fixture needed by the
Assessment Intelligence v1.0 Batch G browser proof.

This certification covers:

- idempotent fixture seed script;
- approved Grade 6 Science question paper fixture;
- linked/evaluable Unit Test exam fixture;
- deterministic question schema;
- focused fixture tests;
- browser-proof prerequisite guidance;
- no schema/API/UI/runtime behavior change.

It does not certify new product behavior, marks, grading, evidence-ledger
changes, AEI behavior changes, EUI source adoption, OCR behavior, PDF ingestion,
or public product claim expansion.

---

## 2. Artifact inventory

| Artifact | Status |
|---|---|
| `ASSESSMENT_INTELLIGENCE_V1_BATCH_G_B_REPRODUCIBLE_REFERENCE_FIXTURE_DESIGN_BRIEF.md` | Present / accepted |
| `ASSESSMENT_INTELLIGENCE_V1_BATCH_G_B_REPRODUCIBLE_REFERENCE_FIXTURE_IMPLEMENTATION_AUTHORIZATION_CONTRACT.md` | Present / accepted |
| `apps/api/scripts/seed_assessment_browser_proof_fixture.py` | Present |
| `apps/api/tests/test_assessment_intelligence_v1_browser_proof_fixture.py` | Present |
| `apps/admin-web/e2e-assessment-intelligence-v1.cjs` | Guidance updated |
| `ASSESSMENT_INTELLIGENCE_V1_BATCH_G_B_REPRODUCIBLE_REFERENCE_FIXTURE_CERTIFICATION_REPORT.md` | Present |

---

## 3. Fixture scope

```text
Tenant: reference
Board: SSC
Curriculum: Telangana reference material
Grade: 6
Subject: Science
Paper type: Unit Test
Language: English
Question paper: Grade 6 General Science FA-I Reference Unit Test
Exam: Grade 6 General Science FA-I Reference Unit Test
```

The fixture creates proof prerequisites only. It does not create marks,
evaluations, teacher-review records, evidence-ledger records, mastery updates,
or parent/student-visible evidence.

---

## 4. Runtime behavior impact

| Area | Result |
|---|---|
| Runtime product behavior | Unchanged |
| Production UI pages | Unchanged |
| API contracts | Unchanged |
| Database schema | Unchanged |
| Feature flags | Unchanged |
| Question-paper generation | Unchanged |
| Exam service behavior | Unchanged |
| Answer-sheet evaluation behavior | Unchanged |
| AEI behavior | Unchanged |
| EUI behavior | Unchanged |
| Marks | Unchanged |
| Evidence ledger | Unchanged |
| Parent/student visibility | Unchanged |
| Product claims | Unchanged |

---

## 5. Validation evidence

Local validation completed.

```text
cd apps/api
python -m pytest tests/test_assessment_intelligence_v1_browser_proof_fixture.py
Result: PASS - 5 passed

ruff check scripts/seed_assessment_browser_proof_fixture.py tests/test_assessment_intelligence_v1_browser_proof_fixture.py
Result: PASS

python -c "import app.main"
Result: PASS

python scripts/seed_assessment_browser_proof_fixture.py
Result: PASS - fixture ready

cd ../admin-web
npm run build
Result: PASS

node --check e2e-assessment-intelligence-v1.cjs
Result: PASS

npx eslint --no-ignore e2e-assessment-intelligence-v1.cjs
Result: PASS

npm run e2e-assessment-v1
Result: PASS - 16 checks, 0 disallowed console/API errors

cd ../..
git diff --check
Result: PASS
```

The browser proof was executed against the built admin-web app served locally
with `next start` on `127.0.0.1:3000`.

---

## 6. Browser proof result

```text
Assessment Intelligence v1.0 browser proof
tenant=reference base=http://127.0.0.1:3000 api=http://127.0.0.1:8000
primary_scope={"board":"SSC","curriculum":"Telangana reference material","grade":"6","subject":"Science","paperType":"Unit Test","language":"English"}

ALL GREEN (16 checks, 0 disallowed console/API errors)
```

Passing evidence:

- Reference tenant Grade 6 class found;
- Reference tenant Science subject found;
- supported-scope question paper found:
  `Grade 6 General Science FA-I Reference Unit Test (approved)`;
- linked/evaluable exam found:
  `Grade 6 General Science FA-I Reference Unit Test`;
- AI Papers route rendered;
- Exams route rendered;
- Evaluation route rendered;
- teacher authority posture visible/verifiable;
- AEI/evaluation assist posture visible/verifiable;
- no unsupported language/product claims detected;
- tenant header guard passed on 52 API calls.

Allowed console noise:

- four pre-auth/refresh-style `401 Unauthorized` resource messages were
  observed and classified by the existing harness as allowed;
- no disallowed console errors or unexpected API failures were observed.

---

## 7. No-overclaim posture

Batch G-B does not expand product support claims. It provides reproducible proof
data only for the already-declared supported browser-proof scenario.

The browser harness continues to fail if teacher-facing routes present
unsupported claims such as:

- universal multilingual assessment supported;
- automatic question-paper translation supported;
- automatic rubric translation supported;
- autonomous language grading;
- autonomous paper approval.

---

## 8. Risk assessment

| Risk area | Assessment |
|---|---|
| Product behavior risk | Low - explicit Reference tenant fixture script and browser harness guidance only |
| UI risk | Low - no production page edits |
| API/schema risk | Low - no API or schema edits |
| Tenant risk | Low - script targets Reference tenant only; harness verifies tenant header behavior |
| Product-claim risk | Low - no product claim expansion |
| AEI risk | Low - AEI behavior unchanged |
| EUI risk | Low - EUI behavior unchanged |
| Rollback risk | Low - remove fixture script/test/docs/harness guidance |

---

## 9. Certification decision

Batch G-B implementation is ready for ARM acceptance.

Recommended ARM decision:

```text
Decision: Accepted
Commit: Approved
Tag: Approved
```
