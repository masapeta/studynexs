"use client";

import Link from "next/link";
import type { ReactNode } from "react";
import type {
  WorkspaceAction,
  WorkspaceBlock,
  WorkspaceCitation,
  WorkspaceMetricItem,
  WorkspaceVerification,
} from "@/lib/workspace-types";

function surfaceClass(priority: WorkspaceBlock["priority"]): string {
  return priority === "primary"
    ? "sn-workspace sn-workspace--primary"
    : "sn-workspace sn-workspace--secondary";
}

function statusTint(status: WorkspaceMetricItem["status"]): string {
  if (status === "risk") return "var(--danger)";
  if (status === "warning") return "var(--warning)";
  return "var(--text-primary)";
}

function verificationLabel(verification: WorkspaceVerification): string {
  if (verification.status === "verified") return "Verified evidence";
  if (verification.status === "stale") return "Evidence may be stale";
  if (verification.status === "conflicting") return "Evidence has conflicts";
  if (verification.status === "requires_approval") return "Needs approval";
  return "Evidence missing";
}

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

export function TeacherWorkspaceBlockRenderer({
  block,
}: {
  block: WorkspaceBlock;
}) {
  if (block.type === "student_card") {
    return (
      <section className={surfaceClass(block.priority)} style={{ padding: 18 }}>
        <div className="sn-workspace-zone" style={{ display: "grid", gap: 14 }}>
          {block.title ? <h2 className="sn-page-header-card__title">{block.title}</h2> : null}
          <div
            style={{
              display: "grid",
              gap: 12,
              gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
            }}
          >
            <div>
              <div style={{ color: "var(--text-muted)", fontSize: 12 }}>Student</div>
              <div style={{ fontSize: 18, fontWeight: 700 }}>{block.payload.display_name}</div>
            </div>
            <div>
              <div style={{ color: "var(--text-muted)", fontSize: 12 }}>Class</div>
              <div>{block.payload.class_label}</div>
            </div>
            <div>
              <div style={{ color: "var(--text-muted)", fontSize: 12 }}>Section</div>
              <div>{block.payload.section_label}</div>
            </div>
            <div>
              <div style={{ color: "var(--text-muted)", fontSize: 12 }}>Admission no.</div>
              <div>{block.payload.admission_no || "Not available"}</div>
            </div>
          </div>
        </div>
      </section>
    );
  }

  if (block.type === "metric_row") {
    return (
      <section className={surfaceClass(block.priority)} style={{ padding: 18 }}>
        <div className="sn-workspace-zone" style={{ display: "grid", gap: 14 }}>
          {block.title ? <h2 className="sn-page-header-card__title">{block.title}</h2> : null}
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

  if (block.type === "table") {
    return (
      <section className={surfaceClass(block.priority)} style={{ padding: 18, overflowX: "auto" }}>
        <div className="sn-workspace-zone" style={{ display: "grid", gap: 14 }}>
          {block.title ? <h2 className="sn-page-header-card__title">{block.title}</h2> : null}
          {block.payload.rows.length === 0 ? (
            <div style={{ color: "var(--text-muted)", fontSize: 14 }}>{block.payload.empty_message}</div>
          ) : (
            <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 520 }}>
              <thead>
                <tr>
                  {block.payload.columns.map((column) => (
                    <th
                      key={column.key}
                      style={{
                        borderBottom: "1px solid var(--border)",
                        color: "var(--text-muted)",
                        fontSize: 12,
                        fontWeight: 600,
                        padding: "0 0 10px",
                        textAlign: "left",
                      }}
                    >
                      {column.label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {block.payload.rows.map((row, index) => (
                  <tr key={index}>
                    {block.payload.columns.map((column) => (
                      <td
                        key={column.key}
                        style={{
                          borderBottom: "1px solid color-mix(in srgb, var(--border) 70%, transparent)",
                          padding: "12px 0",
                          verticalAlign: "top",
                        }}
                      >
                        {row[column.key] === null ? "-" : String(row[column.key])}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </section>
    );
  }

  if (block.type === "citation_list") {
    return (
      <section className={surfaceClass(block.priority)} style={{ padding: 18 }}>
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

  if (block.type === "action_list") {
    return (
      <section className={surfaceClass(block.priority)} style={{ padding: 18 }}>
        <div className="sn-workspace-zone" style={{ display: "grid", gap: 14 }}>
          {block.title ? <h2 className="sn-page-header-card__title">{block.title}</h2> : null}
          <NavigationActions actions={block.payload.items} />
        </div>
      </section>
    );
  }

  return (
    <section className={surfaceClass(block.priority)} style={{ padding: 18 }}>
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

export function TeacherWorkspaceResponseMeta({
  verification,
  warnings,
  requestId,
}: {
  verification: WorkspaceVerification;
  warnings: string[];
  requestId: string;
}) {
  return (
    <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
      <MetaChip>{verificationLabel(verification)}</MetaChip>
      {verification.checked_at ? <MetaChip>Checked {new Date(verification.checked_at).toLocaleString()}</MetaChip> : null}
      {warnings.length > 0 ? <MetaChip>{warnings.length} warning{warnings.length === 1 ? "" : "s"}</MetaChip> : null}
      <MetaChip>Request {requestId.slice(0, 8)}</MetaChip>
    </div>
  );
}