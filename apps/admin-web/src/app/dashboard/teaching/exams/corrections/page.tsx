"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, getApiErrorMessage } from "@/lib/api";
import { AppSelect } from "@/components/ui/AppSelect";
import { PageHeaderCard } from "@/components/layout/PageHeaderCard";
import { formatClassLabel, sortClasses } from "@/lib/format";
import { TEACHING } from "@/lib/dashboard-routes";

export default function CorrectionsPage() {
  const [classes, setClasses] = useState<any[]>([]);
  const [classId, setClassId] = useState("");
  const [rows, setRows] = useState<any[]>([]);
  const [misconceptions, setMisconceptions] = useState<any[]>([]);
  const [students, setStudents] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api("/api/v1/academic/classes?page_size=100")
      .then((r) => {
        const items = sortClasses<any>(r.items || r.data || []);
        setClasses(items);
        if (items[0]) setClassId(items[0].id);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!classId) return;
    setLoading(true);
    setError("");
    Promise.all([
      api(`/api/v1/exams/corrections?class_id=${classId}&limit=200`),
      api(`/api/v1/exams/misconceptions?class_id=${classId}&limit=50`),
      api(`/api/v1/academic/students?class_id=${classId}&page_size=200`),
    ])
      .then(([corrRes, miscRes, stuRes]) => {
        setRows(corrRes.data || []);
        setMisconceptions(miscRes.data || []);
        const map: Record<string, string> = {};
        (stuRes.items || stuRes.data || []).forEach((s: any) => {
          map[s.id] = s.student_name || s.full_name || s.roll_no || s.id.slice(0, 8);
        });
        setStudents(map);
      })
      .catch((e) => setError(getApiErrorMessage(e, "Failed to load corrections")))
      .finally(() => setLoading(false));
  }, [classId]);

  return (
    <>
      <PageHeaderCard
        title="Past corrections"
        subtitle="Corrections, misconceptions & weak-topic signals"
      >
        <Link href={TEACHING.exams} className="btn btn-ghost gw-btn-sm">← Exams</Link>
      </PageHeaderCard>

      <div className="card sn-filter-panel">
        <label className="stat-label">Class</label>
        <AppSelect
          variant="field"
          value={classId}
          onChange={setClassId}
          aria-label="Class"
          className="sn-search-inline"
          options={classes.map((c) => ({
            value: c.id,
            label: formatClassLabel(c.grade, c.section),
          }))}
        />
      </div>

      {error && <div className="card sn-inline-alert sn-inline-alert--error">{error}</div>}

      <div className="card" style={{ padding: 0, overflow: "hidden" }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Topic</th>
              <th>Exam</th>
              <th>Student</th>
              <th>Q</th>
              <th>AI</th>
              <th>Teacher</th>
              <th>Max</th>
              <th>Feedback</th>
              <th>Override</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={9} style={{ textAlign: "center", padding: 40 }}><div className="spinner" style={{ margin: "0 auto" }} /></td></tr>
            ) : rows.length === 0 ? (
              <tr><td colSpan={9} style={{ textAlign: "center", padding: 40, color: "var(--text-muted)" }}>No approved corrections yet for this class.</td></tr>
            ) : rows.map((r, i) => (
              <tr key={`${r.evaluation_id}-${r.question_no}-${i}`}>
                <td style={{ fontSize: 13 }}>{r.topic || "—"}</td>
                <td>{r.exam_title}</td>
                <td>{students[r.student_id] || "—"}</td>
                <td style={{ fontWeight: 600 }}>{r.question_no}</td>
                <td>{r.ai_marks}</td>
                <td style={{ fontWeight: r.ai_marks !== r.teacher_marks ? 700 : 400, color: r.ai_marks !== r.teacher_marks ? "var(--primary)" : undefined }}>
                  {r.teacher_marks}
                </td>
                <td>{r.max_marks}</td>
                <td style={{ fontSize: 13, maxWidth: 220 }}>{r.ai_feedback}</td>
                <td style={{ fontSize: 12, color: "var(--text-muted)" }}>{r.override_reason || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card" style={{ marginTop: 24, padding: 0, overflow: "hidden" }}>
        <div style={{ padding: "14px 20px", borderBottom: "1px solid var(--border)", fontWeight: 700 }}>
          Misconception library
        </div>
        <table className="data-table">
          <thead>
            <tr>
              <th>Topic</th>
              <th>Q</th>
              <th>Common mistake</th>
              <th>Remedial</th>
              <th>Seen</th>
            </tr>
          </thead>
          <tbody>
            {misconceptions.length === 0 ? (
              <tr><td colSpan={5} style={{ textAlign: "center", padding: 32, color: "var(--text-muted)" }}>No misconceptions recorded yet — approve evaluations with partial marks.</td></tr>
            ) : misconceptions.map((m) => (
              <tr key={m.id}>
                <td style={{ fontWeight: 600 }}>{m.topic}</td>
                <td>{m.question_no || "—"}</td>
                <td style={{ fontSize: 13, maxWidth: 280 }}>{m.common_mistake}</td>
                <td style={{ fontSize: 13, maxWidth: 280 }}>{m.remedial_activity || "—"}</td>
                <td>{m.occurrence_count}×</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

