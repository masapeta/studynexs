"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Plus } from "lucide-react";
import { api, getApiErrorMessage } from "@/lib/api";
import { formatClassLabel, sortClasses } from "@/lib/format";
import { AppSelect } from "@/components/ui/AppSelect";
import MarksGrid from "./MarksGrid";
import QuestionSchemaEditor from "./QuestionSchemaEditor";
import { TEACHING } from "@/lib/dashboard-routes";
import { EXAM_TYPE_OPTIONS, examTypeLabel } from "@/lib/exam-types";

type ClassSummary = { id: string; grade: string; section: string };
type SubjectSummary = { id: string; name: string };
type ExamSummary = {
  id: string;
  class_id: string;
  subject_id: string;
  exam_type: string;
  title: string;
  total_marks: number | string;
  topic?: string | null;
  has_question_schema: boolean;
  can_evaluate_sheets: boolean;
};
type StudentSummary = {
  id: string;
  roll_no?: string | null;
  student_name?: string | null;
};
type QuestionSummary = { no: string; max_marks: number; topic?: string | null };
type ExamMarkSummary = {
  student_id: string;
  marks_obtained: number | string;
  question_marks?: Record<string, number> | null;
};
type ListResponse<T> = T[] | { items?: T[]; data?: T[] };

function responseItems<T>(response: ListResponse<T>): T[] {
  return Array.isArray(response) ? response : response.items || response.data || [];
}

export default function ExamsPage() {
  const [classes, setClasses] = useState<ClassSummary[]>([]);
  const [subjects, setSubjects] = useState<SubjectSummary[]>([]);
  const [classId, setClassId] = useState("");
  const [exams, setExams] = useState<ExamSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({
    subject_id: "",
    exam_type: "slip_test",
    title: "",
    total_marks: 100,
    exam_date: new Date().toISOString().split("T")[0],
    topic: "",
  });
  const [creating, setCreating] = useState(false);

  const [activeExam, setActiveExam] = useState<ExamSummary | null>(null);
  const [schemaExam, setSchemaExam] = useState<ExamSummary | null>(null);
  const [students, setStudents] = useState<StudentSummary[]>([]);
  const [marks, setMarks] = useState<Record<string, string>>({});
  const [questions, setQuestions] = useState<QuestionSummary[]>([]);
  const [questionMarks, setQuestionMarks] = useState<Record<string, Record<string, number>>>({});
  const [savingMarks, setSavingMarks] = useState(false);

  const loadExams = useCallback(() => {
    if (!classId) return;
    api<{ data?: ExamSummary[] }>(`/api/v1/exams?class_id=${classId}`)
      .then((response) => setExams(response.data || []))
      .catch((caught) => setError(getApiErrorMessage(caught, "Failed to load exams")))
      .finally(() => setLoading(false));
  }, [classId]);

  useEffect(() => {
    api<ListResponse<ClassSummary>>("/api/v1/academic/classes?page_size=100")
      .then((response) => {
        const raw = responseItems(response);
        const items = sortClasses(raw);
        setClasses(items);
        if (items[0]) {
          setLoading(true);
          setClassId(items[0].id);
        }
      })
      .catch((e) => console.error(e));
  }, []);

  useEffect(() => {
    if (!classId) return;
    api<ListResponse<SubjectSummary>>(`/api/v1/academic/subjects?class_id=${classId}`)
      .then((response) => {
        const items = responseItems(response);
        setSubjects(items);
        setForm((f) => ({ ...f, subject_id: items[0]?.id || "" }));
      })
      .catch((e) => console.error(e));
    loadExams();
  }, [classId, loadExams]);

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
          topic: form.topic.trim() || null,
        }),
      });
      setShowCreate(false);
      setForm((f) => ({ ...f, title: "", topic: "" }));
      setLoading(true);
      loadExams();
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to create exam"));
    } finally {
      setCreating(false);
    }
  }

  async function openMarks(exam: ExamSummary) {
    setActiveExam(exam);
    setSchemaExam(null);
    setError("");
    try {
      const stuRes = await api<ListResponse<StudentSummary>>(
        `/api/v1/academic/students?class_id=${exam.class_id}&page_size=100`
      );
      const stus = responseItems(stuRes);
      setStudents(stus);

      const mkRes = await api<{ data?: ExamMarkSummary[] }>(`/api/v1/exams/${exam.id}/marks`);
      const existing = mkRes.data || [];

      if (exam.has_question_schema) {
        const qRes = await api<{ data?: QuestionSummary[] }>(
          `/api/v1/exams/${exam.id}/questions`
        );
        setQuestions(qRes.data || []);
        const qm: Record<string, Record<string, number>> = {};
        existing.forEach((x) => {
          if (x.question_marks) qm[x.student_id] = x.question_marks;
        });
        setQuestionMarks(qm);
      } else {
        setQuestions([]);
        const map: Record<string, string> = {};
        stus.forEach((s) => {
          const m = existing.find((x) => x.student_id === s.id);
          map[s.id] = m ? String(m.marks_obtained) : "";
        });
        setMarks(map);
      }
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

  async function saveQuestionMarks(
    entries: { student_id: string; question_marks: Record<string, number> }[]
  ) {
    if (!activeExam) return;
    setSavingMarks(true);
    setError("");
    try {
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
      <div className="card bento-glass gw-toolbar">
        <h1 className="gw-toolbar-title">Exams &amp; Marks</h1>
        <div className="gw-toolbar-actions">
          <Link href={TEACHING.corrections} className="gw-toolbar-link">
            Past corrections
          </Link>
          <AppSelect
            variant="pill"
            value={classId}
            onChange={(nextClassId) => {
              setActiveExam(null);
              setSchemaExam(null);
              setLoading(true);
              setClassId(nextClassId);
            }}
            aria-label="Select class and section"
            options={classes.map((c) => ({
              value: c.id,
              label: formatClassLabel(c.grade, c.section),
            }))}
          />
          {!activeExam && (
            <button
              type="button"
              className="btn btn-primary gw-btn-sm gw-toolbar-btn"
              onClick={() => setShowCreate((v) => !v)}
            >
              {showCreate ? (
                "Cancel"
              ) : (
                <>
                  <Plus size={16} aria-hidden />
                  New exam
                </>
              )}
            </button>
          )}
          {activeExam && (
            <button
              type="button"
              className="btn btn-ghost gw-btn-sm gw-toolbar-btn"
              onClick={() => setActiveExam(null)}
            >
              ← Back to exams
            </button>
          )}
        </div>
      </div>

      {error && <div className="card" style={{ marginBottom: 16, padding: 12, color: "var(--danger)" }}>{error}</div>}

      {showCreate && !activeExam && (
        <div className="card" style={{ marginBottom: 24, padding: 24, display: "grid", gridTemplateColumns: "2fr 1fr 1fr 1fr 1fr auto", gap: 12, alignItems: "end" }}>
          <div>
            <label className="stat-label">Title</label>
            <input className="form-input sn-inline-field" value={form.title} placeholder="Algebra Slip Test" onChange={(e) => setForm({ ...form, title: e.target.value })} />
          </div>
          <div>
            <label className="stat-label">Subject</label>
            <AppSelect
              variant="field"
              value={form.subject_id}
              onChange={(v) => setForm({ ...form, subject_id: v })}
              aria-label="Subject"
              options={subjects.map((s) => ({ value: s.id, label: s.name }))}
            />
          </div>
          <div>
            <label className="stat-label">Type</label>
            <AppSelect
              variant="field"
              value={form.exam_type}
              onChange={(v) => setForm({ ...form, exam_type: v })}
              aria-label="Exam type"
              options={EXAM_TYPE_OPTIONS}
            />
          </div>
          <div>
            <label className="stat-label">Max marks</label>
            <input type="number" className="form-input sn-inline-field" value={form.total_marks} onChange={(e) => setForm({ ...form, total_marks: Number(e.target.value) })} />
          </div>
          <div>
            <label className="stat-label">Chapter / Topic</label>
            <input className="form-input sn-inline-field" value={form.topic} placeholder="e.g. Algebra" onChange={(e) => setForm({ ...form, topic: e.target.value })} />
          </div>
          <button className="btn btn-primary" style={btn} onClick={createExam} disabled={creating}>
            {creating ? "Creating…" : "Create"}
          </button>
        </div>
      )}

      {schemaExam && !activeExam && (
        <QuestionSchemaEditor
          exam={schemaExam}
          onCancel={() => setSchemaExam(null)}
          onSaved={(updated) => {
            setSchemaExam(null);
            setExams((es) => es.map((e) => (e.id === updated.id ? { ...e, ...updated } : e)));
          }}
        />
      )}

      {activeExam ? (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <div style={{ padding: "14px 24px", display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid var(--border)" }}>
            <div>
              <div style={{ fontWeight: 700 }}>{activeExam.title}</div>
              <div style={{ fontSize: 13, color: "var(--text-muted)" }}>
                {examTypeLabel(activeExam.exam_type)} · {subjName(activeExam.subject_id)} · Max {activeExam.total_marks}
                {activeExam.topic ? ` · ${activeExam.topic}` : ""}
                {activeExam.has_question_schema ? " · per-question" : ""}
              </div>
            </div>
            {!activeExam.has_question_schema && (
              <button className="btn btn-primary" style={btn} onClick={saveMarks} disabled={savingMarks || students.length === 0}>
                {savingMarks ? "Saving…" : "Save Marks"}
              </button>
            )}
          </div>
          {students.length === 0 ? (
            <div style={{ textAlign: "center", padding: 32, color: "var(--text-muted)" }}>No students in this class.</div>
          ) : activeExam.has_question_schema ? (
            <MarksGrid
              students={students}
              questions={questions}
              initialMarks={questionMarks}
              onSave={saveQuestionMarks}
              saving={savingMarks}
            />
          ) : (
            <table className="data-table">
              <thead><tr><th>Roll</th><th>Student</th><th style={{ textAlign: "right" }}>Marks (/ {activeExam.total_marks})</th></tr></thead>
              <tbody>
                {students.map((s) => (
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
          )}
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
                  <td>{examTypeLabel(e.exam_type)}</td>
                  <td>{subjName(e.subject_id)}</td>
                  <td>{e.total_marks}</td>
                  <td style={{ textAlign: "right", whiteSpace: "nowrap" }}>
                    <button className="btn btn-ghost" style={btn} onClick={() => setSchemaExam(e)}>
                      {e.has_question_schema ? "Questions ✓" : "Questions"}
                    </button>{" "}
                    {e.can_evaluate_sheets && (
                      <a className="btn btn-ghost" style={btn} href={TEACHING.evaluate(e.id)}>Evaluate</a>
                    )}{" "}
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

const btn: React.CSSProperties = { width: "auto", padding: "8px 18px", borderRadius: "var(--radius-full)", fontSize: 13 };
