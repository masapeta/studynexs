"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Sparkles } from "lucide-react";
import type { AssistantBlock } from "@/lib/assistant-client";
import {
  actionResultSucceeded,
  fmt,
  isSupportedActionEndpoint,
  mixedChildren,
  workflowStateLabel,
} from "./assistant-block-logic";

/** A governed chat action the user may confirm. `onAction` runs it and appends the real result. */
export interface AssistantActionRequest {
  endpoint: string;
  payload?: Record<string, unknown>;
  label: string;
}

/**
 * A confirm/approve control for a governed action. It POSTs ONLY through the caller's `onAction`
 * (which validates the endpoint + runs the authenticated client), shows a pending state, blocks
 * repeat clicks, and never implies success — on failure it surfaces the error and stays clickable.
 * An unsupported endpoint renders as an inert label (no request is possible).
 */
function ActionButton({
  request,
  onAction,
  variant = "primary",
}: {
  request: AssistantActionRequest;
  onAction?: (req: AssistantActionRequest) => Promise<void>;
  variant?: "primary" | "outline";
}) {
  const [pending, setPending] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const supported = isSupportedActionEndpoint(request.endpoint);
  if (!supported || !onAction) {
    // Not actionable from chat — show the label as plain text, never a dead button that posts.
    return <span style={{ fontSize: 13, color: "var(--text-secondary)" }}>{request.label}</span>;
  }

  const run = async () => {
    if (pending || done) return; // anti double-click / double-submit
    setPending(true);
    setError(null);
    try {
      await onAction(request);
      setDone(true); // success is driven by onAction resolving, i.e. the backend confirming
    } catch (e) {
      setError(e instanceof Error ? e.message : "That action couldn't be completed.");
    } finally {
      setPending(false);
    }
  };

  return (
    <span style={{ display: "inline-flex", flexDirection: "column", gap: 4 }}>
      <button
        type="button"
        className={variant === "primary" ? "btn btn-primary" : "btn btn-outline"}
        style={{ width: "auto", padding: "7px 14px", opacity: done ? 0.6 : 1 }}
        onClick={run}
        disabled={pending || done}
        aria-busy={pending}
      >
        {pending ? "Working…" : done ? "Done" : request.label}
      </button>
      {error ? (
        <span style={{ fontSize: 12, color: "var(--danger)" }} role="alert">
          {error}
        </span>
      ) : null}
    </span>
  );
}

/** Renders one assistant result block. onSelect feeds a clarify choice back as a turn;
 * onAction runs a governed action/workflow endpoint and appends the confirmed result. */
export function AssistantBlockView({
  block,
  onSelect,
  onAction,
  onNavigate,
}: {
  block: AssistantBlock;
  onSelect?: (text: string) => void;
  onAction?: (req: AssistantActionRequest) => Promise<void>;
  /** Keeps the conversation recoverable (record drawer / back chip). Defaults to a plain push. */
  onNavigate?: (href: string) => void;
}) {
  const router = useRouter();
  const go = (href: string) => (onNavigate ? onNavigate(href) : router.push(href));

  if (block.kind === "guide") {
    return (
      <div className="card" style={{ margin: 0, padding: 22 }}>
        <div style={{ display: "flex", alignItems: "flex-start", gap: 12, marginBottom: 14 }}>
          <span
            style={{
              display: "inline-flex",
              width: 36,
              height: 36,
              borderRadius: 10,
              alignItems: "center",
              justifyContent: "center",
              background: "var(--accent-50)",
              color: "var(--accent-dark)",
              flexShrink: 0,
            }}
          >
            <Sparkles size={18} />
          </span>
          <div>
            <div style={{ fontSize: 15, fontWeight: 700, color: "var(--text-primary)" }}>
              {block.title || "Here's where to look"}
            </div>
            {block.message ? (
              <p style={{ fontSize: 13, color: "var(--text-secondary)", marginTop: 3 }}>
                {block.message}
              </p>
            ) : null}
          </div>
        </div>
        {block.suggestions?.length ? (
          <div
            style={{
              display: "grid",
              gap: 8,
              gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))",
            }}
          >
            {block.suggestions.map((s) => (
              <button
                key={s.href}
                type="button"
                className="card"
                onClick={() => go(s.href)}
                style={{
                  margin: 0,
                  padding: "12px 14px",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  gap: 10,
                  cursor: "pointer",
                  textAlign: "left",
                }}
              >
                <span style={{ fontSize: 13, fontWeight: 600, color: "var(--text-primary)" }}>
                  {s.label}
                </span>
                <span style={{ color: "var(--text-muted)", fontSize: 12 }}>Open</span>
              </button>
            ))}
          </div>
        ) : null}
      </div>
    );
  }

  if (block.kind === "error") {
    return (
      <div
        className="card"
        style={{
          margin: 0,
          padding: 18,
          background: "var(--danger-light)",
          border: "1px solid color-mix(in srgb, var(--danger) 30%, transparent)",
          color: "var(--danger)",
          fontSize: 14,
        }}
      >
        {block.message || block.title || "Something went wrong."}
      </div>
    );
  }

  if (block.kind === "navigate") {
    return (
      <div
        className="card"
        style={{
          margin: 0,
          padding: 16,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 12,
        }}
      >
        <span style={{ fontSize: 14, color: "var(--text-primary)" }}>
          {block.title || "Opening"} {block.label}
        </span>
        {block.href ? (
          <button
            type="button"
            className="btn btn-primary"
            style={{ width: "auto", padding: "7px 14px" }}
            onClick={() => go(block.href!)}
          >
            Open
          </button>
        ) : null}
      </div>
    );
  }

  if (block.kind === "not_found") {
    return (
      <div className="card" style={{ margin: 0, padding: 18 }}>
        <div style={{ fontSize: 15, fontWeight: 700, color: "var(--text-primary)" }}>
          {block.title || "Nothing found"}
        </div>
        {block.message ? (
          <p style={{ fontSize: 13, color: "var(--text-secondary)", marginTop: 4 }}>
            {block.message}
          </p>
        ) : null}
      </div>
    );
  }

  if (block.kind === "mixed") {
    const children = mixedChildren(block);
    return (
      <div style={{ display: "grid", gap: 12 }}>
        {children.map((child, i) => (
          <AssistantBlockView
            key={i}
            block={child}
            onSelect={onSelect}
            onAction={onAction}
            onNavigate={onNavigate}
          />
        ))}
      </div>
    );
  }

  if (block.kind === "document") {
    return (
      <div className="card" style={{ margin: 0, padding: 22 }}>
        <div style={{ fontSize: 15, fontWeight: 800, color: "var(--text-primary)", marginBottom: 8 }}>
          {block.title || "From school policy"}
        </div>
        {block.message ? (
          <p style={{ fontSize: 14, color: "var(--text-primary)", lineHeight: 1.55 }}>
            {block.message}
          </p>
        ) : null}
        {block.citations?.length ? (
          <div style={{ marginTop: 14, display: "grid", gap: 6 }}>
            {block.citations.map((c, i) => (
              <div
                key={i}
                style={{
                  fontSize: 12,
                  color: "var(--text-muted)",
                  borderLeft: "2px solid var(--accent)",
                  paddingLeft: 10,
                }}
              >
                {c.title}
                {c.document_type ? ` · ${c.document_type}` : ""}
              </div>
            ))}
          </div>
        ) : null}
      </div>
    );
  }

  if (block.kind === "clarify") {
    return (
      <div className="card" style={{ margin: 0, padding: 22 }}>
        <div style={{ fontSize: 15, fontWeight: 700, color: "var(--text-primary)" }}>
          {block.title || "Which one do you mean?"}
        </div>
        {block.message ? (
          <p style={{ fontSize: 13, color: "var(--text-secondary)", marginTop: 4, marginBottom: 14 }}>
            {block.message}
          </p>
        ) : null}
        <div style={{ display: "grid", gap: 8 }}>
          {(block.options ?? []).map((o) => (
            <button
              key={o.id}
              type="button"
              className="card"
              onClick={() => onSelect?.(o.label)}
              style={{
                margin: 0,
                padding: "11px 14px",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                gap: 10,
                cursor: onSelect ? "pointer" : "default",
                textAlign: "left",
              }}
            >
              <span style={{ fontSize: 13, fontWeight: 600, color: "var(--text-primary)" }}>
                {o.label}
              </span>
              <span style={{ color: "var(--text-muted)", fontSize: 12 }}>Select</span>
            </button>
          ))}
        </div>
      </div>
    );
  }

  if (block.kind === "workflow") {
    const summary = block.summary ?? {};
    return (
      <div className="card" style={{ margin: 0, padding: 22 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
          <span style={{ fontSize: 15, fontWeight: 800, color: "var(--text-primary)" }}>
            {block.title || "Workflow"}
          </span>
          {block.workflow_state ? (
            <span
              style={{
                fontSize: 11,
                fontWeight: 700,
                color: "var(--accent-dark)",
                background: "var(--accent-50)",
                border: "1px solid color-mix(in srgb, var(--accent) 30%, transparent)",
                padding: "3px 9px",
                borderRadius: 999,
                textTransform: "capitalize",
              }}
            >
              {workflowStateLabel(block.workflow_state)}
            </span>
          ) : null}
        </div>
        {block.message ? (
          <p style={{ fontSize: 13, color: "var(--text-secondary)", marginTop: 2 }}>
            {block.message}
          </p>
        ) : null}
        {Object.keys(summary).length ? (
          <div style={{ marginTop: 12, display: "grid", gap: 4 }}>
            {Object.entries(summary).map(([k, v]) => (
              <div key={k} style={{ fontSize: 12, color: "var(--text-muted)" }}>
                <span style={{ textTransform: "capitalize" }}>{k.replace(/_/g, " ")}</span>:{" "}
                <span style={{ color: "var(--text-primary)" }}>{String(v ?? "—")}</span>
              </div>
            ))}
          </div>
        ) : null}
        {block.actions?.length ? (
          <div style={{ marginTop: 16, display: "flex", gap: 8, flexWrap: "wrap" }}>
            {block.actions.map((a, i) =>
              a.href ? (
                <button
                  key={i}
                  type="button"
                  className="btn btn-outline"
                  style={{ width: "auto", padding: "7px 14px" }}
                    onClick={() => go(a.href!)}
                >
                  {a.label}
                </button>
              ) : a.endpoint ? (
                <ActionButton
                  key={i}
                  request={{ endpoint: a.endpoint, label: a.label }}
                  onAction={onAction}
                  variant="outline"
                />
              ) : (
                <span key={i} style={{ fontSize: 13, color: "var(--text-secondary)" }}>
                  {a.label}
                </span>
              )
            )}
          </div>
        ) : null}
      </div>
    );
  }

  if (block.kind === "action_preview") {
    const preview = block.preview ?? {};
    const confirm = block.confirm_action;
    return (
      <div className="card" style={{ margin: 0, padding: 22 }}>
        <div style={{ fontSize: 15, fontWeight: 800, color: "var(--text-primary)", marginBottom: 6 }}>
          {block.title || "Review before confirming"}
        </div>
        {block.message ? (
          <p style={{ fontSize: 13, color: "var(--text-secondary)", marginBottom: 12 }}>
            {block.message}
          </p>
        ) : null}
        {Object.keys(preview).length ? (
          <div
            style={{
              display: "grid",
              gap: 6,
              padding: "12px 14px",
              borderRadius: 12,
              background: "var(--bg)",
              border: "1px solid var(--border)",
            }}
          >
            {Object.entries(preview).map(([k, v]) => (
              <div key={k} style={{ fontSize: 12, color: "var(--text-muted)" }}>
                <span style={{ textTransform: "capitalize" }}>{k.replace(/_/g, " ")}</span>:{" "}
                <span style={{ color: "var(--text-primary)" }}>{String(v ?? "—")}</span>
              </div>
            ))}
          </div>
        ) : null}
        {confirm?.endpoint ? (
          <div style={{ marginTop: 14, display: "flex", flexDirection: "column", gap: 8 }}>
            <ActionButton
              request={{
                endpoint: confirm.endpoint,
                payload: confirm.payload,
                label: confirm.label || "Confirm",
              }}
              onAction={onAction}
              variant="primary"
            />
            <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
              Nothing is changed until you confirm.
            </span>
          </div>
        ) : null}
      </div>
    );
  }

  if (block.kind === "action_result") {
    // Only show success when the backend actually confirms it (see assistant-block-logic).
    const succeeded = actionResultSucceeded(block);
    return (
      <div
        className="card"
        style={{
          margin: 0,
          padding: 18,
          background: succeeded ? "var(--success-light)" : "var(--bg)",
          border: `1px solid ${
            succeeded
              ? "color-mix(in srgb, var(--success) 30%, transparent)"
              : "var(--border)"
          }`,
          color: succeeded ? "var(--success)" : "var(--text-primary)",
          fontSize: 14,
        }}
      >
        {succeeded
          ? block.message || block.title || "Done."
          : block.message || block.title || "The action did not complete."}
      </div>
    );
  }

  // metrics + table share a header + source footer.
  return (
    <div className="card" style={{ margin: 0, padding: 22 }}>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 12,
          borderBottom: "1px solid var(--border)",
          paddingBottom: 14,
          marginBottom: 16,
        }}
      >
        <div>
          <h3 style={{ fontSize: 16, fontWeight: 800, color: "var(--text-primary)" }}>
            {block.title}
          </h3>
          {block.subtitle ? (
            <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 2 }}>
              {block.subtitle}
            </div>
          ) : null}
        </div>
        {block.kind === "table" ? (
          <span
            style={{
              fontSize: 11,
              fontWeight: 700,
              color: "var(--success)",
              background: "var(--success-light)",
              border: "1px solid color-mix(in srgb, var(--success) 30%, transparent)",
              padding: "4px 10px",
              borderRadius: 999,
            }}
          >
            {block.rows?.length ?? 0} result{(block.rows?.length ?? 0) === 1 ? "" : "s"}
          </span>
        ) : (
          <span
            style={{
              fontSize: 11,
              fontWeight: 700,
              color: "var(--success)",
              background: "var(--success-light)",
              border: "1px solid color-mix(in srgb, var(--success) 30%, transparent)",
              padding: "4px 10px",
              borderRadius: 999,
            }}
          >
            Verified
          </span>
        )}
      </div>

      {block.kind === "metrics" && (block.metrics?.length ?? 0) === 0 && block.message ? (
        <p style={{ fontSize: 14, color: "var(--text-secondary)" }}>{block.message}</p>
      ) : null}

      {block.kind === "metrics" && (block.metrics?.length ?? 0) > 0 ? (
        <div
          style={{
            display: "grid",
            gap: 12,
            gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
          }}
        >
          {(block.metrics ?? []).map((m) => (
            <div
              key={m.label}
              style={{
                border: "1px solid var(--border)",
                borderRadius: 12,
                padding: "14px 16px",
                background: "var(--bg)",
              }}
            >
              <div style={{ fontSize: 12, color: "var(--text-muted)" }}>{m.label}</div>
              <div style={{ fontSize: 22, fontWeight: 800, color: "var(--text-primary)" }}>
                {fmt(m.value, m.format)}
              </div>
            </div>
          ))}
        </div>
      ) : null}

      {block.kind === "table" ? (
        (block.rows?.length ?? 0) === 0 ? (
          <p style={{ fontSize: 14, color: "var(--text-secondary)" }}>
            {block.empty_message || "No results."}
          </p>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 520 }}>
              <thead>
                <tr>
                  {(block.columns ?? []).map((c) => (
                    <th
                      key={c.key}
                      style={{
                        textAlign: "left",
                        fontSize: 12,
                        fontWeight: 600,
                        color: "var(--text-muted)",
                        borderBottom: "1px solid var(--border)",
                        padding: "0 12px 10px 0",
                      }}
                    >
                      {c.label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(block.rows ?? []).map((row, i) => (
                  <tr key={i}>
                    {(block.columns ?? []).map((c, ci) => {
                      const text = c.format ? fmt(row[c.key], c.format) : String(row[c.key] ?? "—");
                      const href = ci === 0 && typeof row.href === "string" ? row.href : null;
                      return (
                        <td
                          key={c.key}
                          style={{
                            fontSize: 13,
                            color: "var(--text-primary)",
                            borderBottom:
                              "1px solid color-mix(in srgb, var(--border) 70%, transparent)",
                            padding: "10px 12px 10px 0",
                          }}
                        >
                          {href ? (
                            <button
                              type="button"
                              className="sn-asst-row-link"
                              data-record-href={href}
                              onClick={() => go(href)}
                            >
                              {text}
                            </button>
                          ) : (
                            text
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      ) : null}

      {block.source || block.href ? (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: 10,
            marginTop: 16,
            flexWrap: "wrap",
          }}
        >
          {block.source ? (
            <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
              Source: {block.source}
            </span>
          ) : (
            <span />
          )}
          {block.href ? (
            <button
              type="button"
              className="btn btn-outline"
              style={{ width: "auto", padding: "7px 14px" }}
              onClick={() => go(block.href!)}
            >
              {block.href_label ?? "Open"}
            </button>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
