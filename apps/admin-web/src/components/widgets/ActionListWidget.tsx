import Link from "next/link";
import type { ActionListBlock, WorkspaceAction } from "@/lib/workspace-types";

function NavigationActions({ actions }: { actions: WorkspaceAction[] }) {
  return (
    <div className="sn-workspace-zone" style={{ display: "grid", gap: 10 }}>
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
    <section className="sn-workspace sn-workspace--secondary p-5 rounded-xl border border-line">
      <div className="sn-workspace-zone" style={{ display: "grid", gap: 14 }}>
        {block.title ? <h2 className="sn-page-header-card__title">{block.title}</h2> : null}
        <NavigationActions actions={block.payload.items} />
      </div>
    </section>
  );
}
