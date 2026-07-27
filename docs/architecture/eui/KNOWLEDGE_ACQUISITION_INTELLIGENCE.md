# Knowledge Acquisition Intelligence (KAI)

- **Status:** Accepted
- **Parent architecture:** [`../EUI.md`](../EUI.md)

---

## 1. Purpose

Knowledge Acquisition Intelligence converts educational inputs into governed educational knowledge candidates.

Schools generate knowledge every day:

- worksheets;
- PDFs;
- images;
- voice notes;
- answer keys;
- teacher notes;
- lesson plans;
- rubrics;
- lab manuals;
- board updates;
- circulars;
- student work.

KAI prevents those inputs from remaining static files. It routes them through acquisition, extraction, normalization, context resolution, trust reporting, and knowledge-graph mapping.

---

## 2. Pipeline

```text
Acquire
  -> Extract
  -> Normalize
  -> Understand
  -> Resolve Context
  -> Map to Educational Knowledge Graph
  -> Store as governed educational knowledge
```

KAI is not a shortcut around human approval. It produces structured candidates and evidence, not unconditional truth.

---

## 3. Input channels

| Input | Acquisition concerns |
|---|---|
| PDF | Layout, embedded text, scanned pages, source provenance |
| Worksheet | Question boundaries, answer key detection, curriculum mapping |
| Image | Camera quality, crop, handwriting, diagram regions |
| Voice | Speaker clarity, language, transcript confidence |
| Teacher note | Informality, local terminology, context dependence |
| Lesson plan | Learning objectives, activities, timeline |
| Rubric | Criteria, marks, acceptable variants, policy alignment |
| Answer key | Question linkage, acceptable answers, tolerances |
| Student work | PII sensitivity, evidence lineage, teacher review |

---

## 4. Canonical output

KAI should output an educational artifact candidate with:

- original source reference;
- provenance;
- extracted content;
- normalized content;
- language and script signals;
- modality signals;
- curriculum/context mapping;
- educational identity;
- evidence references;
- Trust Report;
- capability claims;
- review status.

This architecture program defines the contract only. It does not add persistence or runtime behavior.

Provenance is distinct from the Trust Report. KAI records where an artifact came from and which version or approval state it belongs to; the Trust Report records reliability, uncertainty, and review posture.

---

## 5. Review posture

KAI outputs have trust levels:

| Trust posture | Meaning |
|---|---|
| Approved source | Comes from approved curriculum or previously certified content. |
| Teacher-submitted candidate | Needs teacher or academic owner confirmation before authoritative use. |
| Machine-extracted candidate | Useful for assistance; must expose extraction confidence. |
| Low-confidence candidate | Routed to review and never silently used as truth. |
| Unsupported input | Stored or rejected according to product policy; not interpreted as knowledge. |

---

## 6. Boundaries

KAI must not:

- call LLM providers outside the AI Gateway;
- create final evaluation decisions;
- silently add low-confidence content to EKG as trusted knowledge;
- infer school policies without Institutional Memory or ECE context;
- expose unreviewed sensitive student evidence downstream.

---

## 7. Consumers

KAI primarily feeds:

- EKG;
- ECE;
- Institutional Memory;
- AEI;
- Curriculum Intelligence;
- Question Generation;
- Lesson Planning;
- Teacher Copilot.

No consumer should implement its own independent acquisition pipeline.
