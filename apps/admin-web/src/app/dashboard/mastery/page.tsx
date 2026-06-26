"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, getApiErrorMessage } from "@/lib/api";

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

export default function MasteryFlagsPage() {
  const router = useRouter();
  const [tab, setTab] = useState<string>("pending_review");
  const [flags, setFlags] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState<string | null>(null);
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [credits, setCredits] = useState<{
    user_credits_remaining?: number | null;
    credits_remaining?: number;
    purpose_costs?: { mastery_narrative?: number };
  } | null>(null);

  function load(status = tab) {
    setLoading(true);
    api(`/api/v1/mastery/flags?status=${status}`)
      .then((r) => setFlags(r.data || []))
      .catch((e) => setError(getApiErrorMessage(e, "Failed to load flags")))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    load(tab);
    setError("");
    api("/api/v1/ai/credits").then(setCredits).catch(() => {});
  }, [tab]);

  async function act(flag: any, action: "approve" | "dismiss" | "notify") {
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
        const res = await api(`/api/v1/mastery/flags/${flag.id}/approve`, { method: "POST" });
        // Show the drafted note immediately for editing.
        setDrafts((d) => ({ ...d, [flag.id]: res.data.narrative }));
        api("/api/v1/ai/credits").then(setCredits).catch(() => {});
        setTab("approved");
      } else if (action === "dismiss") {
        const reason = window.prompt("Why dismiss? (optional — helps tune the alerts)") || undefined;
        await api(`/api/v1/mastery/flags/${flag.id}/dismiss`, {
          method: "POST",
          body: JSON.stringify({ reason }),
        });
        load();
      } else {
        // Save any narrative edits before sending.
        const edited = drafts[flag.id];
        if (edited !== undefined && edited !== flag.narrative) {
          await api(`/api/v1/mastery/flags/${flag.id}/narrative`, {
            method: "PUT",
            body: JSON.stringify({ narrative: edited }),
          });
        }
        const res = await api(`/api/v1/mastery/flags/${flag.id}/notify`, { method: "POST" });
        alert(res.message || "Sent");
        load();
      }
    } catch (e) {
      setError(getApiErrorMessage(e, "Action failed"));
    } finally {
      setBusyId(null);
    }
  }

  return (
    <>
      <div className="card bento-glass" style={{ marginBottom: 24, display: "flex", justifyContent: "space-between", alignItems: "center", padding: "16px 24px", flexWrap: "wrap", gap: 12 }}>
        <div>
          <h1 style={{ fontSize: 20, fontWeight: 700, margin: 0 }}>Topic Mastery — Weakness Flags</h1>
          <div style={{ fontSize: 13, color: "var(--text-muted)", marginTop: 2 }}>
            Raised by score rules, never by AI. Nothing reaches a parent without your approval.
          </div>
        </div>
        <button className="btn btn-ghost" style={btn} onClick={() => router.push("/dashboard/mastery/digest")}>
          Print digest
        </button>
      </div>

      <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
        {TABS.map((t) => (
          <button
            key={t.key}
            className={`btn ${tab === t.key ? "btn-primary" : "btn-ghost"}`}
            style={btn}
            onClick={() => setTab(t.key)}
          >
            {t.label}
          </button>
        ))}
      </div>

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
                    <b>{ev.subject_name}</b> → {f.topic_display}
                  </div>
                </div>
                <button
                  className="btn btn-ghost"
                  style={btn}
                  onClick={() =>
                    router.push(
                      `/dashboard/ai-papers?class_id=${f.class_id}&subject_id=${f.subject_id}&topics=${encodeURIComponent(f.topic_display)}&difficulty=easy`
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
                  {(ev.history || []).map((h: any) => `${h.date} · ${h.title}: ${h.pct}%`).join("   |   ")}
                </div>
              )}

              {/* Parent note (approved+) — editable until sent */}
              {(f.status === "approved" || f.status === "notified") && (
                <div style={{ marginTop: 12 }}>
                  <label className="stat-label">Note to parent {f.status === "approved" ? "(edit before sending)" : "(sent)"}</label>
                  <textarea
                    className="form-input"
                    style={{ width: "100%", minHeight: 90, marginTop: 4, fontSize: 14, lineHeight: 1.5 }}
                    value={drafts[f.id] ?? f.narrative ?? ""}
                    readOnly={f.status === "notified"}
                    onChange={(e) => setDrafts((d) => ({ ...d, [f.id]: e.target.value }))}
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
                      {busyId === f.id ? "Drafting note…" : "Approve & draft note"}
                    </button>
                  </>
                )}
                {f.status === "approved" && (
                  <>
                    <button className="btn btn-ghost" style={btn} disabled={busyId === f.id} onClick={() => act(f, "dismiss")}>
                      Dismiss
                    </button>
                    <button className="btn btn-primary" style={btn} disabled={busyId === f.id} onClick={() => act(f, "notify")}>
                      {busyId === f.id ? "Sending…" : "Send to parent"}
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

const btn: React.CSSProperties = { width: "auto", padding: "8px 18px", borderRadius: "var(--radius-full)", fontSize: 13 };
