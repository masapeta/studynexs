"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

interface StudentRow {
  id: string;
  user_id: string;
  admission_no: string;
  class_id: string;
  student_name?: string | null;
  class_name?: string | null;
}

export default function StudentsPage() {
  const [students, setStudents] = useState<StudentRow[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    fetchStudents();
  }, [page]);

  async function fetchStudents() {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: String(page),
        page_size: "15",
      });
      if (search.trim()) {
        params.set("search", search.trim());
      }
      const res = await api(`/api/v1/academic/students?${params}`);
      setStudents(res.items || res.data || []);
      setTotal(res.total || 0);
    } catch (err) {
      console.error("Fetch students error:", err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700 }}>Students</h1>
        <div style={{ display: "flex", gap: 12 }}>
          <input
            className="form-input"
            placeholder="Search students..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && fetchStudents()}
            style={{ width: 260 }}
          />
          <button className="btn btn-primary" style={{ width: "auto", padding: "10px 20px" }}>
            + Add Student
          </button>
        </div>
      </div>

      <div className="data-table-card">
        <table className="data-table">
          <thead>
            <tr>
              <th>Admission No.</th>
              <th>Student Name</th>
              <th>Class</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={5} style={{ textAlign: "center", padding: 40 }}>
                <div className="spinner" style={{ margin: "0 auto" }} />
              </td></tr>
            ) : students.length === 0 ? (
              <tr><td colSpan={5} style={{ textAlign: "center", padding: 40, color: "var(--text-muted)" }}>
                No students found
              </td></tr>
            ) : (
              students.map((s) => (
                <tr
                  key={s.id}
                  onClick={() => router.push(`/dashboard/students/${s.id}`)}
                  style={{ cursor: "pointer" }}
                >
                  <td style={{ fontWeight: 600 }}>{s.admission_no || "—"}</td>
                  <td>{s.student_name || "—"}</td>
                  <td>{s.class_name || "—"}</td>
                  <td><span className="status-dot green" />Active</td>
                  <td style={{ color: "var(--accent-dark)", fontWeight: 600, fontSize: 13 }}>View →</td>
                </tr>
              ))
            )}
          </tbody>
        </table>

        {total > 15 && (
          <div style={{ padding: "14px 22px", display: "flex", justifyContent: "space-between", alignItems: "center", borderTop: "1px solid var(--border-light)" }}>
            <span style={{ fontSize: 13, color: "var(--text-muted)" }}>
              Showing {(page - 1) * 15 + 1}–{Math.min(page * 15, total)} of {total}
            </span>
            <div style={{ display: "flex", gap: 8 }}>
              <button className="btn" style={{ padding: "6px 14px", background: "var(--bg)", border: "1px solid var(--border)" }} onClick={() => setPage(Math.max(1, page - 1))} disabled={page === 1}>
                ← Prev
              </button>
              <button className="btn" style={{ padding: "6px 14px", background: "var(--bg)", border: "1px solid var(--border)" }} onClick={() => setPage(page + 1)} disabled={page * 15 >= total}>
                Next →
              </button>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
