"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { api, getApiErrorMessage } from "@/lib/api";

type ClassInfo = {
  id: string;
  grade: string;
  section: string;
  student_count?: number;
  attendance_pct?: number | null;
  avg_score?: number | null;
};

type RosterRow = {
  id: string;
  admission_no: string;
  roll_no?: string | null;
  student_name?: string | null;
  attendance_pct?: number | null;
};

function attColor(pct: number | null | undefined): string {
  if (pct == null) return "var(--text-muted)";
  if (pct >= 90) return "var(--success)";
  if (pct >= 75) return "var(--warning)";
  return "var(--danger)";
}

export default function ClassDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [cls, setCls] = useState<ClassInfo | null>(null);
  const [roster, setRoster] = useState<RosterRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    setError("");
    Promise.all([
      api(`/api/v1/academic/classes/${id}`),
      api(`/api/v1/academic/classes/${id}/roster`),
    ])
      .then(([classRes, rosterRes]) => {
        setCls(classRes.data ?? classRes);
        setRoster(rosterRes.data ?? rosterRes ?? []);
      })
      .catch((e) => setError(getApiErrorMessage(e, "Failed to load class")))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="loading-screen" style={{ minHeight: "50vh" }}>
        <div className="spinner" />
      </div>
    );
  }

  if (error || !cls) {
    return (
      <div className="card" style={{ padding: 32, textAlign: "center" }}>
        <p style={{ color: "var(--danger)", marginBottom: 16 }}>{error || "Class not found"}</p>
        <button type="button" className="btn btn-outline" onClick={() => router.push("/dashboard/classes")}>
          Back to classes
        </button>
      </div>
    );
  }

  const title = `${cls.grade} - ${cls.section}`;

  return (
    <>
      <button
        type="button"
        className="btn btn-ghost"
        onClick={() => router.push("/dashboard/classes")}
        style={{ width: "auto", padding: "6px 0", marginBottom: 16, display: "flex", alignItems: "center", gap: 6 }}
      >
        <ArrowLeft size={16} /> Back to classes
      </button>

      <div className="card bento-glass" style={{ marginBottom: 20, padding: "16px 24px" }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, margin: 0 }}>{title}</h1>
        <p style={{ margin: "6px 0 0", color: "var(--text-muted)", fontSize: 13 }}>
          {roster.length} students · class attendance{" "}
          {cls.attendance_pct != null ? `${cls.attendance_pct}%` : "—"}
          {cls.avg_score != null ? ` · avg score ${cls.avg_score}%` : ""}
        </p>
      </div>

      <div className="data-table-card">
        <table className="data-table">
          <thead>
            <tr>
              <th>Roll</th>
              <th>Admission No.</th>
              <th>Student</th>
              <th>Attendance %</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {roster.length === 0 ? (
              <tr>
                <td colSpan={5} style={{ textAlign: "center", padding: 40, color: "var(--text-muted)" }}>
                  No students in this class.
                </td>
              </tr>
            ) : (
              roster.map((s) => (
                <tr
                  key={s.id}
                  onClick={() => router.push(`/dashboard/students/${s.id}`)}
                  style={{ cursor: "pointer" }}
                >
                  <td>{s.roll_no || "—"}</td>
                  <td style={{ fontWeight: 600 }}>{s.admission_no}</td>
                  <td>{s.student_name || "—"}</td>
                  <td>
                    <span style={{ fontWeight: 700, color: attColor(s.attendance_pct) }}>
                      {s.attendance_pct != null ? `${s.attendance_pct}%` : "—"}
                    </span>
                  </td>
                  <td style={{ color: "var(--accent-dark)", fontWeight: 600, fontSize: 13 }}>View →</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
