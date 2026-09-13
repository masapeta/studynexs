import Link from "next/link";
import type { ActionListBlock, WorkspaceAction } from "@/lib/workspace-types";

function NavigationActions({ actions }: { actions: WorkspaceAction[] }) {
  return (
    <div style={{ display: "grid", gap: 10 }}>
      {actions.map((action) =>
        action.enabled ? (
          <Link
            key={`${action.href}:${action.label}`}
            href={action.href}
            className="btn btn-outline"
            style={{ justifyContent: "space-between", width: "100%" }}
          >
            <span>{action.label}</span>
            <span style={{ color: "var(--text-muted)", fontSize: 12 }}>Open</span>
          </Link>
        ) : (
          <div
            key={`${action.href}:${action.label}`}
            className="sn-filter-pill"
            aria-disabled="true"
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              gap: 12,
              opacity: 0.6,
              padding: "12px 14px",
            }}
          >
            <span>{action.label}</span>
            <span style={{ fontSize: 12, color: "var(--text-muted)" }}>Unavailable</span>
          </div>
        )
      )}
    </div>
  );
}

export function ActionListWidget(block: ActionListBlock) {
  return (
    <section className="card" style={{ margin: 0, padding: 20 }}>
      <div style={{ display: "grid", gap: 14 }}>
        {block.title ? (
          <h2 style={{ fontSize: 15, fontWeight: 700, color: "var(--text-primary)" }}>{block.title}</h2>
        ) : null}
        <NavigationActions actions={block.payload.items} />
      </div>
    </section>
  );
}
