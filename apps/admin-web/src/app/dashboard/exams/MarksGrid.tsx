"use client";

import { useEffect, useRef, useState } from "react";

type Question = { no: string; max_marks: number; topic?: string | null };

/**
 * Fast per-question marks entry: rows = students, columns = questions.
 * Keyboard: Enter/↓ next student (same question), ↑ previous, Tab/→ next question.
 * Blank cell = unattempted (internal choice); fully blank row = not submitted.
 * Explicit save — teachers transcribe from a paper stack, one save per stack.
 */
export default function MarksGrid({
  students,
  questions,
  initialMarks,
  onSave,
  saving,
}: {
  students: any[];
  questions: Question[];
  initialMarks: Record<string, Record<string, number>>;
  onSave: (entries: { student_id: string; question_marks: Record<string, number> }[]) => void;
  saving: boolean;
}) {
  const [grid, setGrid] = useState<Record<string, Record<string, string>>>({});
  const [dirty, setDirty] = useState(false);
  const inputs = useRef<Record<string, HTMLInputElement | null>>({});

  useEffect(() => {
    const g: Record<string, Record<string, string>> = {};
    students.forEach((s) => {
      g[s.id] = {};
      questions.forEach((q) => {
        const v = initialMarks[s.id]?.[q.no];
        g[s.id][q.no] = v === undefined || v === null ? "" : String(v);
      });
    });
    setGrid(g);
    setDirty(false);
  }, [students, questions, initialMarks]);

  useEffect(() => {
    if (!dirty) return;
    const warn = (e: BeforeUnloadEvent) => {
      e.preventDefault();
    };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [dirty]);

  function setCell(studentId: string, qno: string, value: string) {
    setGrid((g) => ({ ...g, [studentId]: { ...g[studentId], [qno]: value } }));
    setDirty(true);
  }

  function onKeyDown(e: React.KeyboardEvent, row: number, col: number) {
    let target: string | null = null;
    if (e.key === "Enter" || e.key === "ArrowDown") target = `${row + 1}-${col}`;
    else if (e.key === "ArrowUp") target = `${row - 1}-${col}`;
    else if (e.key === "ArrowRight") target = `${row}-${col + 1}`;
    else if (e.key === "ArrowLeft") target = `${row}-${col - 1}`;
    if (target && inputs.current[target]) {
      e.preventDefault();
      inputs.current[target]!.focus();
      inputs.current[target]!.select();
    }
  }

  const maxByNo: Record<string, number> = {};
  questions.forEach((q) => (maxByNo[q.no] = q.max_marks));

  const rowTotal = (studentId: string) =>
    Object.entries(grid[studentId] || {})
      .filter(([, v]) => v !== "" && !isNaN(Number(v)))
      .reduce((acc, [, v]) => acc + Number(v), 0);

  function save() {
    const entries = students
      .map((s) => {
        const question_marks: Record<string, number> = {};
        Object.entries(grid[s.id] || {}).forEach(([qno, v]) => {
          if (v !== "" && !isNaN(Number(v))) question_marks[qno] = Number(v);
        });
        return { student_id: s.id, question_marks };
      })
      .filter((e) => Object.keys(e.question_marks).length > 0);
    onSave(entries);
    setDirty(false);
  }

  const invalid = (qno: string, v: string) =>
    v !== "" && (isNaN(Number(v)) || Number(v) < 0 || Number(v) > maxByNo[qno]);

  const anyInvalid = students.some((s) =>
    Object.entries(grid[s.id] || {}).some(([qno, v]) => invalid(qno, v))
  );

  return (
    <div>
      <div style={{ overflowX: "auto" }}>
        <table className="data-table" style={{ minWidth: questions.length * 84 + 240 }}>
          <thead>
            <tr>
              <th style={stickyTh}>Student</th>
              {questions.map((q) => (
                <th key={q.no} style={{ textAlign: "center", minWidth: 76 }} title={q.topic || ""}>
                  Q{q.no}
                  <div style={{ fontSize: 10, fontWeight: 400, color: "var(--text-muted)" }}>
                    /{q.max_marks}{q.topic ? ` · ${q.topic}` : ""}
                  </div>
                </th>
              ))}
              <th style={{ textAlign: "right" }}>Total</th>
            </tr>
          </thead>
          <tbody>
            {students.map((s, row) => (
              <tr key={s.id}>
                <td style={stickyTd}>
                  <span style={{ fontWeight: 600 }}>{s.roll_no || "—"}</span>{" "}
                  {s.student_name || "—"}
                </td>
                {questions.map((q, col) => {
                  const v = grid[s.id]?.[q.no] ?? "";
                  return (
                    <td key={q.no} style={{ textAlign: "center", padding: 4 }}>
                      <input
                        ref={(el) => { inputs.current[`${row}-${col}`] = el; }}
                        inputMode="decimal"
                        value={v}
                        onChange={(e) => setCell(s.id, q.no, e.target.value)}
                        onKeyDown={(e) => onKeyDown(e, row, col)}
                        style={{
                          width: 64,
                          padding: "6px 8px",
                          textAlign: "center",
                          borderRadius: "var(--radius-sm)",
                          border: invalid(q.no, v)
                            ? "2px solid var(--danger)"
                            : "1px solid var(--border)",
                        }}
                      />
                    </td>
                  );
                })}
                <td style={{ textAlign: "right", fontWeight: 700 }}>{rowTotal(s.id)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "14px 24px", borderTop: "1px solid var(--border)" }}>
        <div style={{ fontSize: 13, color: "var(--text-muted)" }}>
          {dirty ? "Unsaved changes" : "All changes saved"}
          {anyInvalid && <span style={{ color: "var(--danger)" }}> · some marks exceed the question max</span>}
        </div>
        <button
          className="btn btn-primary"
          style={{ width: "auto", padding: "8px 18px", borderRadius: "var(--radius-full)", fontSize: 13 }}
          onClick={save}
          disabled={saving || anyInvalid}
        >
          {saving ? "Saving…" : "Save marks"}
        </button>
      </div>
    </div>
  );
}

const stickyTh: React.CSSProperties = { position: "sticky", left: 0, background: "var(--surface, white)", zIndex: 1, minWidth: 200 };
const stickyTd: React.CSSProperties = { position: "sticky", left: 0, background: "var(--surface, white)", zIndex: 1 };
