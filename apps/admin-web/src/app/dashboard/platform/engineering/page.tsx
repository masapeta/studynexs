"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, getApiErrorMessage } from "@/lib/api";
import { PageHeaderCard } from "@/components/layout/PageHeaderCard";
import { PLATFORM } from "@/lib/dashboard-routes";

type CapabilityRow = {
  capability: string;
  status: string;
  verified: string;
  batch: string | null;
  module?: string;
};

type ModuleDeps = {
  satisfied: string[];
  pending: string[];
};

type ModuleRow = {
  id: string;
  name: string;
  status: string;
  verified: string;
  batch?: number;
  doc: string;
  depends_on?: ModuleDeps;
};

type NextMilestone = {
  batch?: number;
  title?: string;
  summary?: string;
  estimated_days?: number;
  dependencies_blocking?: string[];
  dependencies_satisfied?: string[];
  dependencies_optional?: string[];
};

type EngineeringStatus = {
  architecture_version: string;
  updated_at: string;
  last_engineering_batch?: number;
  branch: string;
  last_commit: string;
  last_completed_batch: string | null;
  current_batch: string | null;
  next_batch: string | null;
  next_milestone?: NextMilestone;
  tests: { passed?: number; skipped?: number; last_run?: string; verified?: boolean };
  providers: Record<string, string>;
  capability_matrix: CapabilityRow[];
  modules: ModuleRow[];
  doc_links: Record<string, string>;
  runtime: { git_commit?: string; git_branch?: string; engineering_dir?: string };
};

function statusIcon(status: string): string {
  switch (status) {
    case "complete":
      return "✅";
    case "in_progress":
      return "🟡";
    case "planned":
      return "🔴";
    default:
      return "⬜";
  }
}

function verifiedLabel(v: string): string {
  switch (v) {
    case "tests_passing":
      return "Tests passing";
    case "integration_pending":
      return "Integration pending";
    case "partial":
      return "Partial";
    case "not_started":
      return "Not started";
    default:
      return v.replace(/_/g, " ");
  }
}

export default function EngineeringDashboardPage() {
  const [data, setData] = useState<EngineeringStatus | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api("/api/v1/platform/engineering-status")
      .then((r) => setData(r.data))
      .catch((e) => setError(getApiErrorMessage(e, "Failed to load engineering status")))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="card" style={{ padding: 40, textAlign: "center" }}>
        <div className="spinner" style={{ margin: "0 auto" }} />
      </div>
    );
  }

  if (error || !data) {
    return <div className="card sn-inline-alert sn-inline-alert--error">{error || "No data"}</div>;
  }

  const commit = data.runtime?.git_commit || data.last_commit;
  const branch = data.runtime?.git_branch || data.branch;
  const next = data.next_milestone;

  return (
    <>
      <PageHeaderCard
        title="Engineering Dashboard"
        subtitle="Capability matrix · verification state · dependencies · admin only"
      >
        <Link href={PLATFORM.root} className="btn btn-ghost gw-btn-sm">
          Platform hub
        </Link>
      </PageHeaderCard>

      <div className="card sn-inline-alert" style={{ marginBottom: 16, fontSize: 13 }}>
        <strong>Source of truth:</strong> If this dashboard disagrees with the code, the{" "}
        <strong>implementation wins</strong>. Verify with tests, then update{" "}
        <code>docs/engineering/*.json</code> and <code>PLATFORM_STATUS.md</code>.
      </div>

      <div className="card" style={{ padding: 20, marginBottom: 20 }}>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 16 }}>
          <div>
            <div className="stat-label">Architecture version</div>
            <div style={{ fontWeight: 700, fontSize: 20 }}>v{data.architecture_version}</div>
          </div>
          <div>
            <div className="stat-label">Last updated</div>
            <div style={{ fontWeight: 600 }}>{data.updated_at}</div>
          </div>
          <div>
            <div className="stat-label">Engineering batch</div>
            <div style={{ fontWeight: 600 }}>{data.last_engineering_batch ?? "—"}</div>
          </div>
          <div>
            <div className="stat-label">Git</div>
            <div style={{ fontWeight: 700, fontFamily: "monospace" }}>{commit}</div>
            <div style={{ fontSize: 12, color: "var(--text-muted)" }}>{branch}</div>
          </div>
          <div>
            <div className="stat-label">Tests</div>
            <div style={{ fontWeight: 600 }}>
              {data.tests.passed ?? "—"} passed
              {data.tests.skipped != null ? ` · ${data.tests.skipped} skipped` : ""}
            </div>
            <div style={{ fontSize: 12, color: "var(--text-muted)" }}>
              {data.tests.verified ? "Verified" : "Unverified"} · {data.tests.last_run || "—"}
            </div>
          </div>
        </div>
      </div>

      {next && (
        <div className="card" style={{ padding: 20, marginBottom: 20, borderLeft: "4px solid var(--primary)" }}>
          <h3 style={{ margin: "0 0 12px", fontSize: 16 }}>Next milestone</h3>
          <div style={{ fontWeight: 700, marginBottom: 6 }}>
            Batch {next.batch} — {next.title}
          </div>
          <p style={{ margin: "0 0 12px", fontSize: 14, color: "var(--text-muted)" }}>{next.summary}</p>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 16, fontSize: 13 }}>
            <span>Estimated: <strong>{next.estimated_days ?? "—"} days</strong></span>
            <span>
              Blocking deps:{" "}
              <strong>{(next.dependencies_blocking?.length ?? 0) === 0 ? "None" : next.dependencies_blocking?.join(", ")}</strong>
            </span>
          </div>
          {(next.dependencies_satisfied?.length ?? 0) > 0 && (
            <div style={{ marginTop: 10, fontSize: 13 }}>
              Satisfied: {next.dependencies_satisfied?.join(" · ")}
            </div>
          )}
          {(next.dependencies_optional?.length ?? 0) > 0 && (
            <div style={{ marginTop: 4, fontSize: 13, color: "var(--text-muted)" }}>
              Optional: {next.dependencies_optional?.join(" · ")}
            </div>
          )}
        </div>
      )}

      <div className="card" style={{ padding: 20, marginBottom: 20 }}>
        <h3 style={{ margin: "0 0 12px", fontSize: 16 }}>AI providers</h3>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 12, fontSize: 14 }}>
          <span>LLM default: <strong>{data.providers.llm_default}</strong></span>
          <span>Embeddings: <strong>{data.providers.embedding_provider}</strong> ({data.providers.embedding_model})</span>
          <span>Vector DB: <strong>{data.providers.vector_store}</strong></span>
        </div>
      </div>

      <div className="card" style={{ padding: 0, overflow: "hidden", marginBottom: 20 }}>
        <div style={{ padding: "14px 20px", borderBottom: "1px solid var(--border)", fontWeight: 700 }}>
          Capability matrix
        </div>
        <table className="data-table">
          <thead>
            <tr>
              <th>Capability</th>
              <th>Status</th>
              <th>Verified</th>
              <th>Batch</th>
              <th>Module</th>
            </tr>
          </thead>
          <tbody>
            {data.capability_matrix.map((row) => (
              <tr key={row.capability}>
                <td>{row.capability}</td>
                <td>{statusIcon(row.status)} {row.status.replace("_", " ")}</td>
                <td>{verifiedLabel(row.verified)}</td>
                <td>{row.batch || "—"}</td>
                <td style={{ fontFamily: "monospace", fontSize: 12 }}>{row.module || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card" style={{ padding: 0, overflow: "hidden" }}>
        <div style={{ padding: "14px 20px", borderBottom: "1px solid var(--border)", fontWeight: 700 }}>
          Modules & dependencies
        </div>
        <table className="data-table">
          <thead>
            <tr>
              <th>Module</th>
              <th>Status</th>
              <th>Verified</th>
              <th>Satisfied deps</th>
              <th>Pending deps</th>
            </tr>
          </thead>
          <tbody>
            {data.modules.map((m) => (
              <tr key={m.id}>
                <td style={{ fontWeight: 600 }}>{m.name}</td>
                <td>{statusIcon(m.status)} {m.status.replace("_", " ")}</td>
                <td>{verifiedLabel(m.verified)}</td>
                <td style={{ fontSize: 12 }}>{m.depends_on?.satisfied?.join(", ") || "—"}</td>
                <td style={{ fontSize: 12 }}>{m.depends_on?.pending?.join(", ") || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p style={{ marginTop: 16, fontSize: 13, color: "var(--text-muted)" }}>
        Data: <code>{data.runtime?.engineering_dir || "docs/engineering/"}</code> · Markdown:{" "}
        <code>docs/PLATFORM_STATUS.md</code>
      </p>
    </>
  );
}
