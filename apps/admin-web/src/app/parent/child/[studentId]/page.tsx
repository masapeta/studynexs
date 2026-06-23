"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import PortalShell from "@/components/PortalShell";
import { PARENT_NAV } from "@/lib/portal-nav";
import { api, getApiErrorMessage } from "@/lib/api";

export default function ParentChildPage() {
  const params = useParams();
  const studentId = params.studentId as string;
  const [profile, setProfile] = useState<any>(null);
  const [mastery, setMastery] = useState<any>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!studentId) return;
    Promise.all([
      api(`/api/v1/academic/students/${studentId}/profile`),
      api(`/api/v1/mastery/students/${studentId}`),
    ])
      .then(([p, m]) => {
        setProfile(p.data);
        setMastery(m.data);
      })
      .catch((e) => setError(getApiErrorMessage(e, "Failed to load child")));
  }, [studentId]);

  const weakTopics = (mastery?.subjects || []).flatMap((s: any) =>
    (s.topics || []).filter((t: any) => t.mastery_pct < 70).map((t: any) => ({ ...t, subject: s.subject_name }))
  );

  return (
    <PortalShell title="Child profile" subtitle={profile?.student_name} nav={PARENT_NAV}>
      <Link href="/parent" style={{ fontSize: 13, marginBottom: 12, display: "inline-block" }}>← All children</Link>
      {error && <p style={{ color: "var(--danger)" }}>{error}</p>}
      {!profile ? (
        <div className="spinner" style={{ margin: "40px auto" }} />
      ) : (
        <>
          <div className="portal-stat-grid">
            <div className="portal-stat">
              <div className="portal-stat-label">Attendance</div>
              <div className="portal-stat-value">{profile.attendance?.percentage != null ? `${profile.attendance.percentage}%` : "—"}</div>
            </div>
            <div className="portal-stat">
              <div className="portal-stat-label">Fees pending</div>
              <div className="portal-stat-value">₹{profile.fees?.pending ?? 0}</div>
            </div>
          </div>
          <div className="portal-card">
            <div style={{ fontWeight: 700, marginBottom: 8 }}>Weak concepts (from exams)</div>
            {weakTopics.length === 0 ? (
              <p style={{ fontSize: 13, color: "var(--text-muted)" }}>No weak topics yet — appears after marked exams.</p>
            ) : (
              <ul style={{ margin: 0, paddingLeft: 18, fontSize: 14 }}>
                {weakTopics.slice(0, 8).map((t: any) => (
                  <li key={`${t.subject}-${t.topic}`}>{t.subject}: {t.topic} ({Math.round(t.mastery_pct)}%)</li>
                ))}
              </ul>
            )}
          </div>
          <div className="portal-card">
            <div style={{ fontWeight: 700, marginBottom: 8 }}>Coming next</div>
            <p style={{ fontSize: 13, color: "var(--text-muted)", margin: 0 }}>
              Weekly AI progress summary · Remedial worksheets · WhatsApp alerts (pilot add-on).
            </p>
          </div>
        </>
      )}
    </PortalShell>
  );
}
