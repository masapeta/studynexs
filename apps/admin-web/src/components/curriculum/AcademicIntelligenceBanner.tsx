"use client";

import { CheckCircle2, Loader2, AlertTriangle, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";
import { api, getApiErrorMessage } from "@/lib/api";

export type IntelligenceStatus = {
  pack_id: string;
  phase: "draft" | "approved_preparing" | "ready" | "partial" | "failed";
  pack_status: string;
  pack_approved: boolean;
  kg_ready: boolean;
  rag_ready: boolean;
  academic_intelligence_ready: boolean;
  message: string;
  rag_index_error?: string | null;
  retrievable_topic_count?: number;
  rag_vector_count?: number;
  can_approve?: boolean;
  approval_blockers?: string[];
};

type Props = {
  packId: string | null;
  onReadyChange?: (ready: boolean) => void;
  className?: string;
  canRetry?: boolean;
  onRetryComplete?: () => void;
};

export function AcademicIntelligenceBanner({
  packId,
  onReadyChange,
  className,
  canRetry = false,
  onRetryComplete,
}: Props) {
  const [status, setStatus] = useState<IntelligenceStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [retryBusy, setRetryBusy] = useState(false);
  const [retryError, setRetryError] = useState("");

  useEffect(() => {
    if (!packId) {
      setStatus(null);
      onReadyChange?.(false);
      return;
    }

    let cancelled = false;
    let timer: ReturnType<typeof setInterval> | null = null;

    async function fetchStatus() {
      setLoading(true);
      try {
        const r = await api<{ data: IntelligenceStatus }>(
          `/api/v1/curriculum/packs/${packId}/intelligence-status`
        );
        if (cancelled) return;
        setStatus(r.data);
        onReadyChange?.(r.data.academic_intelligence_ready);

        const shouldPoll =
          r.data.phase === "approved_preparing" || r.data.phase === "partial";
        if (shouldPoll && !timer) {
          timer = setInterval(() => void fetchStatus(), 4000);
        } else if (!shouldPoll && timer) {
          clearInterval(timer);
          timer = null;
        }
      } catch {
        if (!cancelled) {
          setStatus(null);
          onReadyChange?.(false);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void fetchStatus();

    return () => {
      cancelled = true;
      if (timer) clearInterval(timer);
    };
  }, [packId, onReadyChange]);

  async function retryIndexing() {
    if (!packId || !canRetry) return;
    setRetryBusy(true);
    setRetryError("");
    try {
      await api(`/api/v1/curriculum/packs/${packId}/retry-rag-index`, { method: "POST" });
      onRetryComplete?.();
      const r = await api<{ data: IntelligenceStatus }>(
        `/api/v1/curriculum/packs/${packId}/intelligence-status`
      );
      setStatus(r.data);
      onReadyChange?.(r.data.academic_intelligence_ready);
    } catch (e) {
      setRetryError(getApiErrorMessage(e, "Retry failed — check the pack has topics and try again."));
    } finally {
      setRetryBusy(false);
    }
  }

  if (!packId || (loading && !status)) {
    return null;
  }
  if (!status) return null;

  const ready = status.academic_intelligence_ready;
  const failed = status.phase === "failed";
  const preparing = status.phase === "approved_preparing" || status.phase === "partial";
  const showRetry = canRetry && failed && !ready;

  return (
    <div
      className={className}
      role="status"
      aria-live="polite"
      style={{
        display: "flex",
        alignItems: "flex-start",
        gap: 12,
        padding: "14px 18px",
        borderRadius: "var(--radius-lg)",
        border: `1px solid ${ready ? "color-mix(in srgb, var(--success) 40%, transparent)" : failed ? "color-mix(in srgb, var(--danger) 40%, transparent)" : "var(--border-subtle)"}`,
        background: ready
          ? "color-mix(in srgb, var(--success) 8%, var(--sn-glass-b))"
          : failed
            ? "color-mix(in srgb, var(--danger) 8%, var(--sn-glass-b))"
            : "var(--sn-glass-b)",
      }}
    >
      {ready ? (
        <CheckCircle2 size={22} style={{ color: "var(--success)", flexShrink: 0 }} aria-hidden />
      ) : preparing ? (
        <Loader2 size={22} className="animate-spin" style={{ flexShrink: 0 }} aria-hidden />
      ) : (
        <AlertTriangle size={22} style={{ color: "var(--warning)", flexShrink: 0 }} aria-hidden />
      )}
      <div style={{ flex: 1 }}>
        <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 4 }}>
          {ready ? "Academic Intelligence Ready" : preparing ? "Preparing Academic Intelligence" : failed ? "Preparation needs attention" : "Curriculum draft"}
        </div>
        <p style={{ margin: 0, fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.45 }}>
          {status.message}
        </p>
        {!ready && (status.retrievable_topic_count ?? 0) === 0 ? (
          <p style={{ margin: "6px 0 0", fontSize: 12, color: "var(--text-muted)" }}>
            Add topics with curriculum content before approval or indexing.
          </p>
        ) : null}
        {(status.approval_blockers || []).map((blocker) => (
          <p key={blocker} style={{ margin: "6px 0 0", fontSize: 12, color: "var(--text-muted)" }}>
            {blocker}
          </p>
        ))}
        {failed && status.rag_index_error ? (
          <p style={{ margin: "6px 0 0", fontSize: 12, color: "var(--text-muted)" }}>
            {status.rag_index_error.slice(0, 160)}
          </p>
        ) : null}
        {retryError ? (
          <p role="alert" style={{ margin: "8px 0 0", fontSize: 12, color: "var(--danger)" }}>
            {retryError}
          </p>
        ) : null}
        {showRetry ? (
          <button
            type="button"
            className="sn-btn sn-btn--ghost"
            style={{ marginTop: 10, width: "auto", padding: "6px 14px", fontSize: 12 }}
            disabled={retryBusy}
            onClick={() => void retryIndexing()}
          >
            <RefreshCw size={14} style={{ marginRight: 6, verticalAlign: "middle" }} />
            {retryBusy ? "Retrying indexing…" : "Retry indexing"}
          </button>
        ) : null}
      </div>
    </div>
  );
}
