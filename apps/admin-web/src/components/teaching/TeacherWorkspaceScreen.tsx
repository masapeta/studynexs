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
      <div className="flex h-full w-full gap-5 overflow-hidden">
        {/* Left: Chat & Input (1/3 Width) */}
        <section className="flex w-1/3 flex-col gap-5 overflow-y-auto px-6 py-8">
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
            <Sparkles size={16} />
            <strong>Bounded teacher workspace</strong>
          </div>
          <p style={{ color: "var(--text-secondary)", fontSize: 14, margin: 0 }}>
            Ask for a student's learning evidence to orchestrate backend checks and reveal the action canvas.
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
                className="btn btn-accent"
                style={{ padding: "8px 16px", borderRadius: 8, fontWeight: 600 }}
              >
                {submitting ? "Analyzing..." : "Analyze"}
              </button>
            </div>
          </form>
          {error && <p style={{ color: "var(--danger)" }}>{error}</p>}
          {response && (
            <div className="pt-6">
              <TeacherWorkspaceResponseMeta 
                verification={response.verification} 
                warnings={response.warnings?.map(w => w.detail) || []}
                requestId={response.request_id}
              />
            </div>
          )}
        </section>

        {/* Right: Dynamic Action Canvas (2/3 Width) */}
        <section className="h-full w-2/3 border-l border-line bg-surface/50 p-8 overflow-y-auto">
          <div className="flex h-full w-full items-start justify-center">
            {response ? (
              <div className="w-full">
                <TeacherWorkspaceBlockRenderer blocks={response.blocks} />
              </div>
            ) : (
              <div className="text-muted text-center pt-20">
                <p>Orchestrator output and interactive Action Cards will appear here.</p>
              </div>
            )}
          </div>
        </section>
      </div>
    </PageShell>
  );
}