"use client";

import { useEffect, useState } from "react";
import { api, getApiErrorMessage } from "@/lib/api";
import { AppSelect } from "@/components/ui/AppSelect";

type QuestionRow = { no: string; max_marks: string; topic: string };
type QuestionSchemaItem = { no: string; max_marks: number | string; topic?: string | null };
type ExamSummary = {
  id: string;
  class_id: string;
  subject_id: string;
  exam_type: string;
  title: string;
  total_marks: number | string;
};
type PaperSummary = {
  id: string;
  class_id: string;
  subject_id: string;
  exam_type?: string;
  title: string;
  total_marks: number | string;
  status: string;
};
type ListResponse<T> = T[] | { items?: T[] };

export default function QuestionSchemaEditor({
  exam,
  onSaved,
  onCancel,
}: {
  exam: ExamSummary;
  onSaved: (updatedExam: ExamSummary) => void;
  onCancel: () => void;
}) {
  const [rows, setRows] = useState<QuestionRow[]>([{ no: "1", max_marks: "", topic: "" }]);
  const [papers, setPapers] = useState<PaperSummary[]>([]);
  const [knownTopics, setKnownTopics] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api<{ data?: QuestionSchemaItem[] }>(`/api/v1/exams/${exam.id}/questions`)
      .then((r) => {
        const qs = r.data || [];
        if (qs.length > 0) {
          setRows(qs.map((q) => ({
            no: q.no,
            max_marks: String(q.max_marks),
            topic: q.topic || "",
          })));
        }
      })
      .catch(() => {});
    // Approved AI papers for this class are importable as a question structure.
    api<ListResponse<PaperSummary>>("/api/v1/ai/question-papers")
      .then((r) => {
        const items = Array.isArray(r) ? r : r.items || [];
        setPapers(items.filter((p) =>
          p.status === "approved" &&
          p.class_id === exam.class_id &&
          p.subject_id === exam.subject_id &&
          (p.exam_type || "unit_test") === exam.exam_type &&
          Number(p.total_marks) === Number(exam.total_marks)
        ));
      })
      .catch(() => {});
    // Topic typeahead — endpoint ships with the mastery module; harmless 404 until then.
    api<{ data?: string[] }>(`/api/v1/mastery/topics?subject_id=${exam.subject_id}`)
      .then((r) => setKnownTopics(r.data || []))
      .catch(() => {});
  }, [exam.class_id, exam.exam_type, exam.id, exam.subject_id, exam.total_marks]);

  const sumMax = rows.reduce((acc, r) => acc + (Number(r.max_marks) || 0), 0);

  function updateRow(i: number, patch: Partial<QuestionRow>) {
    setRows((rs) => rs.map((r, idx) => (idx === i ? { ...r, ...patch } : r)));
  }

  function addRow() {
    setRows((rs) => {
      const lastNo = Number(rs[rs.length - 1]?.no);
      const nextNo = Number.isFinite(lastNo) ? String(lastNo + 1) : "";
      const lastTopic = rs[rs.length - 1]?.topic || "";
      return [...rs, { no: nextNo, max_marks: rs[rs.length - 1]?.max_marks || "", topic: lastTopic }];
    });
  }

  async function importFromPaper(paperId: string) {
    if (!paperId) return;
    setSaving(true);
    setError("");
    try {
      const res = await api<{ data: ExamSummary }>(`/api/v1/exams/${exam.id}/questions`, {
        method: "PUT",
        body: JSON.stringify({ source_paper_id: paperId }),
      });
      onSaved(res.data);
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to import paper structure"));
    } finally {
      setSaving(false);
    }
  }

  async function save() {
    const questions = rows
      .filter((r) => r.no.trim() && Number(r.max_marks) > 0)
      .map((r) => ({
        no: r.no.trim(),
        max_marks: Number(r.max_marks),
        topic: r.topic.trim() || null,
      }));
    if (questions.length === 0) {
      setError("Add at least one question with marks.");
      return;
    }
    setSaving(true);
    setError("");
    try {
      const res = await api<{ data: ExamSummary }>(`/api/v1/exams/${exam.id}/questions`, {
        method: "PUT",
        body: JSON.stringify({ questions }),
      });
      onSaved(res.data);
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to save question schema"));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="card" style={{ marginBottom: 24, padding: 24 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <div>
          <div style={{ fontWeight: 700 }}>Question structure — {exam.title}</div>
          <div style={{ fontSize: 13, color: "var(--text-muted)" }}>
            Question number, max marks and chapter/topic. Topics power per-topic mastery tracking.
          </div>
        </div>
        {papers.length > 0 && (
          <AppSelect
            variant="field"
            style={{ width: 260 }}
            value=""
            onChange={(v) => importFromPaper(v)}
            disabled={saving}
            aria-label="Import from approved AI paper"
            placeholder="Import from approved AI paper…"
            options={papers.map((p) => ({ value: p.id, label: p.title }))}
          />
        )}
      </div>

      {error && <div style={{ marginBottom: 12, color: "var(--danger)", fontSize: 13 }}>{error}</div>}

      <datalist id="known-topics">
        {knownTopics.map((t) => <option key={t} value={t} />)}
      </datalist>

      <table className="data-table">
        <thead>
          <tr>
            <th style={{ width: 90 }}>Q No</th>
            <th style={{ width: 120 }}>Max marks</th>
            <th>Chapter / Topic</th>
            <th style={{ width: 60 }} />
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i}>
              <td>
                <input className="form-input" style={cell} value={r.no}
                  onChange={(e) => updateRow(i, { no: e.target.value })} />
              </td>
              <td>
                <input className="form-input" style={cell} type="number" min={0} value={r.max_marks}
                  onChange={(e) => updateRow(i, { max_marks: e.target.value })} />
              </td>
              <td>
                <input className="form-input" style={cell} value={r.topic} list="known-topics"
                  placeholder="e.g. Algebra"
                  onChange={(e) => updateRow(i, { topic: e.target.value })} />
              </td>
              <td>
                <button className="btn btn-ghost" style={{ padding: "4px 10px" }}
                  onClick={() => setRows((rs) => rs.filter((_, idx) => idx !== i))}
                  disabled={rows.length === 1}>
                  ✕
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 16 }}>
        <div style={{ fontSize: 13, color: sumMax < Number(exam.total_marks) ? "var(--danger)" : "var(--text-muted)" }}>
          Σ max marks: <b>{sumMax}</b> / exam total {exam.total_marks}
          {sumMax > Number(exam.total_marks) && " (internal choice)"}
          {sumMax < Number(exam.total_marks) && " — questions missing"}
        </div>
        <div style={{ display: "flex", gap: 12 }}>
          <button className="btn btn-ghost" style={btn} onClick={addRow}>+ Add question</button>
          <button className="btn btn-ghost" style={btn} onClick={onCancel}>Cancel</button>
          <button className="btn btn-primary" style={btn} onClick={save} disabled={saving}>
            {saving ? "Saving…" : "Save structure"}
          </button>
        </div>
      </div>
    </div>
  );
}

const cell: React.CSSProperties = { padding: "6px 10px", width: "100%" };
const btn: React.CSSProperties = { width: "auto", padding: "8px 18px", borderRadius: "var(--radius-full)", fontSize: 13 };
