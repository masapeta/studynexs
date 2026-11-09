"use client";

import { useEffect, useState } from "react";
import { ClipboardList } from "lucide-react";
import { Card, EmptyState, ListRow, SectionHeader, SkeletonCard } from "@/components/ui/kit";
import { api, getApiErrorMessage } from "@/lib/api";

export type LearnerResultSummary = {
  exam_id: string;
  exam_title: string;
  subject_name: string | null;
  exam_date: string | null;
  status: "released" | "pending";
  marks_obtained: number | null;
  total_marks: number | null;
  percentage: number | null;
  grade_letter: string | null;
  published_at: string | null;
};

export type LearnerResultDetail = LearnerResultSummary & {
  question_marks: Record<string, number> | null;
  question_max_marks: Record<string, number> | null;
  feedback: string | null;
};

/** Shared list for student self (/portal/results) and parent (/portal/child/{id}/results). */
export function LearnerResultsList({ endpoint, detailHref }: { endpoint: string; detailHref: (examId: string) => string }) {
  const [rows, setRows] = useState<LearnerResultSummary[] | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let alive = true;
    api<{ data: LearnerResultSummary[] }>(endpoint)
      .then((r) => alive && setRows(r.data))
      .catch((e) => alive && setError(getApiErrorMessage(e, "Couldn't load results.")));
    return () => {
      alive = false;
    };
  }, [endpoint]);

  if (error) return <p role="alert" style={{ color: "var(--danger)" }}>{error}</p>;
  if (rows === null) return <SkeletonCard />;
  if (rows.length === 0) {
    return (
      <EmptyState
        icon={ClipboardList}
        title="No results yet"
        message="Results appear here after your teacher releases them."
      />
    );
  }
  return (
    <>
      <SectionHeader title="Exam results" />
      <Card padded={false}>
        {rows.map((r) => (
          <a key={r.exam_id} href={detailHref(r.exam_id)} style={{ color: "inherit", textDecoration: "none", display: "block" }}>
            <ListRow
              icon={ClipboardList}
              tone={r.status === "released" ? "accent" : "default"}
              title={r.exam_title}
              subtitle={[r.subject_name, r.exam_date].filter(Boolean).join(" · ")}
              value={
                r.status === "released"
                  ? `${r.marks_obtained}/${r.total_marks}`
                  : <span style={{ fontSize: 13, color: "var(--text-muted)" }}>Result pending</span>
              }
              chevron
            />
          </a>
        ))}
      </Card>
    </>
  );
}

export function LearnerResultDetailView({ endpoint }: { endpoint: string }) {
  const [row, setRow] = useState<LearnerResultDetail | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let alive = true;
    api<{ data: LearnerResultDetail }>(endpoint)
      .then((r) => alive && setRow(r.data))
      .catch((e) => alive && setError(getApiErrorMessage(e, "Couldn't load this result.")));
    return () => {
      alive = false;
    };
  }, [endpoint]);

  if (error) return <p role="alert" style={{ color: "var(--danger)" }}>{error}</p>;
  if (!row) return <SkeletonCard />;
  if (row.status === "pending") {
    return (
      <EmptyState
        icon={ClipboardList}
        title="Result pending"
        message={`${row.exam_title}: your teacher hasn't released this result yet.`}
      />
    );
  }
  const qnos = Object.keys(row.question_marks || {}).sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));
  return (
    <>
      <Card>
        <div style={{ fontSize: 13, color: "var(--text-muted)" }}>
          {[row.subject_name, row.exam_date].filter(Boolean).join(" · ")}
        </div>
        <div style={{ fontSize: 18, fontWeight: 700, margin: "4px 0" }}>{row.exam_title}</div>
        <div style={{ fontSize: 28, fontWeight: 700 }} data-testid="result-total">
          {row.marks_obtained} / {row.total_marks}
          {row.percentage != null && (
            <span style={{ fontSize: 15, fontWeight: 500, color: "var(--text-muted)" }}> · {row.percentage}%</span>
          )}
        </div>
        {row.grade_letter && <div>Grade: {row.grade_letter}</div>}
      </Card>
      {qnos.length > 0 && (
        <>
          <SectionHeader title="Question-wise marks" />
          <Card padded={false}>
            <div className="sn-table-scroll">
              <table className="data-table">
                <thead><tr><th scope="col">Question</th><th scope="col">Marks</th></tr></thead>
                <tbody>
                  {qnos.map((q) => (
                    <tr key={q}>
                      <td>Q{q}</td>
                      <td>
                        {row.question_marks?.[q]}
                        {row.question_max_marks?.[q] != null && ` / ${row.question_max_marks[q]}`}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </>
      )}
      {row.feedback && (
        <>
          <SectionHeader title="Teacher feedback" />
          <Card><p style={{ whiteSpace: "pre-wrap", margin: 0 }}>{row.feedback}</p></Card>
        </>
      )}
    </>
  );
}
