# The School Knowledge Graph

> **Engineering companion** to [`/CLAUDE.md`](../CLAUDE.md) §39.3 (canonical). **Status: planned — no
> tables yet.** This doc captures the model, the build order, and the rules so it's built correctly
> when its turn comes. It is the backbone of Curriculum Intelligence.

## Why it exists

Beyond the vector index, model curriculum + learning as an explicit **graph of relationships**. It
makes retrieval precise (retrieve *by concept*, not just similarity), tutoring targeted (teach the
exact weak concept), recommendations/adaptive learning possible (next-best concept), analytics
meaningful (concept-level mastery/gaps), and future agents traversable/explainable.

## Core relationships (nodes → edges)

```
Curriculum → Subject → Chapter → Topic → Concept     (the academic spine, from CurriculumPack)
Question   → Concept                                  (every item knows what it tests)
Assessment → Bloom level        Concept → Skill       (difficulty + skill mapping)
Learning outcome → Concept                            (outcomes grounded in concepts)
Student    → weak Concept                             (mastery gaps, derived from evaluation)
Teacher    → Lesson             Textbook → Chapter → Concept   (planning + provenance)
```

## Rules (non-negotiable)

- **Derived from approved sources only** — CurriculumPack + approved Concept Cards (§39, §39.1). Never free-text.
- **Tenant-scoped** (`school_id` on every node/edge; no cross-tenant traversal) (§22).
- **Grounded & citable** — edges trace to a source; supports citations (§109.3).
- **Student-linked edges are PII-sensitive** (§62.5) — same protection as marks.
- **Built incrementally, never as a speculative ontology ahead of need** (§4.1).

## Build order (spine-first)

1. **Curriculum spine** — `Subject → Chapter → Topic → Concept` from the approved pack. (Pack already
   has chapter→topic→concept in `app/modules/curriculum`; the graph makes the edges first-class + queryable.)
2. **Question → Concept** — tag `QuestionBankItem`s to concepts (feeds precise retrieval + difficulty).
3. **Student → weak Concept** — derived from answer-sheet evaluation + mastery (`app/modules/mastery`).
4. **Bloom / Skill / Learning-outcome** edges — as Assessment Intelligence engines land (§40.4).

## Implementation guidance (when built)

- Start in **Postgres** (adjacency tables with `school_id`, FK to pack entities) — not a separate graph
  DB — until a measured need proves otherwise (`CLAUDE.md` §88, avoid premature infra).
- Consume it through Curriculum Intelligence services; RAG retrieval augments similarity search with
  concept edges. Do not fork a second store.

## Current state
Modeled in the constitution; the curriculum hierarchy exists as pack data. **No graph tables/queries
implemented yet.** Sequenced after grounding QP generation and Document Intelligence
(→ [`ROADMAP.md`](./ROADMAP.md)).
