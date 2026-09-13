import type { ErrorStateBlock } from "@/lib/workspace-types";
import type { ReactNode } from "react";

function MetaChip({ children }: { children: ReactNode }) {
  return (
    <span
      className="sn-filter-pill"
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        padding: "6px 10px",
        fontSize: 12,
      }}
    >
      {children}
    </span>
  );
}

export function ErrorStateWidget(block: ErrorStateBlock) {
  return (
    <section className="sn-workspace sn-workspace--secondary p-5 rounded-xl border border-line">
      <div className="sn-workspace-zone" style={{ display: "grid", gap: 10 }}>
        {block.title ? <h2 className="sn-page-header-card__title">{block.title}</h2> : null}
        <div style={{ color: "var(--danger)", fontSize: 15, fontWeight: 700 }}>
          {block.payload.headline}
        </div>
        <div style={{ color: "var(--text-secondary)", fontSize: 14 }}>{block.payload.detail}</div>
        <MetaChip>{block.payload.retryable ? "Retryable" : "Read-only boundary"}</MetaChip>
      </div>
    </section>
  );
}
