# EUI Consumer Contracts

- **Status:** Accepted
- **Parent architecture:** [`../EUI.md`](../EUI.md)

---

## 1. Purpose

EUI is useful only if platform consumers share it instead of reimplementing understanding.

This document defines the architectural contract for consumers of Educational Understanding Intelligence.

---

## 2. Contract principle

Consumers consume educational understanding. They do not create parallel understanding systems.

```text
EUI
  -> Consumer Contract
  -> Product Intelligence Surface
```

---

## 3. Required consumer inputs

A consumer should receive only the EUI outputs it needs:

- resolved educational context;
- educational identity;
- capability claims;
- educational artifact references;
- graph mappings;
- Trust Report;
- approved evidence where consequential output is involved;
- institutional memory entries appropriate to the role.

Role-sensitive consumers must not receive data beyond their authorization scope.

---

## 4. Consumer map

| Consumer | Contract |
|---|---|
| Academic Evaluation Intelligence | Consumes context, capability claims, artifact understanding, EKG mapping, and trust signals; produces teacher-approved evaluation evidence. |
| Teacher Copilot | Consumes approved curriculum, classroom context, institutional memory, and trust-scored recommendations. |
| Lesson Planner | Consumes curriculum graph, learning objectives, teacher style, and school pacing context. |
| Question Generator | Consumes concept graph, Bloom level, competency targets, board/grade context, and capability constraints. |
| AI Tutor | Consumes grade-safe curriculum knowledge, language mode, prerequisite graph, and approved learning evidence. |
| Parent Assistant | Consumes parent-safe approved evidence and explanations only. |
| Principal Dashboard | Consumes aggregated approved evidence and trust-qualified trends. |
| School Analytics | Consumes EKG mappings, attendance/assessment context, and approved trend evidence. |
| Curriculum Intelligence | Produces and consumes EKG structure and source provenance. |
| Assessment Intelligence | Consumes curriculum, competency, capability, and evaluation constraints. |

---

## 5. Consumer obligations

1. Respect tenant and role boundaries.
2. Use ECE for context instead of reconstructing context locally.
3. Use Platform Capability Registry for capability claims.
4. Use Trust Reports when presenting intelligence.
5. Use approved evidence for consequential user-facing conclusions.
6. Route academic evaluation through AEI.
7. Avoid hidden prompt-only behavior that cannot be audited.
8. Extend platform capability through EUI contracts, not local duplicate understanding logic.

---

## 6. Forbidden consumer behavior

- Creating a private language detector inside AI Tutor.
- Creating a private concept map inside Question Generator.
- Creating direct evaluation logic inside Teacher Copilot.
- Showing raw unapproved AI evaluation to parents.
- Reporting principal insights from unsupported or low-trust data without qualification.
- Making school-wide claims from one teacher's unreviewed correction.
