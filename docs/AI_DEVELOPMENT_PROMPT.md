# StudyNexs AI Development Prompt

**Version:** 1.1  
**Last updated:** 2026-07-12  
**Applies to:** Cursor · Claude Code · ChatGPT-assisted reviews

## Purpose

This prompt is used to continue engineering work on the StudyNexs platform.

Its objective is to autonomously implement verified engineering milestones while respecting the Engineering Constitution, validating implementation, maintaining documentation, and preserving platform quality.

---

## Development Scope

The objective is to continue implementation.

Unless blocked:

- Continue development autonomously
- Complete engineering batches
- Run verification
- Update documentation
- Produce an engineering report

Stop only when:

- Product Owner approval is required
- A Git operation requires approval
- A critical blocker is encountered

Do not restart full repository discovery unless the Product Owner instructs you to.

---

## Development Priority

Perform development in this order:

1. Repository Health Check
2. Engineering Startup
3. Verify current implementation
4. Plan
5. Implement
6. Verify (build, lint, test)
7. Update documentation
8. Engineering report
9. Request Product Owner approval

If a **Critical** issue is identified during Engineering Readiness:

- Gather enough evidence to describe the problem
- Do **not** continue implementation based on inconsistent documentation or broken foundation
- Recommend the safest recovery path
- Stop until the Product Owner decides how to proceed

---

You are continuing development of the StudyNexs platform. If these prompts conflict with the repository documentation, follow CLAUDE.md and the engineering documents in the repository. The prompts are startup instructions; the repository documentation is the authoritative source.

Repository

D:\Projects\studynexs-platform\studynexs-dev

Current branch

develop

## Git Rules

Work ONLY in this repository.

Stay on the current branch.

Never:

- Switch branches
- Create branches
- Merge
- Rebase
- Cherry-pick
- Reset
- Stash
- Commit
- Push

If any Git operation is required, explain why and wait for my approval.

---

## Engineering Constraints

Respect the validated architecture.

Do not replace existing implementations unless verification proves they are incorrect.

Prefer extending existing modules over creating new ones.

Avoid duplicate functionality.

Follow the engineering principles defined in CLAUDE.md.

Follow the [Development Lifecycle](./engineering/005-development-lifecycle.md) and [Engineering Validation Standard](./engineering/004-validation-and-testing.md) throughout the session.

Treat the implementation as authoritative.

Before creating any service, endpoint, schema, model, provider, utility, or React component — verify whether an equivalent already exists. Prefer extending existing implementations.

### Continuous architecture improvement

Continuously evaluate the architecture like a senior staff engineer — respect what works, but do not silently accept suboptimal designs forever.

If you identify a **significantly better** architecture or design, a proposal should demonstrate improvements in one or more of:

- Simplicity
- Maintainability
- Reusability
- Performance
- Scalability
- Security
- Reliability
- Testability
- Developer experience

Avoid proposing changes based solely on stylistic preference.

When proposing a change:

- Do **not** replace the existing implementation automatically
- Explain why the proposed design is better (cite concrete benefits from the list above)
- Describe the trade-offs
- Estimate the impact and migration effort
- Recommend whether the change should be adopted **now** or **deferred**
- If the expected benefit is small compared to the migration effort, recommend **deferring** the change

Wait for **Product Owner approval** before implementing architectural changes.

---

## Repository Health Check

Before reading documentation:

- Confirm the repository path
- Confirm the current branch
- Confirm working tree status
- Confirm there are no unexpected local modifications
- Report repository health

---

## Engineering Startup

Read the following completely:

### Engineering Constitution

- CLAUDE.md

### Engineering Dashboard

- docs/PLATFORM_STATUS.md

### Engineering Handover

- docs/AGENT_HANDOVER.md

### Project Status

- docs/STATUS.md
- docs/ROADMAP.md
- docs/DECISION_LOG.md

### Engineering Guides

- docs/engineering/001-studynexs-constitution.md
- docs/engineering/002-git-workflow.md
- docs/engineering/003-engineering-dashboard.md
- docs/engineering/004-validation-and-testing.md
- docs/engineering/005-development-lifecycle.md

### Engineering Dashboard Data

- docs/engineering/platform.json
- docs/engineering/modules.json
- docs/engineering/roadmap.json

---

## Verification

Treat:

- CLAUDE.md as the Engineering Constitution
- PLATFORM_STATUS.md as the Engineering Dashboard
- The implementation as the source of truth

Verify documentation against the actual implementation before making assumptions.

Do not rely solely on documentation.

Do not assume any module exists simply because it appears in documentation.

Use `platform.json`, `modules.json`, `roadmap.json`, and the implementation to determine the current state.

---

## Engineering Readiness

Determine whether the repository is ready for engineering work.

Evaluate:

- Repository health
- Documentation health
- Test health
- Current implementation health
- Architecture consistency
- Dashboard consistency

If inconsistencies exist, classify them as:

| Severity | Examples |
|----------|----------|
| **Critical** | Missing platform foundation, broken imports, failing startup |
| **Important** | Dashboard out of sync with implementation |
| **Informational** | Documentation wording, minor drift |

Recommend the safest recovery path.

Do **not** continue implementation on **Critical** issues until the Product Owner decides.

---

## Autonomous Development

Continue autonomously through engineering batches.

Complete all implementation work necessary to finish the current milestone.

Do **not** stop between normal engineering tasks.

Only stop when:

- Product Owner approval is required
- External blockers exist (missing credentials, unavailable systems, repository limitations)
- Repository health prevents safe implementation
- A Git operation requires approval
- A change could significantly impact business behaviour

Otherwise continue implementation without asking for confirmation between normal engineering tasks.

---

## Autonomous Engineering

Unless one of the stop conditions below is encountered, continue through the entire engineering batch without requesting confirmation between normal engineering activities.

Normal engineering activities include:

- Repository verification
- Reading documentation
- Planning
- Implementation
- Refactoring within approved scope
- Running tests
- Fixing test failures
- Updating documentation
- Updating the Engineering Dashboard
- Producing the Engineering Report

Do not stop after each of these activities.

Treat them as one continuous engineering workflow.

Only stop when:

- A Product Owner decision is required.
- An architectural change requires approval.
- A Git operation requires approval.
- External credentials or systems are unavailable.
- A Critical repository issue prevents safe implementation.

Continue autonomously until the engineering batch is complete.

After completing the batch:

- Present the Engineering Report.
- Summarize verification.
- Summarize documentation updates.
- Summarize remaining work.

Do not commit.

Wait for my approval before committing.

---

## Engineering Dashboard Policy

Before implementing:

- Verify the dashboard matches implementation
- Verify module dependencies
- Verify capability status

After completing a verified engineering batch, update:

- docs/STATUS.md
- docs/CHANGELOG.md
- docs/ROADMAP.md
- docs/AGENT_HANDOVER.md
- docs/PLATFORM_STATUS.md
- docs/engineering/platform.json
- docs/engineering/modules.json
- docs/engineering/roadmap.json
- Any affected docs/modules/*.md

Documentation must always reflect the **verified** implementation.

Never update documentation before verification.

Set `verified` honestly: `tests_passing` only when tests exist and pass.

---

## Testing Policy

Run **only the relevant tests** during development. Reserve the **full test suite** for closing a batch or before significant integration.

Verify as appropriate:

- Imports
- Application startup
- APIs
- Existing functionality (regression)
- New functionality

```text
Build → Lint → Test → fix → repeat until clean
```

Do not claim tests passed unless they were executed.

---

## Batch Completion Checklist

Before producing the Engineering Report, confirm that:

- All planned scope has been completed
- Relevant tests have been executed successfully
- Existing functionality has been verified
- Documentation reflects the verified implementation
- Dashboard metadata has been updated
- No known regressions remain

---

## Engineering Report

After completing a batch, provide:

### Engineering Summary

- Work completed
- Files changed
- Architecture changes (if any)
- New capabilities

### Verification

- Tests executed
- Results
- Application verification
- Regression verification

### Documentation

List every documentation file updated.

### Remaining Work

- Remaining milestones
- Current blockers
- Risks
- Recommended next engineering batch

### Architecture Notes

- Architectural improvements identified
- Deferred improvements (with rationale)
- Technical debt discovered
- Recommended future refactors

---

## Development Complete

A batch is complete only when:

- Scope has been implemented
- Relevant tests pass
- Application verification succeeds
- Documentation is updated
- Dashboard is updated
- Engineering report is complete
- Product Owner approval has been requested

Only then should commit approval be requested.

---

Do not commit unless explicitly asked.

Do not push unless explicitly asked.

Do not perform any Git operation without explicit approval.
