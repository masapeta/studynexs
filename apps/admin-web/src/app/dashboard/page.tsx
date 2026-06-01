"use client";

import { useAuth } from "@/lib/auth-context";
import { useEffect, useState } from "react";
import Link from "next/link";
import { GraduationCap, Users, BookOpen, UserPlus, ClipboardCheck, Megaphone } from "lucide-react";
import { api } from "@/lib/api";

interface DashboardStats {
  totalStudents: number;
  totalTeachers: number;
  totalClasses: number;
  pendingFees: number;
}

export default function DashboardPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState<DashboardStats>({
    totalStudents: 0,
    totalTeachers: 0,
    totalClasses: 0,
    pendingFees: 0,
  });
  const [attendancePercent, setAttendancePercent] = useState<string>("0");
  const [notices, setNotices] = useState<any[]>([]);
  const [classPerf, setClassPerf] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const today = new Date().toISOString().split("T")[0];
        const [studentsRes, classesRes, teachersRes, noticesRes, feesRes, attRes, perfRes] =
          await Promise.allSettled([
            api("/api/v1/academic/students?page_size=1"),
            api("/api/v1/academic/classes?page_size=1"),
            api("/api/v1/users?role=teacher&page_size=1"),
            api("/api/v1/notices"),
            api("/api/v1/fees/stats"),
            api(`/api/v1/attendance/school-summary?date=${today}`),
            api("/api/v1/exams/class-performance?limit=3"),
          ]);

        setStats({
          totalStudents: studentsRes.status === "fulfilled" ? studentsRes.value.total || 0 : 0,
          totalTeachers: teachersRes.status === "fulfilled" ? teachersRes.value.total || 0 : 0,
          totalClasses: classesRes.status === "fulfilled" ? classesRes.value.total || 0 : 0,
          pendingFees: feesRes.status === "fulfilled" ? feesRes.value.data?.pending_amount || 0 : 0,
        });

        if (attRes.status === "fulfilled" && attRes.value.data) {
          setAttendancePercent(attRes.value.data.percentage.toString());
        }
        if (noticesRes.status === "fulfilled") {
          setNotices(noticesRes.value.data?.slice(0, 4) || []);
        }
        if (perfRes.status === "fulfilled") {
          setClassPerf(perfRes.value.data || []);
        }
      } catch (err) {
        console.error("Dashboard fetch error:", err);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="loading-screen" style={{ minHeight: "60vh" }}>
        <div className="spinner" />
      </div>
    );
  }

  return (
    <>
      {/* Hero Banner */}
      <div className="hero-banner">
        <h2>Welcome back, {user?.full_name?.split(" ")[0] || "there"}</h2>
        <p>Here&apos;s your school at a glance today.</p>
        <div className="hero-decorations"><GraduationCap size={76} strokeWidth={1.1} /></div>
      </div>

      {/* Stats Grid */}
      <div className="dashboard-grid">
        {/* Daily Overview */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Daily Overview</span>
            <button className="card-menu">⋯</button>
          </div>
          <div className="stat-row">
            <div className="stat-box">
              <div className="stat-label">Total Attendance</div>
              <div className="stat-value">{attendancePercent}%</div>
            </div>
            <div className="stat-box warning">
              <div className="stat-label">Pending Fees</div>
              <div className="stat-value warning">₹ {stats.pendingFees.toLocaleString()}</div>
            </div>
          </div>
        </div>

        {/* School at a Glance */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">School at a Glance</span>
            <button className="card-menu">⋯</button>
          </div>
          <div className="event-item green">
            <div className="event-icon"><GraduationCap size={18} color="var(--success)" /></div>
            <div>
              <div className="event-title">{stats.totalStudents} Students</div>
              <div className="event-subtitle">Enrolled across {stats.totalClasses} classes</div>
            </div>
          </div>
          <div className="event-item orange">
            <div className="event-icon"><Users size={18} color="var(--accent-dark)" /></div>
            <div>
              <div className="event-title">{stats.totalTeachers} Teaching staff</div>
              <div className="event-subtitle">Active this academic year</div>
            </div>
          </div>
        </div>

        {/* Class Progress */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Class Progress</span>
            <button className="card-menu">⋯</button>
          </div>
          {classPerf.length > 0 ? (
            classPerf.map((c: any, i: number) => (
              <div className="progress-item" key={c.label}>
                <div
                  className="progress-icon"
                  style={{ background: ["var(--primary-50)", "var(--accent-50)", "var(--success-light)"][i % 3] }}
                >
                  <BookOpen size={15} color={["var(--text-secondary)", "var(--accent-dark)", "var(--success)"][i % 3]} />
                </div>
                <div className="progress-info">
                  <div className="progress-label">{c.label}</div>
                  <div className="progress-sub">Overall average</div>
                </div>
                <div className="progress-bar">
                  <div
                    className={`progress-fill ${c.percentage >= 60 ? "green" : "orange"}`}
                    style={{ width: `${Math.min(100, c.percentage)}%` }}
                  />
                </div>
              </div>
            ))
          ) : (
            <div style={{ color: "var(--text-muted)", fontSize: 13, padding: "8px 0" }}>
              No exam data yet.
            </div>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="quick-actions">
        <h3>Quick Actions</h3>
        <div className="quick-actions-row">
          <Link href="/dashboard/students" className="btn btn-action"><UserPlus size={16} /> Add Student</Link>
          <Link href="/dashboard/attendance" className="btn btn-action"><ClipboardCheck size={16} /> Mark Attendance</Link>
          <Link href="/dashboard/notices" className="btn btn-action"><Megaphone size={16} /> Post Notice</Link>
        </div>
      </div>

      {/* Recent Notices Table */}
      <div className="data-table-card">
        <div className="data-table-header">
          <h3>Recent Notices</h3>
          <button className="card-menu">⋯</button>
        </div>
        <table className="data-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Notice</th>
              <th>Date</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {notices.length > 0 ? (
              notices.map((n: any) => (
                <tr key={n.id}>
                  <td>
                    <span className="status-dot green" />
                    {n.title}
                  </td>
                  <td>{n.content?.substring(0, 50)}…</td>
                  <td>{n.created_at ? new Date(n.created_at).toLocaleDateString() : "—"}</td>
                  <td style={{ textTransform: "capitalize" }}>{n.priority}</td>
                  <td><button className="card-menu">⋯</button></td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={5} style={{ color: "var(--text-muted)", textAlign: "center", padding: "16px" }}>
                  No notices yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
