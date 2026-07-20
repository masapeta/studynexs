"use client";

type Props = {
  packId?: string | null;
  packStatus?: string | null;
  packVersion?: number | null;
  grounded?: boolean;
  groundedAt?: string | Date | null;
  compact?: boolean;
};

function formatGroundedAt(value: string | Date): string {
  const d = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/** Shows curriculum pack provenance on grounded AI outputs. */
export function CurriculumGroundingBadge({
  packId,
  packStatus,
  packVersion,
  grounded,
  groundedAt,
  compact = false,
}: Props) {
  if (!grounded && !packId) return null;

  const when = groundedAt ? formatGroundedAt(groundedAt) : null;

  return (
    <div
      className="sn-grounding-badge"
      style={{
        marginTop: compact ? 8 : 12,
        padding: compact ? "8px 12px" : "10px 14px",
        borderRadius: 8,
        border: "1px solid var(--border-subtle)",
        background: "var(--surface-raised, var(--bg-subtle))",
        fontSize: 12,
        lineHeight: 1.5,
      }}
    >
      <div style={{ fontWeight: 700, marginBottom: 4 }}>Curriculum grounding</div>
      <div style={{ color: "var(--text-muted)" }}>
        {grounded ? "Grounded" : "Not grounded"}
        {packId && (
          <>
            {" · "}
            Pack <code style={{ fontSize: 11 }}>{packId.slice(0, 8)}…</code>
          </>
        )}
        {packStatus && <> · {packStatus}</>}
        {packVersion != null && <> · v{packVersion}</>}
        {when && <> · {when}</>}
      </div>
    </div>
  );
}
