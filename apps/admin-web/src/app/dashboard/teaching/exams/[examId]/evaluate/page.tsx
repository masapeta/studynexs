"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api, API_URL, getAccessToken, getApiErrorMessage, getTenantSlug } from "@/lib/api";
import { AppSelect } from "@/components/ui/AppSelect";
import { PageHeaderCard } from "@/components/layout/PageHeaderCard";
import { AppFileInput } from "@/components/ui/AppFileInput";
import { TEACHING } from "@/lib/dashboard-routes";
import { AI_INPUT, clampText, validateAnswerSheetFile } from "@/lib/ai-input-limits";

async function uploadAnswerSheet(file: File): Promise<string> {
  const form = new FormData();
  form.append("file", file);
  const token = getAccessToken();
  const res = await fetch(`${API_URL}/api/v1/files/upload?category=answer_sheet`, {
    method: "POST",
    headers: {
      "X-Tenant-Slug": getTenantSlug(),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: form,
    credentials: "include",
  });
  if (!res.ok) throw new Error(await res.text());
  const body = await res.json();
  return body.data.id;
}

async function pollUntilSuggested(examId: string, evalId: string, jobId?: string) {
  const maxAttempts = 60;
  for (let i = 0; i < maxAttempts; i++) {
    if (jobId) {
      const job = await api(`/api/v1/jobs/${jobId}`).catch(() => null);
      if (job?.data?.status === "failed") {
        throw new Error(job.data.error || "Evaluation job failed");
      }
    }
    const ev = await api(`/api/v1/exams/evaluations/${evalId}`);
    const row = ev.data;
    if (row.status === "suggested" || row.status === "approved") return row;
    if (row.status === "failed") throw new Error(row.error_message || "Evaluation failed");
    await new Promise((r) => setTimeout(r, 1500));
  }
  throw new Error("Evaluation timed out — check again from recent evaluations");
}

export default function EvaluateExamPage() {
  const params = useParams();
  const router = useRouter();
  const examId = params.examId as string;

  const [exam, setExam] = useState<any>(null);
  const [students, setStudents] = useState<any[]>([]);
  const [questions, setQuestions] = useState<any[]>([]);
  const [evaluations, setEvaluations] = useState<any[]>([]);
  const [selectedStudent, setSelectedStudent] = useState("");
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [sheetFile, setSheetFile] = useState<File | null>(null);
  const [activeEval, setActiveEval] = useState<any>(null);
  const [overrides, setOverrides] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [approving, setApproving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!examId) return;
    setLoading(true);
    setError("");

    api("/api/v1/academic/classes?page_size=100")
      .then(async (classesRes) => {
        const classes = classesRes.items || classesRes.data || [];
        for (const c of classes) {
          const exRes = await api(`/api/v1/exams?class_id=${c.id}`).catch(() => ({ data: [] }));
          const found = (exRes.data || []).find((e: any) => e.id === examId);
          if (!found) continue;
          setExam({ ...found, class_id: c.id });
          const [qRes, evRes, stuRes] = await Promise.all([
            api(`/api/v1/exams/${examId}/questions`),
            api(`/api/v1/exams/${examId}/evaluations`),
            api(`/api/v1/academic/students?class_id=${c.id}&page_size=200`),
          ]);
          const qs = qRes.data || [];
          setQuestions(qs);
          setEvaluations(evRes.data || []);
          setStudents(stuRes.items || stuRes.data || []);
          const init: Record<string, string> = {};
          qs.forEach((q: any) => { init[q.no] = ""; });
          setAnswers(init);
          break;
        }
      })
      .catch((e) => setError(getApiErrorMessage(e, "Failed to load exam")))
      .finally(() => setLoading(false));
  }, [examId]);

  useEffect(() => {
    if (loading || evaluations.length === 0 || activeEval) return;
    const pending = evaluations.find((e: { status?: string }) => e.status === "suggested");
    if (pending) loadEval(pending);
  }, [loading, evaluations, activeEval]);

  async function runEvaluation() {
    if (!selectedStudent) {
      setError("Select a student.");
      return;
    }
    const hasAnswers = Object.values(answers).some((v) => v.trim());
    if (!sheetFile && !hasAnswers) {
      setError("Upload an answer sheet photo or enter answers manually.");
      return;
    }
    setRunning(true);
    setError("");
    try {
      let fileId: string | undefined;
      if (sheetFile) {
        const fileErr = validateAnswerSheetFile(sheetFile);
        if (fileErr) {
          setError(fileErr);
          setRunning(false);
          return;
        }
        fileId = await uploadAnswerSheet(sheetFile);
      }
      const res = await api(`/api/v1/exams/${examId}/evaluations`, {
        method: "POST",
        body: JSON.stringify({
          student_id: selectedStudent,
          file_id: fileId,
          student_answers: answers,
        }),
      });
      let row = res.data;
      if (row.status === "processing") {
        row = await pollUntilSuggested(examId, row.id, row.job_id);
      }
      setActiveEval(row);
      setEvaluations((evs) => [row, ...evs.filter((e: any) => e.id !== row.id)]);
      const ov: Record<string, string> = {};
      Object.entries(row.ai_suggestions || {}).forEach(([qno, s]: [string, any]) => {
        ov[qno] = String(s.marks_suggested);
      });
      setOverrides(ov);
    } catch (e) {
      setError(getApiErrorMessage(e, "Evaluation failed"));
    } finally {
      setRunning(false);
    }
  }

  async function approveEvaluation() {
    if (!activeEval) return;
    setApproving(true);
    setError("");
    try {
      const teacher_overrides: Record<string, { marks: number; reason?: string }> = {};
      Object.entries(overrides).forEach(([qno, marks]) => {
        const suggested = activeEval.ai_suggestions?.[qno]?.marks_suggested;
        if (Number(marks) !== Number(suggested)) {
          teacher_overrides[qno] = { marks: Number(marks), reason: "Teacher adjustment" };
        }
      });
      const res = await api(`/api/v1/exams/evaluations/${activeEval.id}/approve`, {
        method: "POST",
        body: JSON.stringify({ teacher_overrides }),
      });
      setActiveEval(res.data);
      setEvaluations((evs) => evs.map((e) => (e.id === res.data.id ? res.data : e)));
      alert("Marks approved. Weak topics updated in mastery; misconceptions saved to library.");
    } catch (e) {
      setError(getApiErrorMessage(e, "Approve failed"));
    } finally {
      setApproving(false);
    }
  }

  function loadEval(ev: any) {
    setActiveEval(ev);
    setSelectedStudent(ev.student_id);
    const ov: Record<string, string> = {};
    Object.entries(ev.ai_suggestions || {}).forEach(([qno, s]: [string, any]) => {
      const override = ev.teacher_overrides?.[qno]?.marks;
      ov[qno] = String(override ?? s.marks_suggested);
    });
    setOverrides(ov);
  }

  const studentName = (id: string) =>
    students.find((s) => s.id === id)?.student_name || students.find((s) => s.id === id)?.full_name || id.slice(0, 8);

  if (loading) {
    return <div className="card" style={{ padding: 40, textAlign: "center" }}><div className="spinner" style={{ margin: "0 auto" }} /></div>;
  }

  if (!exam?.can_evaluate_sheets && exam) {
    return (
      <div className="card" style={{ padding: 24 }}>
        <p>This exam is not linked to an approved AI question paper. Import questions from an approved paper first.</p>
        <Link href={TEACHING.exams} className="btn btn-ghost" style={{ marginTop: 12 }}>← Back to exams</Link>
      </div>
    );
  }

  return (
    <>
      <PageHeaderCard
        title="Evaluate answer sheets"
        subtitle={`${exam?.title || "Exam"} · Vision OCR + async grading`}
      >
        <div style={{ display: "flex", gap: 8 }}>
          <Link href={TEACHING.corrections} className="btn btn-ghost gw-btn-sm">Past corrections</Link>
          <button type="button" className="btn btn-ghost gw-btn-sm" onClick={() => router.push(TEACHING.exams)}>← Exams</button>
        </div>
      </PageHeaderCard>

      {error && <div className="card sn-inline-alert sn-inline-alert--error">{error}</div>}

      {evaluations.some((e) => e.status === "suggested") && (
        <div
          className="card"
          style={{
            marginBottom: 16,
            padding: "12px 16px",
            borderLeft: "3px solid var(--accent)",
            fontSize: 14,
          }}
        >
          AI has suggested marks waiting for your review. Select a student on the left, adjust if needed, then approve to publish.
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "280px 1fr", gap: 20 }}>
        <div className="card" style={{ padding: 16 }}>
          <div className="stat-label" style={{ marginBottom: 8 }}>Students</div>
          <AppSelect
            variant="field"
            value={selectedStudent}
            onChange={setSelectedStudent}
            aria-label="Select student"
            placeholder="Select student…"
            style={{ marginBottom: 12 }}
            options={[
              { value: "", label: "Select student…" },
              ...students.map((s) => ({
                value: s.id,
                label: `${s.roll_no ? `${s.roll_no} · ` : ""}${s.student_name || s.full_name || "Student"}`,
              })),
            ]}
          />
          <div className="stat-label" style={{ marginBottom: 8 }}>Recent evaluations</div>
          {evaluations.length === 0 ? (
            <p style={{ fontSize: 13, color: "var(--text-muted)" }}>None yet.</p>
          ) : evaluations.map((ev) => (
            <button
              key={ev.id}
              type="button"
              className="btn btn-ghost"
              style={{ ...btn, width: "100%", justifyContent: "flex-start", marginBottom: 6, fontSize: 12 }}
              onClick={() => loadEval(ev)}
            >
              {studentName(ev.student_id)} — {ev.status}
            </button>
          ))}
        </div>

        <div className="card" style={{ padding: 20 }}>
          {!activeEval || activeEval.status === "processing" ? (
            <>
              <div style={{ marginBottom: 16 }}>
                <div className="stat-label" style={{ marginBottom: 8 }}>Answer sheet photo</div>
                <AppFileInput
                  variant="field"
                  accept="image/jpeg,image/png,image/webp"
                  file={sheetFile}
                  onChange={setSheetFile}
                  placeholder="Choose JPEG, PNG, or WebP"
                  aria-label="Answer sheet photo"
                />
                {sheetFile && (
                  <p style={{ fontSize: 13, color: "var(--text-muted)", marginTop: 6 }}>
                    Vision OCR will transcribe answers from this sheet.
                  </p>
                )}
              </div>
              <p style={{ fontSize: 14, color: "var(--text-muted)", marginBottom: 12 }}>
                Optional: override or fill gaps with manual answers per question.
              </p>
              <table className="data-table">
                <thead><tr><th>Q</th><th>Max</th><th>Override answer</th></tr></thead>
                <tbody>
                  {questions.map((q) => (
                    <tr key={q.no}>
                      <td style={{ fontWeight: 600 }}>{q.no}</td>
                      <td>{q.max_marks}</td>
                      <td>
                        <input
                          className="form-input"
                          value={answers[q.no] ?? ""}
                          onChange={(e) =>
                            setAnswers({
                              ...answers,
                              [q.no]: clampText(e.target.value, AI_INPUT.answerMaxLength),
                            })
                          }
                          maxLength={AI_INPUT.answerMaxLength}
                          placeholder="Optional override"
                          style={{ width: "100%" }}
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <button className="btn btn-primary" style={{ ...btn, marginTop: 16 }} onClick={runEvaluation} disabled={running}>
                {running ? "Evaluating (async)…" : "Upload & evaluate"}
              </button>
            </>
          ) : (
            <>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 12 }}>
                <strong>Review — {studentName(activeEval.student_id)}</strong>
                <span style={{ fontSize: 13, color: "var(--text-muted)" }}>{activeEval.status}</span>
              </div>
              {activeEval.correction_summary && (
                <div style={{ padding: 12, background: "var(--surface-muted)", borderRadius: 8, marginBottom: 16, fontSize: 13, whiteSpace: "pre-wrap" }}>
                  {activeEval.correction_summary}
                </div>
              )}
              <table className="data-table">
                <thead><tr><th>Q</th><th>AI marks</th><th>Final marks</th><th>Feedback & rubric</th></tr></thead>
                <tbody>
                  {Object.entries(activeEval.ai_suggestions || {}).map(([qno, raw]: [string, any]) => {
                    const s = raw as EvalSuggestion;
                    return (
                    <tr key={qno}>
                      <td>{qno}</td>
                      <td>
                        {s.marks_suggested} / {s.max_marks}
                        {s.method && (
                          <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 4 }}>
                            {methodLabel(s.method)}
                          </div>
                        )}
                      </td>
                      <td>
                        <input
                          type="number"
                          min={0}
                          max={s.max_marks}
                          step={0.5}
                          value={overrides[qno] ?? String(s.marks_suggested)}
                          onChange={(e) => setOverrides({ ...overrides, [qno]: e.target.value })}
                          style={{ width: 72 }}
                          disabled={activeEval.status === "approved"}
                        />
                      </td>
                      <td style={{ fontSize: 13, maxWidth: 420 }}>
                        {s.feedback}
                        <RubricBreakdown suggestion={s} />
                      </td>
                    </tr>
                    );
                  })}
                </tbody>
              </table>
              {activeEval.status === "suggested" && (
                <div style={{ display: "flex", gap: 8, marginTop: 16 }}>
                  <button className="btn btn-primary" style={btn} onClick={approveEvaluation} disabled={approving}>
                    {approving ? "Saving…" : "Approve marks"}
                  </button>
                  <button className="btn btn-ghost" style={btn} onClick={() => setActiveEval(null)}>New evaluation</button>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </>
  );
}

const btn: React.CSSProperties = { width: "auto", padding: "8px 18px", borderRadius: "var(--radius-full)", fontSize: 13 };

type EvalSuggestion = {
  marks_suggested: number;
  max_marks: number;
  feedback: string;
  confidence?: number;
  method?: string;
  criteria?: Array<{
    criterion: string;
    max_points: number;
    awarded_points: number;
    met?: boolean;
    comment?: string;
  }>;
  missing_concepts?: string[];
};

function methodLabel(method?: string): string {
  switch (method) {
    case "objective":
      return "Objective";
    case "llm_rubric":
      return "Rubric (AI)";
    case "heuristic_fallback":
      return "Heuristic";
    default:
      return method || "—";
  }
}

function RubricBreakdown({ suggestion }: { suggestion: EvalSuggestion }) {
  const criteria = suggestion.criteria || [];
  const missing = suggestion.missing_concepts || [];
  const hasMeta = suggestion.method || suggestion.confidence != null || missing.length > 0 || criteria.length > 0;
  if (!hasMeta) return null;

  return (
    <div style={{ marginTop: 8, fontSize: 12, color: "var(--text-muted)" }}>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: criteria.length ? 8 : 0 }}>
        {suggestion.method && (
          <span style={metaChip}>{methodLabel(suggestion.method)}</span>
        )}
        {suggestion.confidence != null && (
          <span style={metaChip}>Confidence {Math.round(suggestion.confidence * 100)}%</span>
        )}
        {missing.map((c) => (
          <span key={c} style={{ ...metaChip, color: "var(--warning)", borderColor: "var(--warning)" }}>
            Missing: {c}
          </span>
        ))}
      </div>
      {criteria.length > 0 && (
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
          <thead>
            <tr>
              <th style={rubricTh}>Criterion</th>
              <th style={rubricTh}>Awarded</th>
              <th style={rubricTh}>Note</th>
            </tr>
          </thead>
          <tbody>
            {criteria.map((c) => (
              <tr key={c.criterion}>
                <td style={rubricTd}>{c.criterion}</td>
                <td style={rubricTd}>
                  {c.awarded_points} / {c.max_points}
                  {c.met === false && " · partial"}
                </td>
                <td style={rubricTd}>{c.comment || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

const metaChip: React.CSSProperties = {
  display: "inline-block",
  padding: "2px 8px",
  borderRadius: 999,
  border: "1px solid var(--border)",
  fontSize: 11,
  color: "var(--text-muted)",
};

const rubricTh: React.CSSProperties = {
  textAlign: "left",
  padding: "4px 6px",
  borderBottom: "1px solid var(--border)",
  fontWeight: 600,
};

const rubricTd: React.CSSProperties = {
  padding: "4px 6px",
  verticalAlign: "top",
  borderBottom: "1px solid var(--border-subtle, var(--border))",
};
