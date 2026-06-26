const MONO_COLORS = ["#a9772b", "#3f7d6a", "#bf4d3a", "#4a5a8a", "#7a5aa0", "#2f7d8c"];

function initials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .map((w) => w[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();
}

type Props = { name: string; size?: number; className?: string; title?: string };

export function PersonMono({ name, size = 38, className = "", title }: Props) {
  const bg = MONO_COLORS[(name.charCodeAt(0) || 0) % MONO_COLORS.length];
  return (
    <div
      className={`briefing-mono ${className}`.trim()}
      style={{
        width: size,
        height: size,
        fontSize: size * 0.36,
        background: `${bg}22`,
        color: bg,
      }}
      title={title}
      aria-hidden={title ? undefined : true}
      aria-label={title}
    >
      {initials(name || "?")}
    </div>
  );
}
