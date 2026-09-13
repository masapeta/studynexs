import type { MetricRowBlock, WorkspaceMetricItem } from "@/lib/workspace-types";

function statusTint(status: WorkspaceMetricItem["status"]): string {
  if (status === "risk") return "var(--danger)";
  if (status === "warning") return "var(--warning)";
  return "var(--text-primary)";
}

export function MetricRowWidget(block: MetricRowBlock) {
  return (
    <section className="card" style={{ margin: 0, padding: 20 }}>
      <div style={{ display: "grid", gap: 14 }}>
        {block.title ? (
          <h2 style={{ fontSize: 15, fontWeight: 700, color: "var(--text-primary)" }}>{block.title}</h2>
        ) : null}
        <div
          style={{
            display: "grid",
            gap: 12,
            gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          }}
        >
          {block.payload.items.map((item) => (
            <div key={item.label} className="sn-filter-pill" style={{ padding: "14px 16px" }}>
              <div style={{ color: "var(--text-muted)", fontSize: 12 }}>{item.label}</div>
              <div style={{ color: statusTint(item.status), fontSize: 22, fontWeight: 800 }}>
                {item.value}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
