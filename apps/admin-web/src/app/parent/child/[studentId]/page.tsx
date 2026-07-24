"use client";

import { FormEvent, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { CalendarCheck, MessageSquare, ShieldCheck, Sparkles, Target, Wallet } from "lucide-react";
import PortalShell from "@/components/PortalShell";
import { Card, SectionHeader, StatTile } from "@/components/ui/kit";
import { PARENT_NAV } from "@/lib/portal-nav";
import { api, getApiErrorMessage } from "@/lib/api";
import type { ParentChildProgress } from "@/lib/portal-types";

type ParentBriefing = {
  summary: string;
  focus_areas: {
    topic: string;
    subject_name: string;
    mastery_pct?: number;
    evidence_reason?: string;
  }[];
  home_tips: string[];
  encouragement: string;
  grounded: boolean;
  fallback: boolean;
  source_count: number;
  evidence_reason: string;
  evidence_summary: string;
  mastery_topic?: string | null;
};

type ParentAnswer = {
  answer: string;
  home_tips: string[];
  grounded: boolean;
  fallback: boolean;
  source_count: number;
  evidence_reason: string;
  evidence_summary: string;
};

function formatDate(iso: string | null | undefined): string {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleDateString("en-IN", {
      day: "numeric",
      month: "short",
      year: "numeric",
    });
  } catch {
    return "";
  }
}

function EvidenceBadge({ verified, label }: { verified: boolean; label: string }) {
  return (
    <span
      data-testid={label === "briefing" ? "parent-evidence-status" : undefined}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 5,
        borderRadius: 999,
        padding: "4px 9px",
        fontSize: 11,
        fontWeight: 700,
        color: verified ? "var(--success)" : "var(--text-muted)",
        background: verified
          ? "rgba(16,185,129,0.10)"
          : "var(--surface-muted, rgba(0,0,0,0.04))",
      }}
    >
      <ShieldCheck size={13} />
      {verified ? (label === "answer" ? "Grounded response" : "Evidence verified") : "Evidence pending"}
    </span>
  );
}

export default function ParentChildPage() {
  const params = useParams();
  const studentId = params.studentId as string;
  const [progress, setProgress] = useState<ParentChildProgress | null>(null);
  const [briefing, setBriefing] = useState<ParentBriefing | null>(null);
  const [briefingLoading, setBriefingLoading] = useState(true);
  const [question, setQuestion] = useState("");
  const [copilotAnswer, setCopilotAnswer] = useState<ParentAnswer | null>(null);
  const [asking, setAsking] = useState(false);
  const [error, setError] = useState("");
  const [copilotError, setCopilotError] = useState("");

  useEffect(() => {
    if (!studentId) return;
    api<{ data: ParentChildProgress }>(`/api/v1/portal/child/${studentId}/progress`)
      .then((res) => setProgress(res.data))
      .catch((e) => setError(getApiErrorMessage(e, "Failed to load child")));
  }, [studentId]);

  useEffect(() => {
    if (!studentId) return;
    api<{ data: ParentBriefing }>(`/api/v1/parent-copilot/students/${studentId}/briefing`)
      .then((res) => setBriefing(res.data))
      .catch((e) => setCopilotError(getApiErrorMessage(e, "Could not load briefing")))
      .finally(() => setBriefingLoading(false));
  }, [studentId]);

  async function askCopilot(e: FormEvent) {
    e.preventDefault();
    if (!studentId || !question.trim()) return;
    setAsking(true);
    setCopilotError("");
    setCopilotAnswer(null);
    try {
      const res = await api<{ data: ParentAnswer }>(`/api/v1/parent-copilot/students/${studentId}/ask`, {
        method: "POST",
        body: JSON.stringify({ question: question.trim() }),
      });
      setCopilotAnswer(res.data);
    } catch (err) {
      setCopilotError(getApiErrorMessage(err, "Could not get an answer"));
    } finally {
      setAsking(false);
    }
  }

  const att = progress?.attendance_pct;
  const attTone = att == null ? "default" : att >= 75 ? "success" : att >= 50 ? "warning" : "danger";
  const feeTone = (progress?.fee_pending ?? 0) > 0 ? "danger" : "success";
  const weakTone = (progress?.weak_topic_count ?? 0) > 0 ? "warning" : "success";
  const briefingVerified = Boolean(briefing?.grounded && !briefing.fallback);
  const answerVerified = Boolean(copilotAnswer?.grounded && !copilotAnswer.fallback);

  return (
    <PortalShell title="Child profile" subtitle={progress?.name} nav={PARENT_NAV}>
      <Link href="/parent/children" style={{ fontSize: 13, marginBottom: 12, display: "inline-block" }}>
        ← All children
      </Link>
      {error && <p style={{ color: "var(--danger)" }}>{error}</p>}
      {!progress ? (
        <div className="spinner" style={{ margin: "40px auto" }} />
      ) : (
        <>
          <div style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 12 }}>
            {progress.class_label}
            {progress.roll_no ? ` · Roll ${progress.roll_no}` : ""}
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10, marginBottom: 16 }}>
            <StatTile icon={CalendarCheck} label="Attendance" tone={attTone} value={att != null ? `${att}%` : "—"} />
            <StatTile
              icon={Wallet}
              label="Fees due"
              tone={feeTone}
              value={progress.fee_pending > 0 ? `₹${progress.fee_pending.toLocaleString("en-IN")}` : "Paid"}
            />
            <StatTile
              icon={Target}
              label="Weak topics"
              tone={weakTone}
              value={progress.weak_topic_count ?? progress.weak_topics.length}
            />
          </div>

          <SectionHeader title="Parent Copilot" />
          <div style={{ marginBottom: 16 }}>
            <Card>
              <div data-testid="parent-learning-brief">
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
                  <Sparkles size={16} style={{ color: "var(--accent)" }} />
                  <span style={{ fontSize: 13, fontWeight: 700 }}>Learning briefing</span>
                  {briefing ? (
                    <span style={{ marginLeft: "auto" }}>
                      <EvidenceBadge verified={briefingVerified} label="briefing" />
                    </span>
                  ) : null}
                </div>
                {copilotError && !briefing && (
                  <p style={{ fontSize: 13, color: "var(--danger)", margin: "0 0 12px" }}>{copilotError}</p>
                )}
                {briefingLoading ? (
                  <div className="spinner" style={{ margin: "12px auto" }} />
                ) : briefing ? (
                  <>
                    <p style={{ margin: "0 0 12px", fontSize: 14, lineHeight: 1.55 }}>{briefing.summary}</p>
                    <div
                      style={{
                        border: "1px solid var(--border)",
                        borderRadius: 14,
                        padding: 12,
                        marginBottom: 12,
                        background: "var(--surface-muted, rgba(0,0,0,0.03))",
                      }}
                    >
                      <div style={{ fontSize: 12, fontWeight: 800, marginBottom: 4 }}>
                        Why this recommendation?
                      </div>
                      <p style={{ margin: 0, fontSize: 13, lineHeight: 1.45, color: "var(--text-secondary)" }}>
                        {briefing.evidence_reason ||
                          "Based on your child's latest learning evidence in StudyNexs."}
                      </p>
                      {briefing.evidence_summary ? (
                        <p style={{ margin: "6px 0 0", fontSize: 12, color: "var(--text-muted)" }}>
                          {briefing.evidence_summary}
                        </p>
                      ) : null}
                    </div>
                    {briefing.focus_areas.length > 0 && (
                      <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 12 }}>
                        {briefing.focus_areas.slice(0, 4).map((area) => (
                          <span
                            key={`${area.subject_name}-${area.topic}`}
                            style={{
                              fontSize: 12,
                              padding: "4px 10px",
                              borderRadius: 999,
                              background: "var(--surface-muted, rgba(0,0,0,0.04))",
                            }}
                          >
                            {area.subject_name}: {area.topic}
                            {area.mastery_pct != null ? ` · ${Math.round(area.mastery_pct)}%` : ""}
                          </span>
                        ))}
                      </div>
                    )}
                    {briefing.home_tips.length > 0 && (
                      <div data-testid="parent-home-support">
                        <div style={{ fontSize: 12, fontWeight: 800, marginBottom: 6 }}>
                          How to help at home
                        </div>
                        <ul style={{ margin: "0 0 10px", paddingLeft: 18, fontSize: 13, lineHeight: 1.5 }}>
                          {briefing.home_tips.map((tip) => (
                            <li key={tip}>{tip}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {briefing.encouragement ? (
                      <p style={{ margin: 0, fontSize: 13, color: "var(--text-muted)", fontStyle: "italic" }}>
                        {briefing.encouragement}
                      </p>
                    ) : null}
                  </>
                ) : (
                  <p style={{ fontSize: 13, color: "var(--text-muted)", margin: 0 }}>
                    Briefing will appear once your child has mastery data from marked exams.
                  </p>
                )}
              </div>

              <form
                onSubmit={askCopilot}
                style={{ marginTop: 16, paddingTop: 16, borderTop: "1px solid var(--border)" }}
              >
                <label
                  htmlFor="parent-copilot-question"
                  style={{ fontSize: 12, fontWeight: 700, color: "var(--text-muted)" }}
                >
                  Ask about your child&apos;s learning
                </label>
                <textarea
                  id="parent-copilot-question"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="How can I help at home with algebra this week?"
                  rows={2}
                  maxLength={800}
                  style={{ width: "100%", marginTop: 8, marginBottom: 8, resize: "vertical" }}
                />
                <button type="submit" className="btn btn-primary" disabled={asking || !question.trim()}>
                  {asking ? "Thinking…" : "Ask"}
                </button>
                {copilotAnswer ? (
                  <div data-testid="parent-copilot-answer" style={{ marginTop: 12, fontSize: 14, lineHeight: 1.5 }}>
                    <div style={{ marginBottom: 8 }}>
                      <EvidenceBadge verified={answerVerified} label="answer" />
                    </div>
                    <p style={{ margin: 0 }}>{copilotAnswer.answer}</p>
                    {copilotAnswer.evidence_reason ? (
                      <p style={{ margin: "6px 0 0", fontSize: 12, color: "var(--text-muted)" }}>
                        {copilotAnswer.evidence_reason}
                      </p>
                    ) : null}
                    {copilotAnswer.home_tips.length > 0 && (
                      <ul style={{ marginTop: 8, paddingLeft: 18, fontSize: 13, color: "var(--text-muted)" }}>
                        {copilotAnswer.home_tips.map((tip) => (
                          <li key={tip}>{tip}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                ) : null}
              </form>
            </Card>
          </div>

          <SectionHeader title="Weak topics" />
          <Card>
            {progress.weak_topics.length === 0 ? (
              <p style={{ fontSize: 13, color: "var(--text-muted)", margin: 0 }}>
                No weak topics yet — appears after marked exams.
              </p>
            ) : (
              <ul style={{ margin: 0, paddingLeft: 18, fontSize: 14 }}>
                {progress.weak_topics.map((topic) => (
                  <li key={`${topic.subject_name}-${topic.topic}`} style={{ marginBottom: 6 }}>
                    <span style={{ fontWeight: 600 }}>{topic.subject_name}</span>: {topic.topic_display}{" "}
                    <span style={{ color: "var(--text-muted)" }}>({Math.round(topic.mastery_pct)}%)</span>
                  </li>
                ))}
              </ul>
            )}
          </Card>

          <SectionHeader title="Teacher feedback" />
          {progress.feedbacks.length === 0 ? (
            <Card>
              <p style={{ fontSize: 13, color: "var(--text-muted)", margin: 0 }}>
                No teacher feedback shared yet. You&apos;ll see notes here when teachers notify you about learning
                gaps.
              </p>
            </Card>
          ) : (
            progress.feedbacks.map((feedback, index) => (
              <div key={`${feedback.topic}-${feedback.notified_at ?? index}`} style={{ marginBottom: 10 }}>
                <Card>
                  <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 6 }}>
                    <MessageSquare size={15} style={{ color: "var(--accent)" }} />
                    <span style={{ fontWeight: 700, fontSize: 14 }}>
                      {feedback.subject_name} · {feedback.topic_display}
                    </span>
                    {feedback.notified_at && (
                      <span style={{ marginLeft: "auto", fontSize: 12, color: "var(--text-muted)" }}>
                        {formatDate(feedback.notified_at)}
                      </span>
                    )}
                  </div>
                  <p style={{ margin: 0, fontSize: 14, lineHeight: 1.5, color: "var(--text-secondary)" }}>
                    {feedback.narrative}
                  </p>
                </Card>
              </div>
            ))
          )}
        </>
      )}
    </PortalShell>
  );
}
