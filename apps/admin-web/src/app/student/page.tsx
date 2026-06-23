"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import PortalShell from "@/components/PortalShell";
import { api, getApiErrorMessage } from "@/lib/api";
import { STUDENT_NAV } from "@/lib/student-portal";

export default function StudentHomePage() {
  const [ctx, setCtx] = useState<any>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api("/api/v1/portal/context")
      .then((r) => setCtx(r.data))
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
          <Link href="/student/tutor" className="portal-card" style={{ display: "block", textDecoration: "none", color: "inherit", marginBottom: 16, borderColor: "var(--accent)" }}>
            <div style={{ fontWeight: 800, fontSize: 17, color: "var(--accent-dark)" }}>AI Tutor — start here</div>
            <p style={{ fontSize: 14, color: "var(--text-muted)", margin: "8px 0 0" }}>
              Teacher-style explanations with voice & pictures. Pause and replay until you understand.
            </p>
          </Link>
          <div className="portal-stat-grid">
            <div className="portal-stat">
              <div className="portal-stat-label">Class</div>
              <div className="portal-stat-value" style={{ fontSize: 16 }}>{me.class_label}</div>
            </div>
            <div className="portal-stat">
              <div className="portal-stat-label">Attendance</div>
              <div className="portal-stat-value">{me.attendance_pct != null ? `${me.attendance_pct}%` : "—"}</div>
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
