"use client";

import { useState } from "react";
import { Sparkles } from "lucide-react";
import { PageShell } from "@/components/layout/PageShell";
import { getApiErrorMessage } from "@/lib/api";
import { createWorkspaceTurn } from "@/lib/workspace-client";
import type { WorkspaceResponse } from "@/lib/workspace-types";
import {
  TeacherWorkspaceBlockRenderer,
  TeacherWorkspaceResponseMeta,
} from "@/components/teaching/TeacherWorkspaceBlockRenderer";

const STARTER_PROMPTS = [
  "Show learning evidence for Aarav in class 7A.",
  "Find student Riya and summarize her weak concepts.",
  "Show recent assessment evidence for admission number 24017.",
];

export function TeacherWorkspaceScreen() {
  const [text, setText] = useState(STARTER_PROMPTS[0]);
  const [response, setResponse] = useState<WorkspaceResponse | null>(null);
  const [error, setError] = useState<string>("");
  const [submitting, setSubmitting] = useState(false);

  async function submitTurn(nextText?: string) {
    const requestText = (nextText ?? text).trim();
    if (!requestText) {
      setError("Enter a student request before running the workspace.");
      return;
    }

    setSubmitting(true);
    setError("");
    try {
      const nextResponse = await createWorkspaceTurn({ mode: "read", text: requestText });
      setResponse(nextResponse);
    } catch (err) {
      setError(getApiErrorMessage(err, "Teacher Copilot could not complete that read request."));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <PageShell
      title="Teacher Copilot"
      subtitle="Read-only learning evidence for students in your teaching scope, grounded in existing school records."
      action={<span className="sn-filter-pill">Phase 1 · Agentic Canvas</span>}
    >
      <div
        style={{
          display: "grid",
          gap: 20,
          gridTemplateColumns: "minmax(280px, 1fr) minmax(0, 1.6fr)",
          alignItems: "start",
        }}
      >
        {/* Left: chat & input */}
        <section
          className="card"
          style={{ margin: 0, padding: 24, display: "flex", flexDirection: "column", gap: 16 }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
            <Sparkles size={16} />
            <strong>Bounded teacher workspace</strong>
          </div>
          <p style={{ color: "var(--text-secondary)", fontSize: 14, margin: 0 }}>
            Ask for a student&apos;s learning evidence to orchestrate backend checks and reveal the action canvas.
          </p>
          <form
            onSubmit={(event) => {
              event.preventDefault();
              void submitTurn();
            }}
            style={{ display: "grid", gap: 12 }}
          >
            <label htmlFor="teacher-workspace-input" style={{ fontWeight: 600 }}>
              Ask for a student learning evidence report
            </label>
            <textarea
              id="teacher-workspace-input"
              value={text}
              onChange={(event) => setText(event.target.value)}
              rows={4}
              maxLength={400}
              placeholder="Show learning evidence for a student in my class."
              style={{
                background: "color-mix(in srgb, var(--bg-card) 84%, transparent)",
                border: "1px solid var(--border)",
                borderRadius: 16,
                color: "var(--text-primary)",
                font: "inherit",
                minHeight: 120,
                padding: 14,
                resize: "vertical",
              }}
            />
            <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                {STARTER_PROMPTS.map((prompt) => (
                  <button
                    key={prompt}
                    type="button"
                    className="btn btn-ghost sn-filter-pill"
                    onClick={() => {
                      setText(prompt);
                      void submitTurn(prompt);
                    }}
                  >
                    {prompt}
                  </button>
                ))}
              </div>
              <button
                type="submit"
                disabled={submitting}
                className="btn btn-primary"
                style={{ padding: "8px 16px", fontWeight: 600, width: "auto" }}
              >
                {submitting ? "Analyzing…" : "Analyze"}
              </button>
            </div>
          </form>
          {error && <p style={{ color: "var(--danger)" }}>{error}</p>}
          {response && (
            <div style={{ paddingTop: 8 }}>
              <TeacherWorkspaceResponseMeta
                verification={response.verification} 
                warnings={response.warnings?.map(w => w.detail) || []}
                requestId={response.request_id}
              />
            </div>
          )}
        </section>

        {/* Right: dynamic action canvas */}
        <section className="card" style={{ margin: 0, padding: 24, minHeight: 360 }}>
          {response ? (
            <div style={{ display: "grid", gap: 16 }}>
              <TeacherWorkspaceBlockRenderer blocks={response.blocks} />
            </div>
          ) : (
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                textAlign: "center",
                color: "var(--text-muted)",
                minHeight: 300,
                gap: 8,
              }}
            >
              <Sparkles size={22} style={{ color: "var(--accent)" }} />
              <p style={{ margin: 0 }}>
                Orchestrator output and interactive action cards will appear here.
              </p>
            </div>
          )}
        </section>
      </div>
    </PageShell>
  );
}