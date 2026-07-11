# StudyNexs AI Discovery Prompt

**Version:** 1.2  
**Last updated:** 2026-07-12  
**Applies to:** Cursor · Claude Code · ChatGPT-assisted reviews

## Purpose

This prompt is used to onboard an AI assistant into the current state of the StudyNexs repository. Its objective is to understand the verified engineering state, identify any inconsistencies, and produce an implementation plan **without making changes**.

---

## Discovery Scope

The objective is to understand the current engineering state.

This is an **analysis session only**.

Do not:

- Implement features
- Refactor code
- Update documentation
- Execute Git operations

unless explicitly instructed.

---

## Discovery Priority

Perform discovery in this order:

1. Repository Health Check
2. Repository documentation
3. Implementation verification
4. Engineering readiness assessment
5. Discovery report

If a **Critical** issue is identified:

- Continue gathering enough evidence to describe the problem
- Do **not** continue making implementation assumptions based on inconsistent documentation
- Clearly identify the blocker in the discovery report

---

You are joining an existing engineering project. If these prompts conflict with the repository documentation, follow CLAUDE.md and the engineering documents in the repository. The prompts are startup instructions; the repository documentation is the authoritative source.

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

Follow the [Development Lifecycle](./engineering/DEVELOPMENT_LIFECYCLE.md) throughout the session.

Treat the implementation as authoritative.

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

- Confirm the repository path.
- Confirm the current branch.
- Confirm working tree status.
- Confirm there are no unexpected local modifications.
- Report repository health.

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
- docs/engineering/DEVELOPMENT_LIFECYCLE.md
- docs/engineering/testing-guidelines.md

### Engineering Dashboard Data

- docs/engineering/platform.json
- docs/engineering/modules.json
- docs/engineering/roadmap.json

---

## Verification

Treat:

- CLAUDE.md as the Engineering Constitution.
- PLATFORM_STATUS.md as the Engineering Dashboard.
- The implementation as the source of truth.

Verify documentation against the actual implementation before making assumptions.

Do not rely solely on documentation.

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

If inconsistencies exist:

Classify them as:

| Severity | Examples |
|----------|----------|
| **Critical** | Missing platform foundation, broken imports, failing startup |
| **Important** | Dashboard out of sync with implementation |
| **Informational** | Documentation wording, minor drift |

Recommend the safest recovery path.

Do not modify the repository.

---

## Required Summary

Summarize:

### Repository

- Repository health
- Current branch
- Working tree status

### Platform

- Architecture version
- Platform health
- Current engineering milestone
- Previous completed milestone
- Current engineering batch

### Platform Summary

Summarize:

- Completed modules
- Modules currently in progress
- Platform capabilities
- Capability verification status
- Module dependency status
- Architecture health

Use `platform.json`, `modules.json`, `roadmap.json`, and the implementation to determine the current state.

Do not assume any module exists simply because it appears in documentation.

### Verification

Identify:

- Documentation that matches implementation
- Documentation that is outdated
- Missing documentation
- Any inconsistencies (with severity: Critical / Important / Informational)

### Engineering

Identify:

- Next engineering milestone
- Dependencies
- Blockers
- Risks
- Recommended implementation plan
- Architectural improvement proposals (if any), with trade-offs and adopt-now vs defer recommendation

---

## Discovery Complete

The discovery phase is complete only when:

- Repository health has been verified
- Documentation has been compared with the implementation
- Engineering readiness has been assessed
- The discovery report has been delivered
- A recommended implementation plan has been presented

Only then should the Product Owner decide whether to begin implementation.

---

Do not write code.

Do not modify files.

Do not update documentation.

Do not begin implementation until you have completed the discovery report and I have approved the recommended implementation plan.
