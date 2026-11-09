"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { History, Send } from "lucide-react";
import { PageHeaderCard } from "@/components/layout/PageHeaderCard";
import { EmptyState } from "@/components/ui/kit";
import { api, ApiError, getApiErrorMessage } from "@/lib/api";
import { TEACHING } from "@/lib/dashboard-routes";

type ApiData<T> = { data: T; message?: string };

type ReleaseEvent = {
  id: string;
  event_no: number;
  generation_no: number | null;
  action: "release" | "withdraw" | "block" | "unblock";
  actor_role: string;
  reason: string | null;
  published_count: number;
  partial: boolean;
  prior_status: string;
  resulting_status: string;
  created_at: string;
};

type ReleaseState = {
  status: "not_released" | "released" | "withdrawn" | "blocked";
  current_generation_no: number;
  published_count: number;
  unpublished_changes_count: number;
  pending: Record<string, number>;
  blocked_reason: string | null;
  can_release: boolean;
  can_withdraw: boolean;
  can_override: boolean;
  history: ReleaseEvent[];
};

type Preview = {
  preview_token: string;
  expected_generation_no: number;
  eligible_count: number;
  changes_count: number;
  pending: Record<string, number>;
  pending_total: number;
  expires_in_seconds: number;
};

type ExamRow = { id: string; title: string; total_marks: number };

const PENDING_LABELS: Record<string, string> = {
  not_submitted: "Sheet not submitted",
  processing: "Evaluation in progress",
  ai_suggested_awaiting_review: "Awaiting teacher review",
  needs_manual_review: "Needs manual review",
  failed: "Evaluation failed",
  absent_or_no_mark: "No mark recorded",
  reopened_under_review: "Reopened, under review",
};

const STATUS_LABELS: Record<ReleaseState["status"], string> = {
  not_released: "Not released",
  released: "Released",
  withdrawn: "Withdrawn",
  blocked: "Blocked by principal",
};

function newToken(): string {
  return crypto.randomUUID();
}

export default function ExamResultsPage() {
  const params = useParams();
  const examId = params.examId as string;
  const [exam, setExam] = useState<ExamRow | null>(null);
  const [state, setState] = useState<ReleaseState | null>(null);
  const [preview, setPreview] = useState<Preview | null>(null);
  const [ackPartial, setAckPartial] = useState(false);
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(true);

  const fetchAll = useCallback(
    () =>
      Promise.all([
        api<ApiData<ExamRow>>(`/api/v1/exams/${examId}`),
        api<ApiData<ReleaseState>>(`/api/v1/exams/${examId}/release`),
      ]),
    [examId]
  );

  const load = useCallback(async () => {
    const [ex, st] = await fetchAll();
    setExam(ex.data);
    setState(st.data);
  }, [fetchAll]);

  useEffect(() => {
    let alive = true;
    fetchAll()
      .then(([ex, st]) => {
        if (!alive) return;
        setExam(ex.data);
        setState(st.data);
      })
      .catch((e) => alive && setError(getApiErrorMessage(e, "Couldn't load release status.")))
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, [fetchAll]);

  async function startPreview() {
    setBusy("preview");
    setError("");
    setNotice("");
    setAckPartial(false);
    try {
      const res = await api<ApiData<Preview>>(`/api/v1/exams/${examId}/release/preview`, { method: "POST" });
      setPreview(res.data);
    } catch (e) {
      setError(getApiErrorMessage(e, "Couldn't prepare the release preview."));
    } finally {
      setBusy(null);
    }
  }

  async function confirmRelease() {
    if (!preview) return;
    setBusy("confirm");
    setError("");
    try {
      const res = await api<ApiData<{ no_changes: boolean; replayed: boolean; release: ReleaseEvent | null }>>(
        `/api/v1/exams/${examId}/release/confirm`,
        {
          method: "POST",
          body: JSON.stringify({
            preview_token: preview.preview_token,
            confirm_partial: preview.pending_total > 0 ? ackPartial : false,
            acknowledged_pending_count: preview.pending_total > 0 ? preview.pending_total : undefined,
          }),
        }
      );
      setPreview(null);
      setNotice(
        res.data.no_changes
          ? "Nothing new to release — every eligible result is already published."
          : `Results released (generation ${res.data.release?.generation_no}). Students and parents have been notified.`
      );
      await load();
    } catch (e) {
      if (e instanceof ApiError && e.status === 409) setPreview(null);
      setError(getApiErrorMessage(e, "Release failed."));
    } finally {
      setBusy(null);
    }
  }

  async function governed(action: "withdraw" | "block" | "unblock") {
    const r = reason.trim();
    if (r.length < 3) {
      setError("Give a reason (at least 3 characters).");
      return;
    }
    setBusy(action);
    setError("");
    setNotice("");
    try {
      const res = await api<ApiData<ReleaseEvent>>(`/api/v1/exams/${examId}/release/${action}`, {
        method: "POST",
        body: JSON.stringify({ reason: r, action_token: newToken() }),
      });
      setReason("");
      setNotice(res.message || "Done");
      setPreview(null);
      await load();
    } catch (e) {
      setError(getApiErrorMessage(e, "Action failed."));
    } finally {
      setBusy(null);
    }
  }

  if (loading) {
    return (
      <div className="card" style={{ padding: 40, textAlign: "center" }} aria-busy="true">
        <div className="spinner" style={{ margin: "0 auto" }} />
      </div>
    );
  }

  return (
    <>
      <PageHeaderCard
        title="Results & release"
        subtitle={`${exam?.title || "Exam"} · Families see results only after they are released`}
      >
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <Link href={TEACHING.evaluate(examId)} className="btn btn-ghost gw-btn-sm">Evaluate sheets</Link>
          <Link href={TEACHING.exams} className="btn btn-ghost gw-btn-sm">← Exams</Link>
        </div>
      </PageHeaderCard>

      {error && <div className="card sn-inline-alert sn-inline-alert--error" role="alert">{error}</div>}
      {notice && <div className="card sn-inline-alert sn-success-pulse" role="status">{notice}</div>}

      {!state ? (
        <EmptyState icon={History} title="Release status unavailable" message="Reload the page to try again." />
      ) : (
        <>
          <div className="card" style={{ padding: 20, marginBottom: 16 }}>
            <div className="sn-release-actions" style={{ justifyContent: "space-between" }}>
              <div>
                <div className="stat-label">Status</div>
                <div style={{ fontSize: 20, fontWeight: 700 }} data-testid="release-status">
                  {STATUS_LABELS[state.status]}
                  {state.current_generation_no > 0 && (
                    <span style={{ fontSize: 13, fontWeight: 400, color: "var(--text-muted)" }}>
                      {" "}· generation {state.current_generation_no}
                    </span>
                  )}
                </div>
                {state.blocked_reason && (
                  <div style={{ fontSize: 13, color: "var(--text-muted)" }}>Reason: {state.blocked_reason}</div>
                )}
              </div>
              <div style={{ textAlign: "right" }}>
                <div className="stat-label">Visible to families</div>
                <div style={{ fontSize: 20, fontWeight: 700 }}>{state.published_count}</div>
                <div style={{ fontSize: 13, color: "var(--text-muted)" }}>
                  {state.unpublished_changes_count} approved result(s) not yet released
                </div>
              </div>
            </div>
            <div className="sn-release-pending" aria-label="Students still pending">
              {Object.entries(state.pending).filter(([, n]) => n > 0).map(([k, n]) => (
                <div key={k} className="ui-card" style={{ padding: 10 }}>
                  <div style={{ fontSize: 20, fontWeight: 700 }}>{n}</div>
                  <div style={{ fontSize: 12, color: "var(--text-muted)" }}>{PENDING_LABELS[k] || k}</div>
                </div>
              ))}
            </div>

            {state.can_release && state.status !== "blocked" && !preview && (
              <button type="button" className="btn btn-primary" onClick={startPreview} disabled={busy !== null}>
                <Send size={16} aria-hidden /> {busy === "preview" ? "Preparing…" : "Preview release"}
              </button>
            )}
            {!state.can_release && (
              <p style={{ fontSize: 13, color: "var(--text-muted)" }}>
                Results are released by the class incharge or the principal.
              </p>
            )}

            {preview && (
              <div className="card" style={{ padding: 16, marginTop: 12 }} data-testid="release-preview">
                <strong>Release generation {preview.expected_generation_no}</strong>
                <p style={{ fontSize: 14 }}>
                  {preview.changes_count} result(s) will become visible to students and their parents.
                  {preview.pending_total > 0 && ` ${preview.pending_total} student(s) are still pending and will see “Result pending”.`}
                </p>
                {preview.pending_total > 0 && (
                  <label style={{ display: "flex", gap: 8, alignItems: "flex-start", fontSize: 14, marginBottom: 12 }}>
                    <input
                      type="checkbox"
                      checked={ackPartial}
                      onChange={(e) => setAckPartial(e.target.checked)}
                      aria-describedby="partial-help"
                    />
                    <span id="partial-help">
                      I understand {preview.pending_total} student(s) are pending; release the others now.
                    </span>
                  </label>
                )}
                <div className="sn-release-actions">
                  <button
                    type="button"
                    className="btn btn-primary"
                    onClick={confirmRelease}
                    disabled={busy !== null || (preview.pending_total > 0 && !ackPartial)}
                  >
                    {busy === "confirm" ? "Releasing…" : "Confirm release"}
                  </button>
                  <button type="button" className="btn btn-ghost" onClick={() => setPreview(null)} disabled={busy !== null}>
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>

          {(state.can_withdraw || state.can_override) && (
            <div className="card" style={{ padding: 20, marginBottom: 16 }}>
              <label htmlFor="governed-reason" className="stat-label" style={{ display: "block", marginBottom: 6 }}>
                Reason (required for withdraw / block / unblock)
              </label>
              <input
                id="governed-reason"
                className="form-input"
                value={reason}
                maxLength={500}
                onChange={(e) => setReason(e.target.value)}
                placeholder="e.g. Marks entry error found in Q4"
                style={{ width: "100%", marginBottom: 12 }}
              />
              <div className="sn-release-actions">
                {state.can_withdraw && state.status === "released" && (
                  <button type="button" className="btn btn-ghost" onClick={() => governed("withdraw")} disabled={busy !== null}>
                    {busy === "withdraw" ? "Withdrawing…" : "Withdraw results"}
                  </button>
                )}
                {state.can_override && state.status !== "blocked" && (
                  <button type="button" className="btn btn-ghost" onClick={() => governed("block")} disabled={busy !== null}>
                    {busy === "block" ? "Blocking…" : "Block release"}
                  </button>
                )}
                {state.can_override && state.status === "blocked" && (
                  <button type="button" className="btn btn-ghost" onClick={() => governed("unblock")} disabled={busy !== null}>
                    {busy === "unblock" ? "Unblocking…" : "Unblock"}
                  </button>
                )}
              </div>
            </div>
          )}

          <div className="card" style={{ padding: 20 }}>
            <div className="stat-label" style={{ marginBottom: 8 }}>History</div>
            {state.history.length === 0 ? (
              <p style={{ fontSize: 13, color: "var(--text-muted)" }}>No release activity yet.</p>
            ) : (
              <div className="sn-table-scroll">
                <table className="data-table">
                  <thead>
                    <tr><th scope="col">When</th><th scope="col">Action</th><th scope="col">By</th><th scope="col">Published</th><th scope="col">Reason</th></tr>
                  </thead>
                  <tbody>
                    {state.history.map((h) => (
                      <tr key={h.id}>
                        <td>{new Date(h.created_at).toLocaleString()}</td>
                        <td>
                          {h.action}{h.generation_no ? ` · gen ${h.generation_no}` : ""}{h.partial ? " (partial)" : ""}
                        </td>
                        <td>{h.actor_role.replace(/_/g, " ")}</td>
                        <td>{h.action === "release" ? h.published_count : "—"}</td>
                        <td>{h.reason || "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}
    </>
  );
}
