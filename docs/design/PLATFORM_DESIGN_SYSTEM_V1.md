# StudyNexs Platform Design System v1

> **Status:** ✅ Complete and canonical (2026-07-17)  
> **Authority:** All future UI work in `apps/admin-web` MUST consume this system.  
> **Governance:** Frozen in Product Execution Phase — extend only when implementation is blocked.

Phases 0 through 3C established the platform design language. **Design System v1 is closed.** Portal parity (Phase 3B) requires separate plans.

**Foundation audit trail:** [`../ui-audit/`](../ui-audit/)

---

## Governance (normative)

| Pillar | Document / asset |
|--------|------------------|
| **Platform Tokens** | `apps/admin-web/src/styles/platform-tokens.css`, `platform-aliases.css` |
| **Platform States** | `platform-states.css` |
| **Platform Components** | `platform-components.css` |
| **Platform Interaction Vocabulary** | [`../ui-audit/PLATFORM_INTERACTION_VOCABULARY.md`](../ui-audit/PLATFORM_INTERACTION_VOCABULARY.md) |
| **Platform Accessibility Principles** | [`../ui-audit/PLATFORM_ACCESSIBILITY_PRINCIPLES.md`](../ui-audit/PLATFORM_ACCESSIBILITY_PRINCIPLES.md) |
| **Brand Consistency Matrix** | [`../ui-audit/BRAND_CONSISTENCY_MATRIX.md`](../ui-audit/BRAND_CONSISTENCY_MATRIX.md) |
| **CSS Ownership** | [`../ui-audit/CSS_OWNERSHIP.md`](../ui-audit/CSS_OWNERSHIP.md) |
| **Review Standards** | [`../reviews/REVIEW_STANDARDS.md`](../reviews/REVIEW_STANDARDS.md) |

**Platform Motion:** `platform-motion.css`, `lib/platform-motion.ts` — extends tokens per CSS ownership map.

---

## Implementation layers

| Layer | Asset | Purpose |
|-------|-------|---------|
| Brand primitives | `PlatformMark`, `StudyNexsBrandMark`, `AppEntryLoading` | Identity continuity |
| Design tokens | `platform-tokens.css`, `platform-aliases.css` | Spacing, color, motion, elevation |
| Interaction states | `platform-states.css` | Hover, focus, loading, semantic surfaces |
| Platform motion | `platform-motion.css` | Enter, modal, briefing; reduced motion |
| Components | `platform-components.css` | Buttons, inputs, tables, cards, dialogs |
| Typography | `platform-typography.css` | Product chrome utilities |

### Import chain

```
platform-tokens.css → platform-aliases.css → platform-states.css
  → platform-components.css → platform-motion.css → platform-typography.css
```

Wired via `globals.css`, `sn-app-bundle.css`, `marketing-tokens.css`.

---

## Drift prevention

1. Extend `platform-tokens.css` — no hardcoded platform values in feature CSS.
2. Interaction states → `platform-states.css` only.
3. Components → `platform-components.css` only.
4. Motion → `platform-motion.css` only.
5. Follow [`CSS_OWNERSHIP.md`](../ui-audit/CSS_OWNERSHIP.md).
6. **No Surprise Rule** — no workflow/nav/IA changes without product approval.
7. **Product Execution Phase:** do not expand DS v1 without implementation-driven need.

---

## Phase history

| Phase | Outcome |
|-------|---------|
| 0–2C | Tokens, states, a11y, components |
| 3A | Motion |
| 3C | CSS maintainability |

Reviews: [`../ui-audit/reviews/`](../ui-audit/reviews/)

---

## Post–v1 (deferred)

| Track | Status |
|-------|--------|
| 3B.1 Parent portal platform parity | Blocked — implementation plan required |
| 3B.2 Parent experience strategy | UX exploration only |

See [`../ui-audit/PHASE3B_JUSTIFICATION_REVISED.md`](../ui-audit/PHASE3B_JUSTIFICATION_REVISED.md).

---

## Verification

```powershell
rg "platform-components|platform-states|platform-tokens" apps/admin-web/src/app/globals.css
# Read docs/ui-audit/CSS_OWNERSHIP.md before extending styles
```
