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

export default function DashboardPage() {
  const { user, loading: authLoading } = useAuth();
  const [summary, setSummary] = useState<Summary | null>(null);
  const [feeStats, setFeeStats] = useState<FeeStats | null>(null);
  const [eventsCount, setEventsCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    setLoading(true);
    setError("");

    const summaryP = api<{ data: Summary }>("/api/v1/dashboard/summary")
      .then((r) => r.data)
      .catch((e) => {
        throw e;
      });

    const eventsP = api<{ data: EventItem[] }>("/api/v1/ops/events")
      .then((r) => setEventsCount((r.data || []).length))
      .catch(() => setEventsCount(0));

    const feesP =
      user?.role === "admin" || user?.role === "super_admin"
        ? api<{ data: FeeStats }>("/api/v1/fees/stats")
            .then((r) => setFeeStats(r.data))
            .catch(() => setFeeStats(null))
        : Promise.resolve();

    Promise.all([summaryP, eventsP, feesP])
      .then(([s]) => setSummary(s))
      .catch((e) => setError(getApiErrorMessage(e, "Could not load dashboard.")))
      .finally(() => setLoading(false));
  }, [user?.role]);

  useEffect(() => {
    if (authLoading || !user) return;
    load();
  }, [authLoading, user, load]);

  if (authLoading || loading) {
    return (
      <div className="loading-screen" style={{ minHeight: "60vh" }}>
        <div className="spinner" />
      </div>
    );
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

  if ((persona === "admin" || persona === "class_incharge") && s && user) {
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
      userName={user?.full_name || "User"}
      userId={user?.id || "guest"}
      summary={s || { persona: "teacher", subtitle: "Your workspace for today." }}
      eventsCount={eventsCount}
    />
  );
}
