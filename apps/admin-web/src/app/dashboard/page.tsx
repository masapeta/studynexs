"use client";

import { useAuth } from "@/lib/auth-context";
import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { GraduationCap, Users, BookOpen, ClipboardCheck, Megaphone } from "lucide-react";
import { api, getApiErrorMessage } from "@/lib/api";
import { roleLabel } from "@/lib/permissions";
import { TeacherCommandCenter, type TeacherHome } from "@/components/TeacherCommandCenter";

type Summary = {
  persona: "admin" | "class_incharge" | "teacher";
  subtitle: string;
  teacher_home?: TeacherHome | null;
  total_students?: number | null;
  total_teachers?: number | null;
  total_classes?: number | null;
  pending_fees?: number | null;
  school_attendance_percent?: number | null;
  class_performance?: { label: string; percentage: number }[];
  incharge_classes?: {
    class_id: string;
    class_label: string;
    attendance_percent?: number | null;
    pending_qp_approvals: number;
  }[];
  quick_actions?: { label: string; href: string }[];
  notices?: { id: string; title: string; content: string; audience: string; priority: string; created_at?: string }[];
};

export default function DashboardPage() {
  const { user, permissions, loading: authLoading } = useAuth();
  const [summary, setSummary] = useState<Summary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    setLoading(true);
    setError("");
    api<{ data: Summary }>("/api/v1/dashboard/summary")
      .then((r) => setSummary(r.data))
      .catch((e) => setError(getApiErrorMessage(e, "Could not load dashboard.")))
      .finally(() => setLoading(false));
  }, []);

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

  return (
    <>
      <div className="hero-banner">
        <h2>Welcome back, {user?.full_name?.split(" ")[0] || "there"}</h2>
        <p>{s?.subtitle || "Your workspace for today."}</p>
        {permissions && (
          <p style={{ fontSize: 13, opacity: 0.85, marginTop: 6 }}>{roleLabel(permissions.role)}</p>
        )}
        <div className="hero-decorations"><GraduationCap size={76} strokeWidth={1.1} /></div>
      </div>

      {persona === "admin" && s && (
        <div className="dashboard-grid">
          <div className="card">
            <div className="card-header"><span className="card-title">Daily Overview</span></div>
            <div className="stat-row">
              <div className="stat-box">
                <div className="stat-label">School Attendance</div>
                <div className="stat-value">{s.school_attendance_percent ?? 0}%</div>
              </div>
              <div className="stat-box warning">
                <div className="stat-label">Pending Fees</div>
                <div className="stat-value warning">₹ {(s.pending_fees ?? 0).toLocaleString()}</div>
              </div>
            </div>
          </div>
          <div className="card">
            <div className="card-header"><span className="card-title">School at a Glance</span></div>
            <div className="event-item green">
              <div className="event-icon"><GraduationCap size={18} color="var(--success)" /></div>
              <div>
                <div className="event-title">{s.total_students ?? 0} Students</div>
                <div className="event-subtitle">Across {s.total_classes ?? 0} classes</div>
              </div>
            </div>
            <div className="event-item orange">
              <div className="event-icon"><Users size={18} color="var(--accent-dark)" /></div>
              <div>
                <div className="event-title">{s.total_teachers ?? 0} Teaching staff</div>
                <div className="event-subtitle">Active this academic year</div>
              </div>
            </div>
          </div>
          <div className="card">
            <div className="card-header"><span className="card-title">Class Progress</span></div>
            {(s.class_performance ?? []).length > 0 ? (
              s.class_performance!.map((c, i) => (
                <div className="progress-item" key={c.label}>
                  <div className="progress-icon" style={{ background: ["var(--primary-50)", "var(--accent-50)", "var(--success-light)"][i % 3] }}>
                    <BookOpen size={15} />
                  </div>
                  <div className="progress-info">
                    <div className="progress-label">{c.label}</div>
                    <div className="progress-sub">Exam average</div>
                  </div>
                  <div className="progress-bar">
                    <div className={`progress-fill ${c.percentage >= 60 ? "green" : "orange"}`} style={{ width: `${Math.min(100, c.percentage)}%` }} />
                  </div>
                </div>
              ))
            ) : (
              <div style={{ color: "var(--text-muted)", fontSize: 13 }}>No exam data yet.</div>
            )}
          </div>
        </div>
      )}

      {persona === "class_incharge" && s && (
        <div className="dashboard-grid">
          {(s.incharge_classes ?? []).map((c) => (
            <div className="card" key={c.class_id}>
              <div className="card-header"><span className="card-title">{c.class_label}</span></div>
              <div className="stat-row">
                <div className="stat-box">
                  <div className="stat-label">Today&apos;s Attendance</div>
                  <div className="stat-value">{c.attendance_percent ?? "—"}%</div>
                </div>
                <div className="stat-box warning">
                  <div className="stat-label">Papers to Approve</div>
                  <div className="stat-value warning">{c.pending_qp_approvals}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {(s?.quick_actions?.length ?? 0) > 0 && (
        <div className="quick-actions">
          <h3>Quick Actions</h3>
          <div className="quick-actions-row">
            {s!.quick_actions!.map((a) => (
              <Link key={a.href} href={a.href} className="btn btn-action">
                {a.label.includes("Attendance") && <ClipboardCheck size={16} />}
                {a.label.includes("Notice") && <Megaphone size={16} />}
                {a.label}
              </Link>
            ))}
          </div>
        </div>
      )}
    </>
  );
}
