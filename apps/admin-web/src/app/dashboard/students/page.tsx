"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Eye, UserPlus, X } from "lucide-react";
import { api, getApiErrorMessage } from "@/lib/api";
import { PageHeaderCard } from "@/components/layout/PageHeaderCard";
import { AppSelect } from "@/components/ui/AppSelect";
import { formatClassLabel, formatDob, sortClasses } from "@/lib/format";

interface StudentRow {
  id: string;
  user_id: string;
  admission_no: string;
  class_id: string;
  student_name?: string | null;
  class_name?: string | null;
  date_of_birth?: string | null;
  parent_phone?: string | null;
}

interface ClassOption {
  id: string;
  grade: string;
  section: string;
}

const btnSm: React.CSSProperties = { width: "auto", padding: "8px 18px", borderRadius: "var(--radius-full)", fontSize: 13 };
const EMPTY = { full_name: "", mobile: "", class_id: "", admission_no: "", roll_no: "" };

export default function StudentsPage() {
  const [students, setStudents] = useState<StudentRow[]>([]);
  const [classes, setClasses] = useState<ClassOption[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [listError, setListError] = useState("");
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ ...EMPTY });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const router = useRouter();

  useEffect(() => {
    const timer = setTimeout(() => {
      const next = search.trim();
      setDebouncedSearch((prev) => {
        if (prev !== next) setPage(1);
        return next;
      });
    }, 350);
    return () => clearTimeout(timer);
  }, [search]);

  const fetchStudents = useCallback(async () => {
    setLoading(true);
    setListError("");
    try {
      const params = new URLSearchParams({ page: String(page), page_size: "20" });
      if (debouncedSearch) params.set("search", debouncedSearch);
      const res = await api(`/api/v1/academic/students?${params}`);
      setStudents(res.items || res.data || []);
      setTotal(res.total || 0);
    } catch (err) {
      setListError(getApiErrorMessage(err, "Couldn't load students. Please try again."));
    } finally {
      setLoading(false);
    }
  }, [page, debouncedSearch]);

  useEffect(() => {
    fetchStudents();
  }, [fetchStudents]);

  useEffect(() => {
    api("/api/v1/academic/classes?page_size=100")
      .then((r) => setClasses(sortClasses<ClassOption>(r.items || r.data || [])))
      .catch(() => {});
  }, []);

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
      <PageHeaderCard title="Students" subtitle="Enrolled students across all classes.">
        <input
          className="form-input sn-search-inline"
          placeholder="Search students..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              setDebouncedSearch(search.trim());
              setPage(1);
            }
          }}
        />
        <button
          type="button"
          className="gw-table-icon-btn"
          aria-label={showAdd ? "Cancel add student" : "Add student"}
          title={showAdd ? "Cancel" : "Add student"}
          onClick={() => setShowAdd((v) => !v)}
        >
          {showAdd ? <X size={20} /> : <UserPlus size={20} />}
        </button>
      </PageHeaderCard>

      {error && <div className="card" style={{ marginBottom: 16, padding: 12, color: "var(--danger)" }}>{error}</div>}

      {showAdd && (
        <div className="card sn-section-gap" style={{ padding: 18, display: "grid", gridTemplateColumns: "1.5fr 1fr 1fr 1fr 0.8fr auto", gap: 12, alignItems: "end" }}>
          <div><label className="stat-label">Full name</label><input className="form-input sn-inline-field" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} /></div>
          <div><label className="stat-label">Mobile</label><input className="form-input sn-inline-field" value={form.mobile} onChange={(e) => setForm({ ...form, mobile: e.target.value })} /></div>
          <div>
            <label className="stat-label">Class</label>
            <AppSelect
              variant="field"
              value={form.class_id}
              onChange={(v) => setForm({ ...form, class_id: v })}
              aria-label="Class"
              placeholder="Select…"
              options={[
                { value: "", label: "Select…" },
                ...classes.map((c) => ({
                  value: c.id,
                  label: formatClassLabel(c.grade, c.section),
                })),
              ]}
            />
          </div>
          <div><label className="stat-label">Admission no</label><input className="form-input sn-inline-field" value={form.admission_no} onChange={(e) => setForm({ ...form, admission_no: e.target.value })} /></div>
          <div><label className="stat-label">Roll</label><input className="form-input sn-inline-field" value={form.roll_no} onChange={(e) => setForm({ ...form, roll_no: e.target.value })} /></div>
          <button className="btn btn-primary" style={btnSm} onClick={addStudent} disabled={saving}>{saving ? "Adding…" : "Add"}</button>
        </div>
      )}

      <div className="data-table-card">
        <table className="students-table" aria-label="Students">
          <colgroup>
            <col className="students-col-adm" />
            <col className="students-col-name" />
            <col className="students-col-class" />
            <col className="students-col-dob" />
            <col className="students-col-phone" />
            <col className="students-col-action" />
          </colgroup>
          <thead>
            <tr>
              <th>Admission No.</th>
              <th>Student Name</th>
              <th>Class</th>
              <th>DOB</th>
              <th>Parent Phone</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={6} className="students-table-empty">
                  <div className="spinner" style={{ margin: "0 auto" }} />
                </td>
              </tr>
            ) : listError ? (
              <tr>
                <td colSpan={6} className="students-table-empty" role="alert">
                  <span style={{ color: "var(--danger)" }}>{listError}</span>{" "}
                  <button
                    type="button"
                    className="btn btn-primary"
                    style={{ ...btnSm, marginLeft: 12 }}
                    onClick={() => fetchStudents()}
                  >
                    Retry
                  </button>
                </td>
              </tr>
            ) : students.length === 0 ? (
              <tr>
                <td colSpan={6} className="students-table-empty">No students found</td>
              </tr>
            ) : (
              students.map((s) => (
                <tr
                  key={s.id}
                  className="students-table-row"
                  tabIndex={0}
                  onClick={() => router.push(`/dashboard/students/${s.id}`)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      router.push(`/dashboard/students/${s.id}`);
                    }
                  }}
                >
                  <td className="students-table-adm">{s.admission_no || "—"}</td>
                  <td className="students-table-name">{s.student_name || "—"}</td>
                  <td>{s.class_name || "—"}</td>
                  <td className="students-table-muted">{formatDob(s.date_of_birth)}</td>
                  <td className="students-table-muted">{s.parent_phone || "—"}</td>
                  <td className="students-table-action">
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

        {total > 20 && (
          <div className="data-table-footer">
            <span>
              Showing {(page - 1) * 20 + 1}–{Math.min(page * 20, total)} of {total}
            </span>
            <div style={{ display: "flex", gap: 8 }}>
              <button className="btn" style={{ padding: "5px 12px", background: "var(--bg)", border: "1px solid var(--border)", fontSize: 13 }} onClick={() => setPage(Math.max(1, page - 1))} disabled={page === 1}>
                ← Prev
              </button>
              <button className="btn" style={{ padding: "5px 12px", background: "var(--bg)", border: "1px solid var(--border)", fontSize: 13 }} onClick={() => setPage(page + 1)} disabled={page * 20 >= total}>
                Next →
              </button>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
