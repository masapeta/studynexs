import type { CitationListBlock, WorkspaceCitation } from "@/lib/workspace-types";

export function CitationListWidget(block: CitationListBlock) {
  return (
    <section className="card" style={{ margin: 0, padding: 20 }}>
      <div style={{ display: "grid", gap: 10 }}>
        {block.title ? (
          <h2 style={{ fontSize: 15, fontWeight: 700, color: "var(--text-primary)" }}>{block.title}</h2>
        ) : null}
        {block.payload.items.map((citation: WorkspaceCitation) => (
          <div key={`${citation.source_type}:${citation.source_id}`} className="sn-filter-pill" style={{ padding: "14px 16px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
              <strong>{citation.label}</strong>
              <span style={{ color: "var(--text-muted)", fontSize: 12 }}>{citation.source_type}</span>
            </div>
            <div style={{ color: "var(--text-secondary)", fontSize: 14, marginTop: 6 }}>
              {citation.summary}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
