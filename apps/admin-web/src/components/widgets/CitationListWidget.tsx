import type { CitationListBlock, WorkspaceCitation } from "@/lib/workspace-types";

export function CitationListWidget(block: CitationListBlock) {
  return (
    <section className="sn-workspace sn-workspace--secondary p-5 rounded-xl border border-line">
      <div className="sn-workspace-zone" style={{ display: "grid", gap: 10 }}>
        {block.title ? <h2 className="sn-page-header-card__title">{block.title}</h2> : null}
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
