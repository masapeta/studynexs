"use client";

import { X, ShieldCheck, AlertTriangle, ArrowRight } from "lucide-react";
import type { WorkspaceResponse } from "@/lib/workspace-types";
import type { WorkspaceActionDef } from "@/lib/workspace-actions";
import { verificationLabel } from "@/components/teaching/TeacherWorkspaceBlockRenderer";

export interface WorkflowPanelState {
  action: WorkspaceActionDef;
  status: "running" | "verified" | "coming_soon" | "error";
  response?: WorkspaceResponse | null;
  error?: string;
}

interface Step {
  label: string;
  meta?: string;
  state: "done" | "active" | "todo";
}

function stepsFor(state: WorkflowPanelState): Step[] {
  const base: Step[] = [
    { label: "Understand request", meta: state.action.label, state: "done" },
    { label: "Select governed tool", meta: "Deterministic service", state: "done" },
  ];
  if (state.status === "running") {
    base.push({ label: "Verify records", meta: "Checking source systems…", state: "active" });
    base.push({ label: "Result", state: "todo" });
  } else if (state.status === "verified") {
    base.push({ label: "Verify records", meta: "Verified against source systems", state: "done" });
    base.push({ label: "Result", meta: "Ready — review below", state: "active" });
  } else if (state.status === "coming_soon") {
    base.push({ label: "Verify records", meta: "Tool not yet enabled", state: "todo" });
    base.push({ label: "Result", state: "todo" });
  } else {
    base.push({ label: "Verify records", meta: state.error || "Could not complete", state: "active" });
    base.push({ label: "Result", state: "todo" });
  }
  return base;
}

export function WorkflowPanel({
  state,
  onClose,
}: {
  state: WorkflowPanelState;
  onClose: () => void;
}) {
  const steps = stepsFor(state);
  const verification = state.response?.verification;

  return (
    <aside className="sn-ws-panel" aria-label="Workflow panel">
      <div className="sn-ws-panel__head">
        <span className="sn-ws-panel__title">{state.action.label}</span>
        <button type="button" className="sn-ws-panel__close" onClick={onClose} aria-label="Close workflow panel">
          <X size={16} />
        </button>
      </div>

      <div className="sn-ws-panel__body">
        {/* Steps */}
        <section>
          <div className="sn-ws-panel__section-label">Workflow</div>
          <div className="sn-ws-steps">
            {steps.map((step, i) => (
              <div
                key={step.label}
                className={`sn-ws-step${step.state === "done" ? " sn-ws-step--done" : ""}${
                  step.state === "active" ? " sn-ws-step--active" : ""
                }`}
              >
                <div className="sn-ws-step__rail">
                  <span className="sn-ws-step__dot">{step.state === "done" ? "✓" : i + 1}</span>
                  {i < steps.length - 1 ? <span className="sn-ws-step__line" /> : null}
                </div>
                <div className="sn-ws-step__body">
                  <div className="sn-ws-step__label">{step.label}</div>
                  {step.meta ? <div className="sn-ws-step__meta">{step.meta}</div> : null}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Verification */}
        {verification ? (
          <section>
            <div className="sn-ws-panel__section-label">Verification</div>
            <div
              className="card"
              style={{ margin: 0, padding: 14, display: "flex", gap: 10, alignItems: "flex-start" }}
            >
              <ShieldCheck size={18} style={{ color: "var(--success)", flexShrink: 0, marginTop: 1 }} />
              <div>
                <div style={{ fontWeight: 700, fontSize: 13, color: "var(--text-primary)" }}>
                  {verificationLabel(verification)}
                </div>
                {verification.source_systems?.length ? (
                  <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 3 }}>
                    Sources: {verification.source_systems.join(", ")}
                  </div>
                ) : null}
                {verification.checked_at ? (
                  <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 2 }}>
                    Checked {new Date(verification.checked_at).toLocaleString()}
                  </div>
                ) : null}
              </div>
            </div>
          </section>
        ) : null}

        {/* Coming soon governed notice */}
        {state.status === "coming_soon" ? (
          <section>
            <div
              className="card"
              style={{
                margin: 0,
                padding: 14,
                display: "flex",
                gap: 10,
                alignItems: "flex-start",
                background: "var(--warning-light)",
                border: "1px solid color-mix(in srgb, var(--warning) 30%, transparent)",
              }}
            >
              <AlertTriangle size={18} style={{ color: "var(--warning)", flexShrink: 0, marginTop: 1 }} />
              <div>
                <div style={{ fontWeight: 700, fontSize: 13, color: "var(--text-primary)" }}>
                  Not yet available
                </div>
                <div style={{ fontSize: 12, color: "var(--text-secondary)", marginTop: 3 }}>
                  This governed action is defined but its backend tool is not enabled yet. It will
                  run against verified records once released — no results are shown until then.
                </div>
              </div>
            </div>
          </section>
        ) : null}

        {/* Error */}
        {state.status === "error" ? (
          <section>
            <div
              className="card"
              style={{
                margin: 0,
                padding: 14,
                background: "var(--danger-light)",
                border: "1px solid color-mix(in srgb, var(--danger) 30%, transparent)",
                color: "var(--danger)",
                fontSize: 13,
              }}
            >
              {state.error || "Could not complete this action."}
            </div>
          </section>
        ) : null}

        {/* Next actions from response */}
        {state.response?.actions?.length ? (
          <section>
            <div className="sn-ws-panel__section-label">Next actions</div>
            <div style={{ display: "grid", gap: 8 }}>
              {state.response.actions.map((a) => (
                <div
                  key={`${a.href}:${a.label}`}
                  className="card"
                  style={{
                    margin: 0,
                    padding: "10px 12px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    gap: 8,
                    opacity: a.enabled ? 1 : 0.6,
                  }}
                >
                  <span style={{ fontSize: 13 }}>{a.label}</span>
                  <ArrowRight size={14} style={{ color: "var(--text-muted)" }} />
                </div>
              ))}
            </div>
          </section>
        ) : null}
      </div>
    </aside>
  );
}
