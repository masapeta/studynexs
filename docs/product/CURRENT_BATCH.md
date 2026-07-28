# StudyNexs Current Batch

> Single operational artifact for the latest completed gate and next authorization boundary.

**Last updated:** 2026-07-28

---

## Latest Completed Batch

**Production Safety** is complete and accepted. No implementation gate is
currently active. Operational Proof is the next planned gate and remains not
authorized.

| Field | Value |
|---|---|
| **Release** | Stabilization program |
| **Batch** | Gate 1 |
| **Title** | Production Safety Batch |
| **Status** | **COMPLETED / CERTIFIED / PUBLICATION AUTHORIZED** |
| **Authorized by** | ARM |
| **Authorization date** | 2026-07-28 |
| **Implementation posture** | ARM accepted; commit, tag, and publication authorized |
| **Previous published slice** | AEI v1.0 Teacher Evaluation UX-C (**Published / Certified**) |
| **Next gate** | Operational Proof (**Planned / Not Authorized**) |

### Mission

Close the verified production-safety findings that must precede operational
proof and AEI activation:

1. required runtime dependency declaration;
2. production CORS localhost rejection;
3. tenant-scoped notification reads;
4. correct teacher-scope pagination and totals;
5. exact `Decimal` money handling;
6. truthful, fail-safe PDF behavior.

### Completion evidence required

- changed-scope build, lint, and tests pass;
- adjacent regression tests pass;
- tenant isolation is explicitly tested for notification reads;
- pagination tests prove filtering occurs before page slicing and totals;
- money-path tests prove no float conversion is introduced;
- PDF tests prove the response is either a real PDF or an explicit supported
  failure/fallback contract, never HTML mislabeled or downloaded as PDF;
- certification records remaining risks and confirms no unrelated scope.

Current evidence:

- [`PRODUCTION_SAFETY_BATCH_CERTIFICATION_REPORT.md`](./PRODUCTION_SAFETY_BATCH_CERTIFICATION_REPORT.md)
- ARM decision: PASS for authorized scope;
- commit, annotated certification tag, and publication: authorized.

### Protected scope

This authorization does not include Operational Proof infrastructure, AEI
feature-flag activation, manual-review workflow changes, Golden-set accuracy
claims, topic-ID/mastery redesign, or Teacher Evaluation UX-D.

---

## Last Completed Batch

**Release 0.3 / Batch 3 — School Pilot Experience: Principal + Teacher**

### Status

Accepted / Frozen.

### Mission completed

Batch 3 validated that the first pilot school's two decision-critical users can complete the existing StudyNexs pilot experience without engineering assistance during the walkthrough.

```text
Principal login
↓
Dashboard + curriculum readiness
↓
Academic Intelligence Ready
↓
Teacher login
↓
Assigned class/subject scope
↓
Approved CurriculumPack
↓
Grounded lesson plan
↓
Grounded question paper
↓
Principal + Teacher browser walkthrough PASS
```

### Evidence

- [`BATCH_03_COMPLETION_REPORT.md`](./BATCH_03_COMPLETION_REPORT.md)
- commit `649d835` — `feat(pilot): complete Batch 3 principal teacher proof`

---

## Freeze Rule

Do not modify Release 0.1, Release 0.2, or Release 0.3 except for:

- production defects;
- security fixes;
- critical regressions.

---

## Ordered gates after the completed batch

| Order | Gate | Status |
|---:|---|---|
| 2 | Operational Proof | Planned / Not Authorized |
| 3 | AEI Activation/Trust | Planned / Not Authorized |
| 4 | Topic-ID/mastery spine unification design | Planned / Not Authorized |
| 5 | Teacher Evaluation UX-D | Deferred pending runtime evidence / Not Authorized |

Completion of Production Safety does not authorize any later gate.
