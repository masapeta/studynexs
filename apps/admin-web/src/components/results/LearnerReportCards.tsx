"use client";

import { useEffect, useState } from "react";
import { FileText } from "lucide-react";
import { Card, EmptyState, ListRow, SectionHeader, SkeletonCard } from "@/components/ui/kit";
import { api, getApiErrorMessage } from "@/lib/api";

export type LearnerReportCard = {
  id: string;
  title: string;
  student_name: string;
  class_name: string;
  subjects: { subject: string; marks_obtained: number; total_marks: number }[];
  not_assessed: string[];
  total_obtained: number;
  total_max: number;
  percentage: number;
  overall_grade: string;
  attendance_percentage: number | null;
  remark: string | null;
  remark_withheld: boolean;
};

/** Approved report cards whose results are all released (server-enforced). */
export function LearnerReportCardsList({ endpoint, detailHref }: { endpoint: string; detailHref: (id: string) => string }) {
  const [rows, setRows] = useState<LearnerReportCard[] | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let alive = true;
    api<{ data: LearnerReportCard[] }>(endpoint)
      .then((r) => alive && setRows(r.data))
      .catch((e) => alive && setError(getApiErrorMessage(e, "Couldn't load report cards.")));
    return () => {
      alive = false;
    };
  }, [endpoint]);

  return (
    <section aria-label="Report cards" style={{ marginTop: 24 }}>
      <SectionHeader title="Report cards" />
      {error ? (
        <p role="alert" style={{ color: "var(--danger)" }}>{error}</p>
      ) : rows === null ? (
        <SkeletonCard />
      ) : rows.length === 0 ? (
        <EmptyState
          icon={FileText}
          title="No report cards yet"
          message="A report card appears once your teacher approves it and every result on it is released."
        />
      ) : (
        <Card padded={false}>
          {rows.map((r) => (
            <a key={r.id} href={detailHref(r.id)} data-testid="report-card-row" style={{ color: "inherit", textDecoration: "none", display: "block" }}>
              <ListRow
                icon={FileText}
                tone="accent"
                title={r.title}
                subtitle={r.class_name}
                value={`${r.percentage}% · ${r.overall_grade}`}
                chevron
              />
            </a>
          ))}
        </Card>
      )}
    </section>
  );
}

export function LearnerReportCardView({ endpoint }: { endpoint: string }) {
  const [card, setCard] = useState<LearnerReportCard | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let alive = true;
    api<{ data: LearnerReportCard }>(endpoint)
      .then((r) => alive && setCard(r.data))
      .catch((e) => alive && setError(getApiErrorMessage(e, "Couldn't load this report card.")));
    return () => {
      alive = false;
    };
  }, [endpoint]);

  if (error) return <p role="alert" style={{ color: "var(--danger)" }}>{error}</p>;
  if (!card) return <SkeletonCard />;
  return (
    <>
      <Card>
        <div style={{ fontSize: 13, color: "var(--text-muted)" }}>{card.student_name} · {card.class_name}</div>
        <div style={{ fontSize: 18, fontWeight: 700, margin: "4px 0" }}>{card.title}</div>
        <div style={{ fontSize: 28, fontWeight: 700 }} data-testid="report-card-total">
          {card.total_obtained} / {card.total_max}
          <span style={{ fontSize: 15, fontWeight: 500, color: "var(--text-muted)" }}> · {card.percentage}%</span>
        </div>
        <div>Grade: {card.overall_grade}</div>
        {card.attendance_percentage != null && <div>Attendance: {card.attendance_percentage}%</div>}
      </Card>
      <SectionHeader title="Subjects" />
      <Card padded={false}>
        <div className="sn-table-scroll">
          <table className="data-table">
            <thead><tr><th scope="col">Subject</th><th scope="col">Marks</th></tr></thead>
            <tbody>
              {card.subjects.map((s) => (
                <tr key={s.subject}>
                  <td>{s.subject}</td>
                  <td>{s.marks_obtained} / {s.total_marks}</td>
                </tr>
              ))}
              {card.not_assessed.map((name) => (
                <tr key={`na-${name}`}>
                  <td>{name}</td>
                  <td style={{ color: "var(--text-muted)" }}>Not assessed</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
      {card.remark ? (
        <>
          <SectionHeader title="Teacher remark" />
          <Card><p style={{ whiteSpace: "pre-wrap", margin: 0 }}>{card.remark}</p></Card>
        </>
      ) : card.remark_withheld ? (
        <Card>
          <p style={{ margin: 0, color: "var(--text-muted)" }} data-testid="remark-withheld">
            The teacher&apos;s remark will appear once updated results are released.
          </p>
        </Card>
      ) : null}
    </>
  );
}
