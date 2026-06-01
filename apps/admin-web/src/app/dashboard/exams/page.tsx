"use client";

import { useEffect, useState } from "react";
import { api, getApiErrorMessage } from "@/lib/api";

const EXAM_TYPES = ["unit_test", "mid_term", "final", "assignment", "quiz"];
const pretty = (s: string) => s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

export default function ExamsPage() {
  const [classes, setClasses] = useState<any[]>([]);
  const [subjects, setSubjects] = useState<any[]>([]);
  const [classId, setClassId] = useState("");
  const [exams, setExams] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({
    subject_id: "",
    exam_type: "unit_test",
    title: "",
    total_marks: 100,
    exam_date: new Date().toISOString().split("T")[0],
  });
  const [creating, setCreating] = useState(false);

  const [activeExam, setActiveExam] = useState<any>(null);
  const [students, setStudents] = useState<any[]>([]);
  const [marks, setMarks] = useState<Record<string, string>>({});
  const [savingMarks, setSavingMarks] = useState(false);

  useEffect(() => {
    api("/api/v1/academic/classes?page_size=100")
      .then((r) => {
        const items = r.items || r.data || [];
        setClasses(items);
        if (items[0]) setClassId(items[0].id);
      })
      .catch((e) => console.error(e));
  }, []);

  useEffect(() => {
    if (!classId) return;
    setActiveExam(null);
    api(`/api/v1/academic/subjects?class_id=${classId}`)
      .then((r) => {
        const items = r.items || r.data || (Array.isArray(r) ? r : []);
        setSubjects(items);
        setForm((f) => ({ ...f, subject_id: items[0]?.id || "" }));
      })
      .catch((e) => console.error(e));
    loadExams();
  }, [classId]);

  function loadExams() {
    setLoading(true);
    api(`/api/v1/exams?class_id=${classId}`)
      .then((r) => setExams(r.data || []))
      .catch((e) => setError(getApiErrorMessage(e, "Failed to load exams")))
      .finally(() => setLoading(false));
  }

  async function createExam() {
    if (!form.subject_id || !form.title) {
      setError("Pick a subject and enter a title.");
      return;
    }
    setCreating(true);
    setError("");
    try {
      await api("/api/v1/exams", {
        method: "POST",
        body: JSON.stringify({
          class_id: classId,
          subject_id: form.subject_id,
          exam_type: form.exam_type,
          title: form.title,
          total_marks: Number(form.total_marks),
          exam_date: form.exam_date || null,
        }),
      });
      setShowCreate(false);
      setForm((f) => ({ ...f, title: "" }));
      loadExams();
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to create exam"));
    } finally {
      setCreating(false);
    }
  }

  async function openMarks(exam: any) {
    setActiveExam(exam);
    setError("");
    try {
      const stuRes = await api(`/api/v1/academic/students?class_id=${exam.class_id}&page_size=100`);
      const stus = stuRes.items || stuRes.data || [];
      setStudents(stus);
      const mkRes = await api(`/api/v1/exams/${exam.id}/marks`);
      const existing = mkRes.data || [];
      const map: Record<string, string> = {};
      stus.forEach((s: any) => {
        const m = existing.find((x: any) => x.student_id === s.id);
        map[s.id] = m ? String(m.marks_obtained) : "";
      });
      setMarks(map);
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to load marks"));
    }
  }

  async function saveMarks() {
    if (!activeExam) return;
    setSavingMarks(true);
    setError("");
    try {
      const entries = Object.entries(marks)
        .filter(([, v]) => v !== "" && !isNaN(Number(v)))
        .map(([student_id, v]) => ({ student_id, marks_obtained: Number(v) }));
      await api("/api/v1/exams/marks", {
        method: "POST",
        body: JSON.stringify({ exam_id: activeExam.id, entries }),
      });
      alert(`Saved marks for ${entries.length} students.`);
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to save marks"));
    } finally {
      setSavingMarks(false);
    }
  }

  const subjName = (id: string) => subjects.find((s) => s.id === id)?.name || "—";

  return (
    <>
      <div className="card bento-glass" style={{ marginBottom: 24, display: "flex", justifyContent: "space-between", alignItems: "center", padding: "16px 24px" }}>
        <h1 style={{ fontSize: 20, fontWeight: 700, margin: 0 }}>Exams &amp; Marks</h1>
        <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
          <select className="form-input" value={classId} onChange={(e) => setClassId(e.target.value)} style={sel}>
            {classes.map((c) => (
              <option key={c.id} value={c.id}>{c.grade} - {c.section}</option>
            ))}
          </select>
          {!activeExam && (
            <button className="btn btn-primary" style={btn} onClick={() => setShowCreate((v) => !v)}>
              {showCreate ? "Cancel" : "+ New Exam"}
            </button>
          )}
          {activeExam && (
            <button className="btn btn-ghost" style={btn} onClick={() => setActiveExam(null)}>← Back to exams</button>
          )}
        </div>
      </div>

      {error && <div className="card" style={{ marginBottom: 16, padding: 12, color: "var(--danger)" }}>{error}</div>}

      {showCreate && !activeExam && (
        <div className="card" style={{ marginBottom: 24, padding: 24, display: "grid", gridTemplateColumns: "2fr 1fr 1fr 1fr auto", gap: 12, alignItems: "end" }}>
          <div>
            <label className="stat-label">Title</label>
            <input className="form-input" style={sel} value={form.title} placeholder="Unit Test 1" onChange={(e) => setForm({ ...form, title: e.target.value })} />
          </div>
          <div>
            <label className="stat-label">Subject</label>
            <select className="form-input" style={sel} value={form.subject_id} onChange={(e) => setForm({ ...form, subject_id: e.target.value })}>
              {subjects.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
          </div>
          <div>
            <label className="stat-label">Type</label>
            <select className="form-input" style={sel} value={form.exam_type} onChange={(e) => setForm({ ...form, exam_type: e.target.value })}>
              {EXAM_TYPES.map((t) => <option key={t} value={t}>{pretty(t)}</option>)}
            </select>
          </div>
          <div>
            <label className="stat-label">Max marks</label>
            <input type="number" className="form-input" style={sel} value={form.total_marks} onChange={(e) => setForm({ ...form, total_marks: Number(e.target.value) })} />
          </div>
          <button className="btn btn-primary" style={btn} onClick={createExam} disabled={creating}>
            {creating ? "Creating…" : "Create"}
          </button>
        </div>
      )}

      {activeExam ? (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <div style={{ padding: "14px 24px", display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid var(--border)" }}>
            <div>
              <div style={{ fontWeight: 700 }}>{activeExam.title}</div>
              <div style={{ fontSize: 13, color: "var(--text-muted)" }}>{pretty(activeExam.exam_type)} · {subjName(activeExam.subject_id)} · Max {activeExam.total_marks}</div>
            </div>
            <button className="btn btn-primary" style={btn} onClick={saveMarks} disabled={savingMarks || students.length === 0}>
              {savingMarks ? "Saving…" : "Save Marks"}
            </button>
          </div>
          <table className="data-table">
            <thead><tr><th>Roll</th><th>Student</th><th style={{ textAlign: "right" }}>Marks (/ {activeExam.total_marks})</th></tr></thead>
            <tbody>
              {students.length === 0 ? (
                <tr><td colSpan={3} style={{ textAlign: "center", padding: 32, color: "var(--text-muted)" }}>No students in this class.</td></tr>
              ) : students.map((s) => (
                <tr key={s.id}>
                  <td style={{ fontWeight: 600 }}>{s.roll_no || "—"}</td>
                  <td>{s.student_name || "—"}</td>
                  <td style={{ textAlign: "right" }}>
                    <input
                      type="number"
                      value={marks[s.id] ?? ""}
                      onChange={(e) => setMarks({ ...marks, [s.id]: e.target.value })}
                      style={{ width: 90, padding: "6px 10px", borderRadius: "var(--radius-sm)", border: "1px solid var(--border)", textAlign: "right" }}
                      max={activeExam.total_marks}
                      min={0}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <table className="data-table">
            <thead><tr><th>Title</th><th>Type</th><th>Subject</th><th>Max</th><th style={{ textAlign: "right" }}>Action</th></tr></thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={5} style={{ textAlign: "center", padding: 40 }}><div className="spinner" style={{ margin: "0 auto" }} /></td></tr>
              ) : exams.length === 0 ? (
                <tr><td colSpan={5} style={{ textAlign: "center", padding: 40, color: "var(--text-muted)" }}>No exams yet for this class. Create one above.</td></tr>
              ) : exams.map((e) => (
                <tr key={e.id}>
                  <td style={{ fontWeight: 600 }}>{e.title}</td>
                  <td>{pretty(e.exam_type)}</td>
                  <td>{subjName(e.subject_id)}</td>
                  <td>{e.total_marks}</td>
                  <td style={{ textAlign: "right" }}>
                    <button className="btn btn-ghost" style={btn} onClick={() => openMarks(e)}>Enter marks</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}

const sel: React.CSSProperties = { width: "100%", padding: "8px 12px", borderRadius: "var(--radius-sm)", border: "1px solid var(--border)", background: "white", marginTop: 4 };
const btn: React.CSSProperties = { width: "auto", padding: "8px 18px", borderRadius: "var(--radius-full)", fontSize: 13 };
