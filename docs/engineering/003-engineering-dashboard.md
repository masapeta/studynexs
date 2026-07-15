---
description: Maintain Engineering Dashboard
---

# Engineering Dashboard Policy

Follow the full lifecycle: [`005-development-lifecycle.md`](./005-development-lifecycle.md).  
Validation gates: [`004-validation-and-testing.md`](./004-validation-and-testing.md).

Before implementing a feature:

1. Read PLATFORM_STATUS.md.
2. Read platform.json.
3. Read modules.json.
4. Read roadmap.json.

Verify that documentation matches implementation.

Never assume documentation is correct without verification.

## Before implementing

Check:

- Does the feature already exist?
- Does it partially exist?
- Can an existing module be extended?
- Can existing services be reused?

Never implement duplicate functionality.

## After verification

Update when appropriate:

- STATUS.md
- CHANGELOG.md
- ROADMAP.md
- AGENT_HANDOVER.md
- PLATFORM_STATUS.md
- platform.json
- modules.json
- roadmap.json

Documentation must reflect verified implementation.

## What to grow (every batch or new capability)

- **Dashboard** — `PLATFORM_STATUS.md`, `platform.json`, `modules.json`, `roadmap.json` (required every engineering batch)
- **Module docs** — add or update `docs/modules/*.md` when a pillar or capability changes
- **Architecture docs** — update `CLAUDE.md` and related docs when platform contracts or design evolve materially

## What to keep stable

- **Core standards** — numbered engineering docs (`001`–`005`), AI prompts, onboarding — change only when real work proves a gap. See [`ONBOARDING.md`](./ONBOARDING.md) *What grows vs what stays stable*.

See [`005-development-lifecycle.md`](./005-development-lifecycle.md) for the full read → verify → plan → implement → validate → document → review → approve → commit flow.