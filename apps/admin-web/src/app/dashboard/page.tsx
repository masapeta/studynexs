"use client";

import { useAuth } from "@/lib/auth-context";
import { useCallback, useEffect, useState } from "react";
import { api, getApiErrorMessage } from "@/lib/api";
import { TeacherCommandCenter, type TeacherHome } from "@/components/TeacherCommandCenter";
import {
  MorningBriefing,
  type BriefingSummary,
} from "@/components/briefing/MorningBriefing";

type Summary = BriefingSummary & {
  teacher_home?: TeacherHome | null;
  class_performance?: { label: string; percentage: number }[];
  quick_actions?: { label: string; href: string }[];
};

type EventItem = { id: string; title: string; event_date: string };
type FeeStats = { total_collected?: number; pending_amount?: number };

function DashboardSkeleton() {
  return (
    <div className="briefing-page briefing-page--executive" aria-busy="true" aria-label="Loading dashboard">
      <div className="briefing-exec-row briefing-exec-row--kpis">
        {[0, 1, 2, 3].map((i) => (
          <div
            key={i}
            className="briefing-glass-chip briefing-exec-kpi"
            style={{ minHeight: 68, opacity: 0.45 }}
          />
        ))}
      </div>
      <div className="briefing-exec-row briefing-exec-row--command">
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="briefing-glass-chip briefing-panel"
            style={{ minHeight: 200, opacity: 0.4 }}
          />
        ))}
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const { user } = useAuth();
  const [summary, setSummary] = useState<Summary | null>(null);
  const [feeStats, setFeeStats] = useState<FeeStats | null>(null);
  const [eventsCount, setEventsCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    if (!user) return;
    setLoading(true);
    setError("");

    const isAdmin = user.role === "admin" || user.role === "super_admin";

    const summaryP = api<{ data: Summary }>("/api/v1/dashboard/summary")
      .then((r) => r.data)
      .catch((e) => {
        throw e;
      });

    const eventsP = api<{ data: EventItem[] }>("/api/v1/ops/events")
      .then((r) => setEventsCount((r.data || []).length))
      .catch(() => setEventsCount(0));

    const feesP = isAdmin
      ? api<{ data: FeeStats }>("/api/v1/fees/stats")
          .then((r) => setFeeStats(r.data))
          .catch(() => setFeeStats(null))
      : Promise.resolve();

    Promise.all([summaryP, eventsP, feesP])
      .then(([s]) => setSummary(s))
      .catch((e) => setError(getApiErrorMessage(e, "Could not load dashboard.")))
      .finally(() => setLoading(false));
  }, [user]);

  useEffect(() => {
    if (!user) return;
    load();
  }, [user, load]);

  if (!user) return null;

  if (loading) {
    return <DashboardSkeleton />;
  }

  if (error) {
    return (
      <div className="card" style={{ padding: 24, marginTop: 24 }}>
        <h2 style={{ fontSize: 18, marginBottom: 8 }}>Dashboard unavailable</h2>
        <p style={{ color: "var(--danger)", marginBottom: 16 }}>{error}</p>
        <button className="btn btn-primary" type="button" onClick={load} style={{ width: "auto" }}>
          Retry
        </button>
      </div>
    );
  }

  const s = summary;
  const persona = s?.persona ?? "teacher";

  if (persona === "teacher" && s?.teacher_home) {
    return <TeacherCommandCenter data={s.teacher_home} onRefresh={load} />;
  }

  if ((persona === "admin" || persona === "class_incharge") && s) {
    return (
      <MorningBriefing
        userName={user.full_name}
        userId={user.id}
        summary={s}
        feeStats={feeStats}
        eventsCount={eventsCount}
      />
    );
  }

  return (
    <MorningBriefing
      userName={user.full_name}
      userId={user.id}
      summary={s || { persona: "teacher", subtitle: "Your workspace for today." }}
      eventsCount={eventsCount}
    />
  );
}
