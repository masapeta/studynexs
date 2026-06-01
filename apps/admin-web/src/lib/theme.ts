// Per-school theming: the whole UI derives from a single CSS variable (--accent).
// Setting it re-themes active nav, buttons, highlights, focus rings, badges, the hero, etc.
// (the accent shades are derived from --accent via color-mix in globals.css).

export const DEFAULT_ACCENT = "#ee6c4d";

export function applyThemeColor(color?: string | null) {
  if (typeof document === "undefined") return;
  const root = document.documentElement;
  if (color && /^#[0-9a-fA-F]{6}$/.test(color)) {
    root.style.setProperty("--accent", color);
  } else {
    root.style.removeProperty("--accent");
  }
}
