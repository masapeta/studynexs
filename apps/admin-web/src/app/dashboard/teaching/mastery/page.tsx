"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, getApiErrorMessage } from "@/lib/api";
import { PageHeaderCard } from "@/components/layout/PageHeaderCard";
import { FilterPillBar } from "@/components/layout/FilterPillBar";
import { TEACHING } from "@/lib/dashboard-routes";
import { AI_INPUT, clampText, sanitizeAiText } from "@/lib/ai-input-limits";

const TABS = [
  { key: "pending_review", label: "Pending review" },
  { key: "approved", label: "Approved" },
  { key: "notified", label: "Sent" },
  { key: "dismissed", label: "Dismissed" },
] as const;

const REASON_LABELS: Record<string, string> = {
  below_class_avg: "Below class average",
  declining_trend: "Declining trend",
  absolute_floor: "Below 40%",
};

type ApiResponse<T> = {
  data: T;
  message?: string;
};

type MasteryHistory = {
  date?: string;
  title?: string;
  pct?: number | string;
};

type MasteryFlagEvidence = {
  student_name?: string;
  subject_name?: string;
  mastery_pct?: number;
  class_avg_pct?: number;
  trend?: string;
  assessments_count?: number;
  history?: MasteryHistory[];
};

type MasteryFlagRow = {
  id: string;
  student_name?: string;
  class_name?: string;
  class_id: string;
  subject_id: string;
  topic_display: string;
  severity: "high" | "medium" | string;
  status: "pending_review" | "approved" | "notified" | "dismissed" | string;
  reasons?: string[];
  evidence?: MasteryFlagEvidence;
  narrative?: string;
  dismissed_reason?: string;
};

type LearningEvidenceExam = {
  title: string;
  topic_pct?: number | string | null;
  question_paper_grounded?: boolean;
};

type LearningEvidenceChain = {
  curriculum_pack_ids?: string[];
  question_paper_ids?: string[];
  approved_evaluation_ids?: string[];
  mastery?: { mastery_pct: number };
  weak_concept_count?: number;
  grounded?: boolean;
  warnings?: string[];
  exams?: LearningEvidenceExam[];
};

type CreditsResponse = {
  user_credits_remaining?: number | null;
  credits_remaining?: number;
  purpose_costs?: { mastery_narrative?: number };
};

export default function MasteryFlagsPage() {
  const router = useRouter();
  const [tab, setTab] = useState<string>("pending_review");
  const [flags, setFlags] = useState<MasteryFlagRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState<string | null>(null);
  const [chainBusyId, setChainBusyId] = useState<string | null>(null);
  const [chains, setChains] = useState<Record<string, LearningEvidenceChain>>({});
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [credits, setCredits] = useState<CreditsResponse | null>(null);

  const load = useCallback((status: string) => {
    setLoading(true);
    api<ApiResponse<MasteryFlagRow[]>>(`/api/v1/mastery/flags?status=${status}`)
      .then((r) => setFlags(r.data || []))
      .catch((e) => setError(getApiErrorMessage(e, "Failed to load flags")))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    void Promise.resolve().then(() => {
      load(tab);
      setError("");
      api<CreditsResponse>("/api/v1/ai/credits").then(setCredits).catch(() => {});
    });
  }, [tab, load]);

  async function act(flag: MasteryFlagRow, action: "approve" | "dismiss" | "notify") {
    setBusyId(flag.id);
    setError("");
    try {
      if (action === "approve") {
        const cost = credits?.purpose_costs?.mastery_narrative ?? 1;
        const remaining = credits?.user_credits_remaining ?? credits?.credits_remaining;
        if (remaining !== undefined && remaining !== null && remaining < cost) {
          setError("Not enough AI credits remaining this month. Contact your class incharge or principal.");
          return;
        }
        const res = await api<ApiResponse<MasteryFlagRow>>(
          `/api/v1/mastery/flags/${flag.id}/approve`,
          { method: "POST" }
        );
        // Show the drafted note immediately for editing.
        setDrafts((d) => ({ ...d, [flag.id]: res.data.narrative || "" }));
        api<CreditsResponse>("/api/v1/ai/credits").then(setCredits).catch(() => {});
        setTab("approved");
      } else if (action === "dismiss") {
        const reason = window.prompt("Why dismiss? (optional - helps tune the alerts)") || undefined;
        await api(`/api/v1/mastery/flags/${flag.id}/dismiss`, {
          method: "POST",
          body: JSON.stringify({ reason }),
        });
        load(tab);
      } else {
        // Save any narrative edits before sending.
        const edited = drafts[flag.id];
        if (edited !== undefined && edited !== flag.narrative) {
          const narrative = sanitizeAiText(edited, AI_INPUT.masteryNarrativeMaxLength, "Note");
          await api(`/api/v1/mastery/flags/${flag.id}/narrative`, {
            method: "PUT",
            body: JSON.stringify({ narrative }),
          });
        }
        const res = await api<ApiResponse<MasteryFlagRow>>(
          `/api/v1/mastery/flags/${flag.id}/notify`,
          { method: "POST" }
        );
        alert(res.message || "Sent");
        load(tab);
      }
    } catch (e) {
      setError(getApiErrorMessage(e, "Action failed"));
    } finally {
      setBusyId(null);
    }
  }

  async function loadEvidenceChain(flag: MasteryFlagRow) {
    if (chains[flag.id]) return;
    setChainBusyId(flag.id);
    setError("");
    try {
      const res = await api<ApiResponse<LearningEvidenceChain>>(
        `/api/v1/mastery/flags/${flag.id}/evidence-chain`
      );
      setChains((current) => ({ ...current, [flag.id]: res.data }));
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to load evidence chain"));
    } finally {
      setChainBusyId(null);
    }
  }

  return (
    <>
      <PageHeaderCard
        title="Topic Mastery - Weakness Flags"
        subtitle="Raised by score rules, never by AI. Nothing reaches a parent without your approval."
      >
        <button className="btn btn-ghost sn-filter-pill" onClick={() => router.push(TEACHING.masteryDigest)}>
          Print digest
        </button>
      </PageHeaderCard>

      <FilterPillBar
        tabs={TABS.map((t) => ({ key: t.key, label: t.label }))}
        activeKey={tab}
        onChange={setTab}
        ariaLabel="Filter weakness flags by status"
      />

      {error && <div className="card" style={{ marginBottom: 16, padding: 12, color: "var(--danger)" }}>{error}</div>}

      {loading ? (
        <div className="card" style={{ padding: 40, textAlign: "center" }}><div className="spinner" style={{ margin: "0 auto" }} /></div>
      ) : flags.length === 0 ? (
        <div className="card" style={{ padding: 40, textAlign: "center", color: "var(--text-muted)" }}>
          {tab === "pending_review"
            ? "No flags waiting for review. Flags appear when topic-tagged marks show a student falling behind."
            : "Nothing here yet."}
        </div>
      ) : (
        flags.map((f) => {
          const ev = f.evidence || {};
          return (
            <div key={f.id} className="card" style={{ padding: 20, marginBottom: 16 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12, flexWrap: "wrap" }}>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                    <span style={{ fontWeight: 700 }}>{f.student_name || ev.student_name}</span>
                    <span style={{ color: "var(--text-muted)", fontSize: 13 }}>{f.class_name}</span>
                    <span className={`badge ${f.severity === "high" ? "badge-danger" : "badge-warning"}`}>
                      {f.severity === "high" ? "HIGH" : "MEDIUM"}
                    </span>
                    {(f.reasons || []).map((r: string) => (
                      <span key={r} className="badge badge-info">{REASON_LABELS[r] || r}</span>
                    ))}
                  </div>
                  <div style={{ marginTop: 6, fontSize: 14 }}>
                    <b>{ev.subject_name}</b> - {f.topic_display}
                  </div>
                </div>
                <button
                  className="btn btn-ghost"
                  style={btn}
                  onClick={() =>
                    router.push(
                      `${TEACHING.aiPapers}?class_id=${f.class_id}&subject_id=${f.subject_id}&topics=${encodeURIComponent(f.topic_display)}&difficulty=easy`
                    )
                  }
                >
                  Practice paper
                </button>
              </div>

              {/* Deterministic evidence — always shown, never just a verdict */}
              <div style={{ display: "flex", gap: 24, marginTop: 12, fontSize: 13, flexWrap: "wrap" }}>
                <span>Mastery: <b>{ev.mastery_pct}%</b></span>
                <span>Class avg: <b>{ev.class_avg_pct}%</b></span>
                <span>Trend: <b style={{ textTransform: "capitalize" }}>{ev.trend}</b></span>
                <span>Assessments: <b>{ev.assessments_count}</b></span>
              </div>
              {(ev.history || []).length > 0 && (
                <div style={{ marginTop: 8, fontSize: 12, color: "var(--text-secondary)" }}>
                  {(ev.history || []).map((h: MasteryHistory) => `${h.date} - ${h.title}: ${h.pct}%`).join("   |   ")}
                </div>
              )}

              <div style={{ marginTop: 12 }}>
                <button
                  className="btn btn-ghost"
                  style={btn}
                  disabled={chainBusyId === f.id}
                  onClick={() => loadEvidenceChain(f)}
                >
                  {chainBusyId === f.id ? "Loading evidence..." : chains[f.id] ? "Evidence chain loaded" : "View evidence chain"}
                </button>
              </div>
              {chains[f.id] && <EvidenceChainPanel chain={chains[f.id]} />}

              {/* Parent note (approved+) — editable until sent */}
              {(f.status === "approved" || f.status === "notified") && (
                <div style={{ marginTop: 12 }}>
                  <label className="stat-label">Note to parent {f.status === "approved" ? "(edit before sending)" : "(sent)"}</label>
                  <textarea
                    className="form-input"
                    style={{ width: "100%", minHeight: 90, marginTop: 4, fontSize: 14, lineHeight: 1.5 }}
                    value={drafts[f.id] ?? f.narrative ?? ""}
                    readOnly={f.status === "notified"}
                    maxLength={AI_INPUT.masteryNarrativeMaxLength}
                    onChange={(e) =>
                      setDrafts((d) => ({
                        ...d,
                        [f.id]: clampText(e.target.value, AI_INPUT.masteryNarrativeMaxLength),
                      }))
                    }
                  />
                </div>
              )}
              {f.status === "dismissed" && f.dismissed_reason && (
                <div style={{ marginTop: 10, fontSize: 13, color: "var(--text-muted)" }}>
                  Dismissed: {f.dismissed_reason}
                </div>
              )}

              <div style={{ display: "flex", gap: 10, marginTop: 14, justifyContent: "flex-end" }}>
                {f.status === "pending_review" && (
                  <>
                    <button className="btn btn-ghost" style={btn} disabled={busyId === f.id} onClick={() => act(f, "dismiss")}>
                      Dismiss
                    </button>
                    <button className="btn btn-primary" style={btn} disabled={busyId === f.id} onClick={() => act(f, "approve")}>
                      {busyId === f.id ? "Drafting note..." : "Approve & draft note"}
                    </button>
                  </>
                )}
                {f.status === "approved" && (
                  <>
                    <button className="btn btn-ghost" style={btn} disabled={busyId === f.id} onClick={() => act(f, "dismiss")}>
                      Dismiss
                    </button>
                    <button className="btn btn-primary" style={btn} disabled={busyId === f.id} onClick={() => act(f, "notify")}>
                      {busyId === f.id ? "Sending..." : "Send to parent"}
                    </button>
                  </>
                )}
              </div>
            </div>
          );
        })
      )}

      {tab === "notified" && flags.length > 0 && (
        <div className="card" style={{ padding: 14, fontSize: 13, color: "var(--text-muted)" }}>
          Parents see these in-app once the parent portal launches — until then, use Print digest for parent meetings.
        </div>
      )}
    </>
  );
}

function EvidenceChainPanel({ chain }: { chain: LearningEvidenceChain }) {
  const exams = chain.exams || [];
  const warnings = chain.warnings || [];
  const weakConceptCount = chain.weak_concept_count || 0;
  return (
    <div
      data-testid="learning-evidence-chain"
      style={{
        marginTop: 12,
        padding: 12,
        border: "1px solid var(--border-light)",
        borderRadius: "var(--radius-lg)",
        background: "rgba(255,255,255,0.42)",
      }}
    >
      <div style={{ fontSize: 12, fontWeight: 800, textTransform: "uppercase", letterSpacing: 0.4, color: "var(--text-muted)" }}>
        Learning evidence chain
      </div>
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 10, fontSize: 12 }}>
        <EvidencePill label="Pack" ok={(chain.curriculum_pack_ids || []).length > 0} value={(chain.curriculum_pack_ids || []).length || 0} />
        <EvidencePill label="Paper" ok={(chain.question_paper_ids || []).length > 0} value={(chain.question_paper_ids || []).length || 0} />
        <EvidencePill label="Exam" ok={exams.length > 0} value={exams.length} />
        <EvidencePill label="Evaluation" ok={(chain.approved_evaluation_ids || []).length > 0} value={(chain.approved_evaluation_ids || []).length || 0} />
        <EvidencePill label="Mastery" ok={!!chain.mastery} value={chain.mastery ? `${Math.round(chain.mastery.mastery_pct)}%` : "none"} />
        <EvidencePill label="Weak concept" ok={weakConceptCount > 0} value={weakConceptCount} />
        <EvidencePill label="Grounded" ok={!!chain.grounded} value={chain.grounded ? "yes" : "no"} />
      </div>
      {exams.length > 0 && (
        <div style={{ marginTop: 10, fontSize: 12, color: "var(--text-secondary)" }}>
          {exams
            .map((exam: LearningEvidenceExam) => `${exam.title}: ${exam.topic_pct ?? "?"}% topic score${exam.question_paper_grounded ? " - grounded paper" : ""}`)
            .join(" | ")}
        </div>
      )}
      {warnings.length > 0 ? (
        <div style={{ marginTop: 8, fontSize: 12, color: "var(--warning, #d97706)" }}>
          Needs attention: {warnings.join(", ")}
        </div>
      ) : (
        <div style={{ marginTop: 8, fontSize: 12, color: "var(--success, #059669)" }}>
          Chain verified from assessment evidence to mastery signal.
        </div>
      )}
    </div>
  );
}

function EvidencePill({ label, ok, value }: { label: string; ok: boolean; value: string | number }) {
  return (
    <span className={`badge ${ok ? "badge-success" : "badge-warning"}`}>
      {label}: {value}
    </span>
  );
}

const btn: React.CSSProperties = { width: "auto", padding: "8px 18px", borderRadius: "var(--radius-full)", fontSize: 13 };
