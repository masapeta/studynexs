"use client";

import { useAuth } from "@/lib/auth-context";
import { useEffect, useState } from "react";
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
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const today = new Date().toISOString().split("T")[0];
        const [studentsRes, classesRes, noticesRes, feesRes, attRes] = await Promise.allSettled([
          api("/api/v1/academic/students?page_size=1"),
          api("/api/v1/academic/classes?page_size=1"),
          api("/api/v1/notices"),
          api("/api/v1/fees/stats"),
          api(`/api/v1/attendance/school-summary?date=${today}`)
        ]);

        setStats({
          totalStudents: studentsRes.status === "fulfilled" ? studentsRes.value.total || 0 : 0,
          totalTeachers: 0,
          totalClasses: classesRes.status === "fulfilled" ? classesRes.value.total || 0 : 0,
          pendingFees: feesRes.status === "fulfilled" ? feesRes.value.data?.pending_amount || 0 : 0,
        });

        if (attRes.status === "fulfilled" && attRes.value.data) {
          setAttendancePercent(attRes.value.data.percentage.toString());
        }

        if (noticesRes.status === "fulfilled") {
          setNotices(noticesRes.value.data?.slice(0, 3) || []);
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
        <h2>STUDYNEXS CONNECT | ADMIN HUB</h2>
        <p>Welcome back, {user?.full_name}! Here&apos;s your school overview.</p>
        <div className="hero-decorations">📖 🎓 ✏️</div>
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

        {/* Upcoming Events */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Upcoming Events</span>
            <button className="card-menu">⋯</button>
          </div>
          <div className="event-item green">
            <div className="event-icon">📋</div>
            <div>
              <div className="event-title">Field Trip</div>
              <div className="event-subtitle">Science Museum · 10:00 AM</div>
            </div>
          </div>
          <div className="event-item orange">
            <div className="event-icon">🏆</div>
            <div>
              <div className="event-title">Sports Day</div>
              <div className="event-subtitle">Annual Sports · 8:00 AM</div>
            </div>
          </div>
        </div>

        {/* Class Progress */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Class Progress</span>
            <button className="card-menu">⋯</button>
          </div>
          <div className="progress-item">
            <div className="progress-icon" style={{ background: "var(--primary-50)" }}>📘</div>
            <div className="progress-info">
              <div className="progress-label">Grade 8-A</div>
              <div className="progress-sub">Maths</div>
            </div>
            <div className="progress-bar">
              <div className="progress-fill green" style={{ width: "85%" }} />
            </div>
          </div>
          <div className="progress-item">
            <div className="progress-icon" style={{ background: "var(--warning-light)" }}>📗</div>
            <div className="progress-info">
              <div className="progress-label">Grade 7-B</div>
              <div className="progress-sub">English</div>
            </div>
            <div className="progress-bar">
              <div className="progress-fill orange" style={{ width: "45%" }} />
            </div>
          </div>
          <div className="progress-item">
            <div className="progress-icon" style={{ background: "var(--success-light)" }}>📕</div>
            <div className="progress-info">
              <div className="progress-label">Grade 6-A</div>
              <div className="progress-sub">Science</div>
            </div>
            <div className="progress-bar">
              <div className="progress-fill green" style={{ width: "92%" }} />
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="quick-actions">
        <h3>Quick Actions</h3>
        <div className="quick-actions-row">
          <button className="btn btn-action btn-green">👨‍🎓 Add Student</button>
          <button className="btn btn-action btn-blue">📋 Create Event</button>
          <button className="btn btn-action btn-orange">🔔 Send Alert</button>
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
                  <td>{n.content?.substring(0, 40)}...</td>
                  <td>{new Date(n.created_at).toLocaleDateString()}</td>
                  <td>{n.priority}</td>
                  <td><button className="card-menu">⋯</button></td>
                </tr>
              ))
            ) : (
              <>
                <tr>
                  <td><span className="status-dot green" />Grade 8-A Maths</td>
                  <td>Science Project due 16:00</td>
                  <td>May 12, 2026</td>
                  <td>Active</td>
                  <td><button className="card-menu">⋯</button></td>
                </tr>
                <tr>
                  <td><span className="status-dot orange" />Grade 7-B English</td>
                  <td>History Essay submission</td>
                  <td>May 10, 2026</td>
                  <td>Pending</td>
                  <td><button className="card-menu">⋯</button></td>
                </tr>
                <tr>
                  <td><span className="status-dot green" />Grade 6-A Science</td>
                  <td>Lab session rescheduled</td>
                  <td>May 8, 2026</td>
                  <td>Active</td>
                  <td><button className="card-menu">⋯</button></td>
                </tr>
              </>
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
