"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, getApiErrorMessage } from "@/lib/api";

interface StudentRow {
  id: string;
  user_id: string;
  admission_no: string;
  class_id: string;
  student_name?: string | null;
  class_name?: string | null;
}

const sel: React.CSSProperties = { width: "100%", padding: "8px 12px", borderRadius: "var(--radius-sm)", border: "1px solid var(--border)", background: "white", marginTop: 4 };
const btnSm: React.CSSProperties = { width: "auto", padding: "8px 18px", borderRadius: "var(--radius-full)", fontSize: 13 };
const EMPTY = { full_name: "", mobile: "", class_id: "", admission_no: "", roll_no: "" };

export default function StudentsPage() {
  const [students, setStudents] = useState<StudentRow[]>([]);
  const [classes, setClasses] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ ...EMPTY });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const router = useRouter();

  useEffect(() => { fetchStudents(); /* eslint-disable-next-line */ }, [page]);
  useEffect(() => {
    api("/api/v1/academic/classes?page_size=100")
      .then((r) => setClasses(r.items || r.data || []))
      .catch(() => {});
  }, []);

  async function fetchStudents() {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page: String(page), page_size: "15" });
      if (search.trim()) params.set("search", search.trim());
      const res = await api(`/api/v1/academic/students?${params}`);
      setStudents(res.items || res.data || []);
      setTotal(res.total || 0);
    } catch (err) {
      console.error("Fetch students error:", err);
    } finally {
      setLoading(false);
    }
  }

  async function addStudent() {
    if (!form.full_name.trim() || !form.mobile.trim() || !form.class_id || !form.admission_no.trim()) {
      setError("Name, mobile, class and admission number are required.");
      return;
    }
    setSaving(true);
    setError("");
    try {
      // Enrollment is two-step: create the user account, then the student record.
      const userRes = await api<{ data: { id: string } }>("/api/v1/users", {
        method: "POST",
        body: JSON.stringify({ full_name: form.full_name, mobile: form.mobile, role: "student" }),
      });
      await api("/api/v1/academic/students/enroll", {
        method: "POST",
        body: JSON.stringify({
          user_id: userRes.data.id,
          class_id: form.class_id,
          admission_no: form.admission_no,
          roll_no: form.roll_no || null,
        }),
      });
      setForm({ ...EMPTY });
      setShowAdd(false);
      setPage(1);
      fetchStudents();
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to add student"));
    } finally {
      setSaving(false);
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
          <button className="btn btn-primary" style={{ width: "auto", padding: "10px 20px" }} onClick={() => setShowAdd((v) => !v)}>
            {showAdd ? "Cancel" : "+ Add Student"}
          </button>
        </div>
      </div>

      {error && <div className="card" style={{ marginBottom: 16, padding: 12, color: "var(--danger)" }}>{error}</div>}

      {showAdd && (
        <div className="card" style={{ marginBottom: 20, padding: 24, display: "grid", gridTemplateColumns: "1.5fr 1fr 1fr 1fr 0.8fr auto", gap: 12, alignItems: "end" }}>
          <div><label className="stat-label">Full name</label><input className="form-input" style={sel} value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} /></div>
          <div><label className="stat-label">Mobile</label><input className="form-input" style={sel} value={form.mobile} onChange={(e) => setForm({ ...form, mobile: e.target.value })} /></div>
          <div>
            <label className="stat-label">Class</label>
            <select className="form-input" style={sel} value={form.class_id} onChange={(e) => setForm({ ...form, class_id: e.target.value })}>
              <option value="">Select…</option>
              {classes.map((c) => <option key={c.id} value={c.id}>{c.grade} - {c.section}</option>)}
            </select>
          </div>
          <div><label className="stat-label">Admission no</label><input className="form-input" style={sel} value={form.admission_no} onChange={(e) => setForm({ ...form, admission_no: e.target.value })} /></div>
          <div><label className="stat-label">Roll</label><input className="form-input" style={sel} value={form.roll_no} onChange={(e) => setForm({ ...form, roll_no: e.target.value })} /></div>
          <button className="btn btn-primary" style={btnSm} onClick={addStudent} disabled={saving}>{saving ? "Adding…" : "Add"}</button>
        </div>
      )}

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
