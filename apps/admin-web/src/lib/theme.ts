// Per-school theming: the whole UI derives from --accent on :root.
// applyThemeColor() sets --accent + --accent-rgb so CSS can use rgb(var(--accent-rgb) / α).

// Platform default: StudyNexs blue-violet (soft-glass redesign, ARM 2026-08-11).
// Schools still override via their saved brand colour at runtime.
export const DEFAULT_ACCENT = "#5b6cf5";
const THEME_STORAGE_KEY = "sn-brand-color";

const HEX_RE = /^#?([0-9a-fA-F]{6})$/;

function parseHex(color: string): { hex: string; rgb: string } | null {
  const m = HEX_RE.exec(color.trim());
  if (!m) return null;
  const hex = `#${m[1].toLowerCase()}`;
  const n = parseInt(m[1], 16);
  const r = (n >> 16) & 255;
  const g = (n >> 8) & 255;
  const b = n & 255;
  return { hex, rgb: `${r} ${g} ${b}` };
}

export function normalizeThemeColor(color?: string | null): string | null {
  if (!color) return null;
  return parseHex(color)?.hex ?? null;
}

export function getStoredThemeColor(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return normalizeThemeColor(localStorage.getItem(THEME_STORAGE_KEY));
  } catch {
    return null;
  }
}

/** Colour for settings UI — API value, then last saved local, then default. */
export function themeColorForUi(apiColor?: string | null): string {
  return normalizeThemeColor(apiColor) ?? getStoredThemeColor() ?? DEFAULT_ACCENT;
}

type ApplyThemeOptions = {
  /** When true, remember this colour as the school's saved brand (default: false). */
  persist?: boolean;
};

export function applyThemeColor(color?: string | null, options?: ApplyThemeOptions) {
  if (typeof document === "undefined") return;

  const hex =
    normalizeThemeColor(color) ??
    (options?.persist ? null : getStoredThemeColor()) ??
    DEFAULT_ACCENT;

  const parsed = parseHex(hex);
  if (!parsed) return;

  const root = document.documentElement;
  root.style.setProperty("--accent", parsed.hex);
  root.style.setProperty("--accent-rgb", parsed.rgb);

  if (options?.persist) {
    try {
      localStorage.setItem(THEME_STORAGE_KEY, parsed.hex);
    } catch {
      /* ignore quota / private mode */
    }
  }

  window.dispatchEvent(new CustomEvent("sn-theme", { detail: { color: parsed.hex } }));
}
