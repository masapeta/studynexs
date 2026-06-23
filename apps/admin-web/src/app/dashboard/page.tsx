"use client";

import { useAuth } from "@/lib/auth-context";
import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  GraduationCap, Users, BookOpen, ClipboardCheck, Megaphone,
  CalendarDays, UserPlus, BellRing, Wallet,
} from "lucide-react";
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

type EventItem = { id: string; title: string; event_date: string; event_time?: string | null; venue?: string | null };

const ACTION_TONES = ["blue", "green", "orange"] as const;

function actionIcon(label: string) {
  if (/student|add/i.test(label)) return <UserPlus size={16} />;
  if (/attendance/i.test(label)) return <ClipboardCheck size={16} />;
  if (/notice|alert|parent/i.test(label)) return <BellRing size={16} />;
  if (/event/i.test(label)) return <CalendarDays size={16} />;
  return <Megaphone size={16} />;
}

function fmtDate(iso?: string) {
  if (!iso) return "";
  const d = new Date(iso);
  return isNaN(d.getTime()) ? "" : d.toLocaleDateString("en-IN", { day: "numeric", month: "short" });
}

export default function DashboardPage() {
  const { user, permissions, loading: authLoading } = useAuth();
  const [summary, setSummary] = useState<Summary | null>(null);
  const [events, setEvents] = useState<EventItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    setLoading(true);
    setError("");
    api<{ data: Summary }>("/api/v1/dashboard/summary")
      .then((r) => setSummary(r.data))
      .catch((e) => setError(getApiErrorMessage(e, "Could not load dashboard.")))
      .finally(() => setLoading(false));
    api<{ data: EventItem[] }>("/api/v1/ops/events")
      .then((r) => setEvents((r.data || []).slice(0, 3)))
      .catch(() => setEvents([]));
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

  const hubLabel = persona === "admin" ? "Admin Hub" : "Class Hub";

  return (
    <>
      <div className="hero-banner hero-hub">
        <div className="hero-eyebrow">StudyNexs Connect · {hubLabel}</div>
        <h2>Welcome back, {user?.full_name?.split(" ")[0] || "there"}</h2>
        <p>{s?.subtitle || "Your workspace for today."}</p>
        {permissions && (
          <p style={{ fontSize: 13, opacity: 0.85, marginTop: 6 }}>{roleLabel(permissions.role)}</p>
        )}
        <div className="hero-decorations"><BookOpen size={76} strokeWidth={1.1} /></div>
      </div>

      {persona === "admin" && s && (
        <div className="dashboard-grid">
          <div className="card">
            <div className="card-header"><span className="card-title">Daily Overview</span></div>
            <div className="stat-row">
              <div className="stat-box info">
                <div className="stat-label">Total Attendance</div>
                <div className="stat-value info">{s.school_attendance_percent ?? 0}%</div>
              </div>
              <div className="stat-box warning">
                <div className="stat-label">Pending Fees</div>
                <div className="stat-value warning">₹{(s.pending_fees ?? 0).toLocaleString("en-IN")}</div>
              </div>
            </div>
            <div className="stat-mini-row">
              <span>{s.total_students ?? 0} students</span>
              <span>{s.total_teachers ?? 0} staff</span>
              <span>{s.total_classes ?? 0} classes</span>
            </div>
          </div>

          <div className="card">
            <div className="card-header"><span className="card-title">Upcoming Events</span></div>
            {events.length > 0 ? (
              events.map((e, i) => (
                <div className={`event-item ${i % 2 === 0 ? "green" : "orange"}`} key={e.id}>
                  <div className="event-icon">
                    <CalendarDays size={18} color={i % 2 === 0 ? "var(--success)" : "var(--accent-dark)"} />
                  </div>
                  <div>
                    <div className="event-title">{e.title}</div>
                    <div className="event-subtitle">
                      {fmtDate(e.event_date)}{e.event_time ? ` · ${e.event_time}` : ""}{e.venue ? ` · ${e.venue}` : ""}
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div style={{ color: "var(--text-muted)", fontSize: 13, padding: "8px 0" }}>
                No upcoming events. <Link href="/dashboard/events" style={{ color: "var(--accent-dark)", fontWeight: 600 }}>Create one →</Link>
              </div>
            )}
          </div>

          <div className="card">
            <div className="card-header"><span className="card-title">Class Progress</span></div>
            {(s.class_performance ?? []).length > 0 ? (
              s.class_performance!.map((c, i) => (
                <div className="progress-item" key={c.label}>
                  <div className="progress-icon" style={{ background: ["var(--info-light)", "var(--accent-50)", "var(--success-light)"][i % 3] }}>
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
                <div className="stat-box info">
                  <div className="stat-label">Today&apos;s Attendance</div>
                  <div className="stat-value info">{c.attendance_percent ?? "—"}%</div>
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
            {s!.quick_actions!.map((a, i) => (
              <Link key={a.href} href={a.href} className={`btn btn-action ${ACTION_TONES[i % ACTION_TONES.length]}`}>
                {actionIcon(a.label)}
                {a.label}
              </Link>
            ))}
          </div>
        </div>
      )}

      {(s?.notices?.length ?? 0) > 0 && (
        <div className="data-table-card">
          <div className="card-header" style={{ padding: "16px 20px 0" }}>
            <span className="card-title">Recent Notices</span>
            <Link href="/dashboard/notices" style={{ fontSize: 13, color: "var(--accent-dark)", fontWeight: 600 }}>View all →</Link>
          </div>
          <table className="data-table">
            <thead>
              <tr><th>Notice</th><th>Audience</th><th>Priority</th><th style={{ textAlign: "right" }}>Date</th></tr>
            </thead>
            <tbody>
              {s!.notices!.map((n) => (
                <tr key={n.id}>
                  <td style={{ fontWeight: 600 }}>{n.title}</td>
                  <td style={{ textTransform: "capitalize" }}>{n.audience}</td>
                  <td>
                    <span className={`badge ${n.priority === "high" || n.priority === "urgent" ? "badge-danger" : "badge-info"}`} style={{ textTransform: "capitalize" }}>
                      {n.priority}
                    </span>
                  </td>
                  <td style={{ textAlign: "right", color: "var(--text-muted)" }}>{fmtDate(n.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
