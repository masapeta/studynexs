"use client";

import { useCallback, useEffect, useState } from "react";
import { api, ApiError, getApiErrorMessage } from "@/lib/api";
import { formatClassLabel, sortClasses } from "@/lib/format";
import { PageShell } from "@/components/layout/PageShell";
import { StatusBadge } from "@/components/briefing/StatusBadge";

type Subject = { id: string; name: string; short: string };
type StudentRow = {
  student_id: string;
  name: string;
  marks: Record<string, number>;
  average: number | null;
  grade_letter: string | null;
};

const gradeTone: Record<string, "green" | "brass" | "blue" | "red" | "gray"> = {
  "A+": "blue",
  A: "green",
  B: "brass",
  C: "brass",
  D: "red",
  F: "red",
};

export default function GradebookPage() {
  const [classes, setClasses] = useState<{ id: string; grade: string; section: string }[]>([]);
  const [classId, setClassId] = useState("");
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [students, setStudents] = useState<StudentRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api("/api/v1/academic/classes?page_size=100")
      .then((r) => {
        const items = sortClasses<any>(r.items || r.data || []);
        setClasses(items);
        if (items[0]) setClassId(items[0].id);
      })
      .catch((e) => setError(getApiErrorMessage(e, "Failed to load classes")));
  }, []);

  const loadGradebook = useCallback(async () => {
    if (!classId) return;
    setLoading(true);
    setError("");
    try {
      const res = await api<{ data: { subjects: Subject[]; students: StudentRow[] } }>(
        `/api/v1/exams/gradebook?class_id=${classId}`
      );
      setSubjects(res.data?.subjects || []);
      setStudents(res.data?.students || []);
    } catch (e) {
      if (e instanceof ApiError && e.status === 404) {
        try {
          const roster = await api<{ items?: { id: string; student_name?: string | null }[]; data?: { id: string; student_name?: string | null }[] }>(
            `/api/v1/academic/students?class_id=${classId}&page_size=100`
          );
          const items = roster.items || roster.data || [];
          setSubjects([]);
          setStudents(
            items.map((s) => ({
              student_id: s.id,
              name: s.student_name || "—",
              marks: {},
              average: null,
              grade_letter: null,
            }))
          );
        } catch (fallbackErr) {
          setSubjects([]);
          setStudents([]);
          setError(getApiErrorMessage(fallbackErr, "Failed to load gradebook"));
        }
      } else {
        setError(getApiErrorMessage(e, "Failed to load gradebook"));
      }
    } finally {
      setLoading(false);
    }
  }, [classId]);

  useEffect(() => {
    loadGradebook();
  }, [loadGradebook]);

  const classLabel = (id: string) => {
    const c = classes.find((x) => x.id === id);
    return c ? formatClassLabel(c.grade, c.section) : id;
  };

  return (
    <PageShell title="Gradebook & Exams" subtitle="Term 1 — Mid Year · marks out of 100">
      {error && <div className="gw-alert gw-alert-error">{error}</div>}

      <div className="gw-class-tabs">
        {classes.map((c) => (
          <button
            key={c.id}
            type="button"
            className={`gw-class-tab ${classId === c.id ? "active" : ""}`}
            onClick={() => setClassId(c.id)}
          >
            {formatClassLabel(c.grade, c.section)}
          </button>
        ))}
      </div>

      <div className="gw-card" style={{ overflow: "auto" }}>
        <table className="data-table gw-table">
          <thead>
            <tr>
              <th>Student</th>
              {subjects.map((s) => (
                <th key={s.id}>{s.short}</th>
              ))}
              <th>Avg</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={subjects.length + 2} className="gw-center">
                  <div className="spinner" />
                </td>
              </tr>
            ) : students.length === 0 ? (
              <tr>
                <td colSpan={Math.max(subjects.length, 1) + 2} className="gw-muted gw-center">
                  No students in {classLabel(classId)}.
                </td>
              </tr>
            ) : (
              students.map((s) => (
                <tr key={s.student_id}>
                  <td style={{ fontWeight: 600 }}>{s.name}</td>
                  {subjects.map((sub) => (
                    <td key={sub.id}>{s.marks[sub.id] ?? "—"}</td>
                  ))}
                  <td>
                    {s.average != null && s.grade_letter ? (
                      <StatusBadge tone={gradeTone[s.grade_letter] || "gray"}>
                        {s.average} · {s.grade_letter}
                      </StatusBadge>
                    ) : (
                      "—"
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </PageShell>
  );
}
