"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import PortalShell from "@/components/PortalShell";
import { api, getApiErrorMessage } from "@/lib/api";
import { STUDENT_NAV } from "@/lib/student-portal";
import type { DailyLearningPlan } from "@/lib/student-portal";
import type { PortalContext } from "@/lib/portal-types";

export default function StudentHomePage() {
  const [ctx, setCtx] = useState<PortalContext | null>(null);
  const [dailyPlan, setDailyPlan] = useState<DailyLearningPlan | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api<{ data: PortalContext }>("/api/v1/portal/context")
      .then(async (r) => {
        setCtx(r.data);
        const sid = r.data?.children?.[0]?.student_id ?? r.data?.student_id;
        if (!sid) return;
        const plan = await api<{ data: DailyLearningPlan }>(
          `/api/v1/tutor/students/${sid}/daily-plan`
        );
        setDailyPlan(plan.data);
      })
      .catch((e) => setError(getApiErrorMessage(e, "Failed to load")));
  }, []);

  const me = ctx?.children?.[0];

  return (
    <PortalShell title="Student Portal" subtitle={me?.name || ctx?.student_name || "Your learning"} nav={STUDENT_NAV}>
      {error && <p style={{ color: "var(--danger)" }}>{error}</p>}
      {!ctx ? (
        <div className="spinner" style={{ margin: "40px auto" }} />
      ) : !me ? (
        <p>No student profile linked to this account.</p>
      ) : (
        <>
          {dailyPlan?.status === "ready" ? (
            <Link
              href={`/student/tutor?lesson=${dailyPlan.lesson_key}`}
              className="portal-card"
              data-testid="student-daily-plan"
              style={{ display: "block", textDecoration: "none", color: "inherit", marginBottom: 16, borderColor: "var(--accent)" }}
            >
              <div style={{ fontSize: 12, fontWeight: 800, color: "var(--text-muted)", marginBottom: 6 }}>
                Study this today
              </div>
              <div style={{ fontWeight: 800, fontSize: 17, color: "var(--accent-dark)" }}>{dailyPlan.title}</div>
              <p style={{ fontSize: 14, color: "var(--text-muted)", margin: "8px 0 0" }}>
                {dailyPlan.reason}
              </p>
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 10, fontSize: 12 }}>
                <span className={`badge ${dailyPlan.grounded && !dailyPlan.fallback ? "badge-success" : "badge-warning"}`}>
                  {dailyPlan.grounded && !dailyPlan.fallback ? "Evidence verified" : "Needs teacher evidence"}
                </span>
                {dailyPlan.mastery_pct != null && (
                  <span className="badge badge-warning">{Math.round(dailyPlan.mastery_pct)}% mastery</span>
                )}
                {dailyPlan.mastery_topic ? (
                  <span className="badge badge-info">From {dailyPlan.mastery_topic}</span>
                ) : null}
              </div>
            </Link>
          ) : (
            <Link
              href="/student/tutor"
              className="portal-card"
              data-testid="student-daily-plan-empty"
              style={{ display: "block", textDecoration: "none", color: "inherit", marginBottom: 16, borderColor: "var(--accent)" }}
            >
              <div style={{ fontWeight: 800, fontSize: 17, color: "var(--accent-dark)" }}>AI Tutor - start here</div>
              <p style={{ fontSize: 14, color: "var(--text-muted)", margin: "8px 0 0" }}>
                Teacher-style explanations unlock after your first assessed weak topic.
              </p>
            </Link>
          )}
          <div className="portal-stat-grid">
            <div className="portal-stat">
              <div className="portal-stat-label">Class</div>
              <div className="portal-stat-value" style={{ fontSize: 16 }}>{me.class_label}</div>
            </div>
            <div className="portal-stat">
              <div className="portal-stat-label">Attendance</div>
              <div className="portal-stat-value">{me.attendance_pct != null ? `${me.attendance_pct}%` : "-"}</div>
            </div>
            <div className="portal-stat">
              <div className="portal-stat-label">Weak topics</div>
              <div className="portal-stat-value">{me.weak_topic_count}</div>
            </div>
            <div className="portal-stat">
              <div className="portal-stat-label">Tutor</div>
              <div className="portal-stat-value" style={{ fontSize: 14 }}>Live</div>
            </div>
          </div>
        </>
      )}
    </PortalShell>
  );
}
