# Design System

> **Engineering companion** to [`/CLAUDE.md`](../CLAUDE.md) Part VII (§53–§60) and Part XV (§107,
> the design compass). CLAUDE.md is canonical; this doc records where the system lives in code, how
> to use it, and current gaps. App: `apps/admin-web` (Next.js 16 / React 19 / Tailwind v4).

## The bar
Professional software someone works in all day — comparable to Linear, Notion, Stripe Dashboard.
Every surface must feel: **calm, fast, professional, trustworthy, modern, minimal, accessible,
predictable, never cluttered, never overwhelming** (§107). One unified ecosystem across all portals
(§17) — a parent's screen and a principal's screen are unmistakably the same product.

## Where it lives (code)

| Layer | Path | Notes |
|---|---|---|
| Design tokens | `src/app/globals.css` (`:root`) + `src/styles/` | CSS custom properties; **use tokens, never hardcode** |
| Dark-glass system | `src/styles/sn-*.css`, imported in order via `sn-app-bundle.css` | Respect import order — later files layer on earlier |
| UI primitives | `src/components/ui/` (`kit.tsx`) | Extend these; don't fork a button/input/card per feature |
| Layout shell | `src/components/layout/` (`PageShell`, `PageHeaderCard`, `TopBar`, nav) | Reuse so every portal feels identical |
| Feature components | `src/components/<feature>/` (`briefing/`, `admissions/`, `tutor/`, `staff/`, `marketing/`) | |
| Motion | `src/styles/sn-app-motion.css` + `framer-motion` (component-level) | Don't add a second animation library |
| Icons | `lucide-react` only | Consistent stroke/size |

## Tokens (the ladder — §54)

- **Brand/accent:** `--primary` (deep slate-navy), **`--accent` = the school's colour, injected at
  runtime** (shades via `color-mix`) — **never hardcode the accent**; `--accent-rgb` for alpha.
- **Semantic:** `--success/--warning/--danger/--info` (+ `-light`). Semantic color is separate from
  the accent.
- **Text:** `--text-primary/-secondary/-muted`. **Surfaces:** `--bg`, `--bg-card`, `--border`, and the
  **dark-glass ladder `--sn-glass-a … --sn-glass-g`** (tiered per-surface opacity — the mechanism
  behind distinct, non-uniform tiles).
- **Radius / spacing / layout / motion / type** tokens per §54. If a recurring value isn't tokenized, add a token — don't sprinkle magic numbers.

## The dark-glass system (§55)

Layered translucency + directional light; **per-tile opacity variation** so tiles read as depths, not
one flat sheet. Group related content into `sn-workspace` sheets subdivided into `sn-workspace-zone`s
in a bento grid — not a vertical stack of identical cards. **Hover affects light, not opacity** (never
flatten a tile's base glass on hover — a real past regression). Dark mode is the primary app surface.

## Required states (§57) — every async surface ships all four
Loading (skeletons matching final layout, not spinners) · Empty (teaching empty state + primary
action) · Error (graceful, generic, retry) · Success (`sn-success-pulse`). A screen without them is
not production-ready.

## Accessibility (§58, WCAG 2.1 AA) & responsiveness (§59)
Full keyboard operability + visible focus rings; semantic HTML + ARIA only to fill gaps; AA contrast
on glass; respect `prefers-reduced-motion` (motion layer + `useReducedMotion`); labelled forms with
error association + focus-to-error. Mobile-first, fluid reflow; touch targets ≥44px; no horizontal
page scroll (wide tables scroll in their own container).

## Current gaps (from the Phase-1 assessment — fix in a UI batch)

- **No mobile navigation below 768px** — the sidebar is removed with no replacement drawer.
- Pinch-zoom disabled globally (`maximumScale:1`) — WCAG 1.4.4 failure.
- Muted text fails AA contrast on some glass surfaces; modals lack focus trap + restoration; async
  status not announced to screen readers.
- Native `alert()/confirm()/prompt()` used for success + credit-spend confirmations — build a shared
  toast/confirm service.
- Four stacked CSS theme generations resolved by load order + `!important` — consolidate.

## Rule of extension
Before creating a component, check `ui/` and the feature folder. Add a `variant` prop, don't fork.
Never build a glass card from raw utilities when an `sn-*` primitive exists. Marketing may use the
editorial serif + richer layouts but stays recognizably one family. Branding changes are a
product-owner decision (§60).
