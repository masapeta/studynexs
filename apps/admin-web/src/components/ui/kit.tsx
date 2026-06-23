"use client";

/**
 * Shared mobile UI kit — the reusable primitives the portals were missing.
 * Clean, iOS-leaning cards/rows/tiles built on the app's CSS variables.
 * Styling lives in globals.css under the `.ui-*` namespace.
 */
import type { ReactNode } from "react";
import type { LucideIcon } from "lucide-react";
import { ChevronRight } from "lucide-react";

export type Tone = "default" | "success" | "warning" | "danger" | "info" | "accent";

export function Card({
  children,
  onClick,
  className = "",
  padded = true,
}: {
  children: ReactNode;
  onClick?: () => void;
  className?: string;
  padded?: boolean;
}) {
  const interactive = !!onClick;
  return (
    <div
      className={`ui-card${padded ? "" : " ui-card-flush"}${interactive ? " ui-card-tap" : ""} ${className}`}
      onClick={onClick}
      role={interactive ? "button" : undefined}
      tabIndex={interactive ? 0 : undefined}
      onKeyDown={interactive ? (e) => (e.key === "Enter" || e.key === " ") && onClick!() : undefined}
    >
      {children}
    </div>
  );
}

export function SectionHeader({ title, action }: { title: string; action?: ReactNode }) {
  return (
    <div className="ui-section-header">
      <h2 className="ui-section-title">{title}</h2>
      {action}
    </div>
  );
}

export function StatTile({
  icon: Icon,
  label,
  value,
  tone = "default",
  hint,
}: {
  icon: LucideIcon;
  label: string;
  value: ReactNode;
  tone?: Tone;
  hint?: string;
}) {
  return (
    <div className={`ui-stat ui-tone-${tone}`}>
      <div className="ui-stat-top">
        <span className="ui-stat-icon">
          <Icon size={15} strokeWidth={2.4} />
        </span>
        <span className="ui-stat-label">{label}</span>
      </div>
      <div className="ui-stat-value">{value}</div>
      {hint && <div className="ui-stat-hint">{hint}</div>}
    </div>
  );
}

export function ListRow({
  icon: Icon,
  title,
  subtitle,
  value,
  tone = "default",
  onClick,
  chevron = false,
}: {
  icon?: LucideIcon;
  title: ReactNode;
  subtitle?: ReactNode;
  value?: ReactNode;
  tone?: Tone;
  onClick?: () => void;
  chevron?: boolean;
}) {
  const interactive = !!onClick;
  return (
    <div
      className={`ui-row${interactive ? " ui-row-tap" : ""}`}
      onClick={onClick}
      role={interactive ? "button" : undefined}
      tabIndex={interactive ? 0 : undefined}
      onKeyDown={interactive ? (e) => (e.key === "Enter" || e.key === " ") && onClick!() : undefined}
    >
      {Icon && (
        <span className={`ui-row-icon ui-tone-${tone}`}>
          <Icon size={18} strokeWidth={2.2} />
        </span>
      )}
      <div className="ui-row-body">
        <div className="ui-row-title">{title}</div>
        {subtitle && <div className="ui-row-subtitle">{subtitle}</div>}
      </div>
      {value != null && <div className="ui-row-value">{value}</div>}
      {chevron && <ChevronRight size={18} className="ui-row-chevron" />}
    </div>
  );
}

function toneForPct(pct: number): Tone {
  if (pct >= 75) return "success";
  if (pct >= 50) return "warning";
  return "danger";
}

export function ProgressBar({
  pct,
  tone,
}: {
  pct: number;
  tone?: Tone;
}) {
  const t = tone ?? toneForPct(pct);
  return (
    <div className="ui-progress">
      <div className={`ui-progress-fill ui-tone-${t}`} style={{ width: `${Math.max(0, Math.min(100, pct))}%` }} />
    </div>
  );
}

export function Ring({
  pct,
  size = 60,
  tone,
  label,
}: {
  pct: number;
  size?: number;
  tone?: Tone;
  label?: string;
}) {
  const t = tone ?? toneForPct(pct);
  const stroke = 6;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const clamped = Math.max(0, Math.min(100, pct));
  return (
    <div className="ui-ring" style={{ width: size, height: size }}>
      <svg width={size} height={size}>
        <circle cx={size / 2} cy={size / 2} r={r} className="ui-ring-track" strokeWidth={stroke} fill="none" />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          className={`ui-ring-fill ui-tone-${t}`}
          strokeWidth={stroke}
          fill="none"
          strokeDasharray={c}
          strokeDashoffset={c * (1 - clamped / 100)}
          strokeLinecap="round"
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
        />
      </svg>
      <span className="ui-ring-label">{label ?? `${Math.round(clamped)}%`}</span>
    </div>
  );
}

export function Skeleton({ h = 16, w = "100%", radius = 8 }: { h?: number; w?: number | string; radius?: number }) {
  return <span className="ui-skel" style={{ height: h, width: w, borderRadius: radius }} />;
}

export function SkeletonCard() {
  return (
    <div className="ui-card" aria-hidden>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 14 }}>
        <Skeleton h={44} w={44} radius={22} />
        <div style={{ flex: 1 }}>
          <Skeleton h={15} w="55%" />
          <div style={{ height: 8 }} />
          <Skeleton h={12} w="35%" />
        </div>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
        <Skeleton h={64} radius={12} />
        <Skeleton h={64} radius={12} />
      </div>
    </div>
  );
}

export function EmptyState({
  icon: Icon,
  title,
  message,
  action,
}: {
  icon: LucideIcon;
  title: string;
  message?: string;
  action?: ReactNode;
}) {
  return (
    <div className="ui-empty">
      <span className="ui-empty-icon">
        <Icon size={26} strokeWidth={2} />
      </span>
      <div className="ui-empty-title">{title}</div>
      {message && <div className="ui-empty-message">{message}</div>}
      {action && <div className="ui-empty-action">{action}</div>}
    </div>
  );
}
