"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Eye } from "lucide-react";
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
  const [search, setSearch] = useState("");
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
  const query = search.trim().toLowerCase();
  const filteredRoster = query
    ? roster.filter(
        (s) =>
          s.student_name?.toLowerCase().includes(query) ||
          s.admission_no?.toLowerCase().includes(query),
      )
    : roster;

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

      <div className="card bento-glass sn-section-gap" style={{ padding: "12px 18px" }}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            gap: 16,
            flexWrap: "wrap",
          }}
        >
          <div>
            <h1 className="sn-page-title">{title}</h1>
            <p style={{ margin: "6px 0 0", color: "var(--text-muted)", fontSize: 13 }}>
              {query
                ? `${filteredRoster.length} of ${roster.length} students`
                : `${roster.length} students`}
              {" · class attendance "}
              {cls.attendance_pct != null ? `${cls.attendance_pct}%` : "—"}
              {cls.avg_score != null ? ` · avg score ${cls.avg_score}%` : ""}
            </p>
          </div>
          <input
            className="form-input"
            placeholder="Search by name or admission no..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ width: 260 }}
            aria-label="Search students by name or admission number"
          />
        </div>
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
            ) : filteredRoster.length === 0 ? (
              <tr>
                <td colSpan={5} style={{ textAlign: "center", padding: 40, color: "var(--text-muted)" }}>
                  No students match &ldquo;{search.trim()}&rdquo;.
                </td>
              </tr>
            ) : (
              filteredRoster.map((s) => (
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
                  <td>
                    <button
                      type="button"
                      className="gw-table-icon-btn"
                      aria-label={`View ${s.student_name || s.admission_no}`}
                      onClick={(e) => {
                        e.stopPropagation();
                        router.push(`/dashboard/students/${s.id}`);
                      }}
                    >
                      <Eye size={16} />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
