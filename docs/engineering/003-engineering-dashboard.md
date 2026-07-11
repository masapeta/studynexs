---
description: Maintain Engineering Dashboard
---

# Engineering Dashboard Policy

Follow the full lifecycle: [`DEVELOPMENT_LIFECYCLE.md`](./DEVELOPMENT_LIFECYCLE.md).

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

See [`DEVELOPMENT_LIFECYCLE.md`](./DEVELOPMENT_LIFECYCLE.md) for the full read → verify → plan → implement → test → document → review → approve → commit flow.