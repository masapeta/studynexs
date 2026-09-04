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
      action={<span className="sn-filter-pill">Phase 0 · Read mode</span>}
    >
      <div style={{ display: "grid", gap: 20 }}>
        <section className="sn-workspace sn-workspace--primary" style={{ padding: 20 }}>
          <div className="sn-workspace-zone" style={{ display: "grid", gap: 16 }}>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
                <Sparkles size={16} />
                <strong>Bounded teacher workspace</strong>
              </div>
              <p style={{ color: "var(--text-secondary)", fontSize: 14, margin: 0 }}>
                This first slice only resolves a student, reads deterministic learning evidence,
                and offers safe navigation targets.
              </p>
            </div>

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
                      disabled={submitting}
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
                <button type="submit" className="btn btn-primary" disabled={submitting}>
                  {submitting ? "Loading evidence..." : "Run workspace"}
                </button>
              </div>
            </form>
          </div>
        </section>

        {error ? (
          <section className="sn-workspace sn-workspace--secondary" style={{ padding: 18 }}>
            <div className="sn-workspace-zone" style={{ color: "var(--danger)", display: "grid", gap: 8 }}>
              <strong>Workspace request failed</strong>
              <span style={{ color: "var(--text-secondary)", fontSize: 14 }}>{error}</span>
            </div>
          </section>
        ) : null}

        {response ? (
          <>
            <section className="sn-workspace sn-workspace--primary" style={{ padding: 20 }}>
              <div className="sn-workspace-zone" style={{ display: "grid", gap: 12 }}>
                <div>
                  <h2 className="sn-page-header-card__title" style={{ marginBottom: 6 }}>
                    {response.message.title}
                  </h2>
                  <p style={{ color: "var(--text-secondary)", fontSize: 15, margin: 0 }}>
                    {response.message.summary}
                  </p>
                </div>
                <TeacherWorkspaceResponseMeta
                  verification={response.verification}
                  warnings={response.warnings.map((warning) => warning.detail)}
                  requestId={response.request_id}
                />
                {response.warnings.length > 0 ? (
                  <div className="sn-workspace-zone" style={{ display: "grid", gap: 8 }}>
                    {response.warnings.map((warning) => (
                      <div key={warning.code} className="sn-filter-pill" style={{ padding: "12px 14px" }}>
                        <strong style={{ display: "block", marginBottom: 4 }}>{warning.code}</strong>
                        <span style={{ color: "var(--text-secondary)", fontSize: 14 }}>
                          {warning.detail}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : null}
              </div>
            </section>

            <div style={{ display: "grid", gap: 16 }} aria-live="polite">
              {response.blocks.map((block) => (
                <TeacherWorkspaceBlockRenderer key={block.id} block={block} />
              ))}
            </div>
          </>
        ) : (
          <section className="sn-workspace sn-workspace--secondary" style={{ padding: 18 }}>
            <div className="sn-workspace-zone" style={{ display: "grid", gap: 8 }}>
              <strong>Ready for a bounded read request</strong>
              <p style={{ color: "var(--text-secondary)", fontSize: 14, margin: 0 }}>
                Ask for one student at a time. This surface will not mutate records, generate
                new academic content, or perform workflow actions in this slice.
              </p>
            </div>
          </section>
        )}
      </div>
    </PageShell>
  );
}