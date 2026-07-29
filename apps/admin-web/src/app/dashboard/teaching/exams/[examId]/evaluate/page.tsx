"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api, API_URL, getAccessToken, getApiErrorMessage, getTenantSlug } from "@/lib/api";
import { AppSelect } from "@/components/ui/AppSelect";
import { PageHeaderCard } from "@/components/layout/PageHeaderCard";
import { AppFileInput } from "@/components/ui/AppFileInput";
import { TEACHING } from "@/lib/dashboard-routes";
import {
  buildAeiEvaluationTrustSummary,
  buildAeiEvidenceRows,
  buildAeiSuggestionTrustBadges,
  type AeiBadgeTone,
  type AeiSuggestionLike,
} from "@/lib/aei-evaluation-display";
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
  const [overrideReasons, setOverrideReasons] = useState<Record<string, string>>({});
  const [manualReviewAcknowledgements, setManualReviewAcknowledgements] = useState<Record<string, boolean>>({});
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
            api(`/api/v1/academic/students?class_id=${c.id}&page_size=100`),
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
      setOverrides(buildOverrideMarks(row));
      setOverrideReasons(buildOverrideReasons(row));
      setManualReviewAcknowledgements(buildManualReviewAcknowledgements(row));
    } catch (e) {
      setError(getApiErrorMessage(e, "Evaluation failed"));
    } finally {
      setRunning(false);
    }
  }

  async function approveEvaluation() {
    if (!activeEval) return;
    setError("");
    const teacher_overrides: Record<string, { marks: number; reason?: string }> = {};
    const manual_review_acknowledgements: Record<
      string,
      { acknowledged: boolean; action: "accepted" | "adjusted" }
    > = {};
    const missingReasons: string[] = [];
    const manualReviewQuestions = manualReviewQuestionNumbers(activeEval);
    const ackRequired = manualReviewAcknowledgementRequired(activeEval);
    const missingAcknowledgements = ackRequired
      ? manualReviewQuestions.filter((qno) => manualReviewAcknowledgements[qno] !== true)
      : [];

    Object.entries(overrides).forEach(([qno, marks]) => {
      const suggested = activeEval.ai_suggestions?.[qno]?.marks_suggested;
      if (hasChangedMarks(suggested, marks)) {
        const reason = (overrideReasons[qno] || "").trim();
        if (!reason) {
          missingReasons.push(qno);
          return;
        }
        teacher_overrides[qno] = { marks: Number(marks), reason };
      }
    });

    manualReviewQuestions.forEach((qno) => {
      if (manualReviewAcknowledgements[qno] === true) {
        const suggested = activeEval.ai_suggestions?.[qno]?.marks_suggested;
        manual_review_acknowledgements[qno] = {
          acknowledged: true,
          action: hasChangedMarks(suggested, overrides[qno]) ? "adjusted" : "accepted",
        };
      }
    });

    if (missingReasons.length > 0) {
      setError(`Add a reason for each changed mark before approving: ${formatQuestionList(missingReasons)}.`);
      return;
    }
    if (missingAcknowledgements.length > 0) {
      setError(`Acknowledge teacher review for: ${formatQuestionList(missingAcknowledgements)}.`);
      return;
    }

    setApproving(true);
    try {
      const res = await api(`/api/v1/exams/evaluations/${activeEval.id}/approve`, {
        method: "POST",
        body: JSON.stringify({ teacher_overrides, manual_review_acknowledgements }),
      });
      setActiveEval(res.data);
      setOverrides(buildOverrideMarks(res.data));
      setOverrideReasons(buildOverrideReasons(res.data));
      setManualReviewAcknowledgements(buildManualReviewAcknowledgements(res.data));
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
    setOverrides(buildOverrideMarks(ev));
    setOverrideReasons(buildOverrideReasons(ev));
    setManualReviewAcknowledgements(buildManualReviewAcknowledgements(ev));
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
        subtitle={`${exam?.title || "Exam"} · Review AI-suggested marks before publishing`}
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
              <EvaluationEvidencePanel evaluation={activeEval} />
              <AeiEvaluationTrustSummaryPanel suggestions={activeEval.ai_suggestions || {}} />
              <table className="data-table">
                <thead><tr><th>Q</th><th>AI marks</th><th>Final marks</th><th>Feedback & rubric</th></tr></thead>
                <tbody>
                  {Object.entries(activeEval.ai_suggestions || {}).map(([qno, raw]) => {
                    const s = raw as EvalSuggestion;
                    const finalMarks = overrides[qno] ?? String(s.marks_suggested);
                    const finalMarksChanged = hasChangedMarks(s.marks_suggested, finalMarks);
                    const savedReason = savedOverrideReason(activeEval, qno);
                    const savedOverrideChanged =
                      activeEval.status === "approved" &&
                      hasSavedOverride(activeEval, qno) &&
                      hasChangedMarks(s.marks_suggested, activeEval.teacher_overrides?.[qno]?.marks);
                    const manualReviewRequired = suggestionRequiresManualReview(s);
                    const ackRequired = manualReviewAcknowledgementRequired(activeEval);
                    const savedAcknowledgement = savedManualReviewAcknowledgement(activeEval, qno);
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
                        <div style={{ display: "grid", gap: 6, minWidth: 160 }}>
                          <input
                            type="number"
                            min={0}
                            max={s.max_marks}
                            step={0.5}
                            value={finalMarks}
                            onChange={(e) => setOverrides({ ...overrides, [qno]: e.target.value })}
                            style={{ width: 72 }}
                            disabled={activeEval.status === "approved"}
                          />
                          {activeEval.status !== "approved" && finalMarksChanged && (
                            <label style={{ display: "grid", gap: 4, fontSize: 12, color: "var(--text-muted)" }}>
                              <span>Reason for change</span>
                              <textarea
                                className="form-input"
                                value={overrideReasons[qno] || ""}
                                onChange={(e) =>
                                  setOverrideReasons({
                                    ...overrideReasons,
                                    [qno]: clampText(e.target.value, OVERRIDE_REASON_MAX_LENGTH),
                                  })
                                }
                                maxLength={OVERRIDE_REASON_MAX_LENGTH}
                                placeholder="Example: Accepted alternate method"
                                rows={2}
                                style={{ width: "100%", resize: "vertical" }}
                              />
                            </label>
                          )}
                          {savedOverrideChanged && (
                            <div style={{ fontSize: 12, color: "var(--text-muted)" }}>
                              <strong style={{ color: "var(--text-primary)" }}>Override reason:</strong>{" "}
                              {savedReason || "Reason not recorded."}
                            </div>
                          )}
                          {activeEval.status !== "approved" && manualReviewRequired && (
                            <label
                              style={{
                                display: "flex",
                                gap: 8,
                                alignItems: "flex-start",
                                fontSize: 12,
                                color: "var(--text-muted)",
                              }}
                            >
                              <input
                                type="checkbox"
                                checked={manualReviewAcknowledgements[qno] === true}
                                onChange={(e) =>
                                  setManualReviewAcknowledgements({
                                    ...manualReviewAcknowledgements,
                                    [qno]: e.target.checked,
                                  })
                                }
                                aria-label={`Acknowledge teacher review for question ${qno}`}
                              />
                              <span>
                                I reviewed this uncertainty{ackRequired ? " (required before approval)" : ""}.
                              </span>
                            </label>
                          )}
                          {activeEval.status === "approved" && savedAcknowledgement && (
                            <div style={{ fontSize: 12, color: "var(--text-muted)" }}>
                              <strong style={{ color: "var(--text-primary)" }}>Manual review:</strong>{" "}
                              acknowledged by teacher.
                            </div>
                          )}
                        </div>
                      </td>
                      <td style={{ fontSize: 13, maxWidth: 420 }}>
                        {s.feedback}
                        <AeiSuggestionTrustMetadata suggestion={s} />
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

function AeiEvaluationTrustSummaryPanel({
  suggestions,
}: {
  suggestions: Record<string, unknown>;
}) {
  const summary = buildAeiEvaluationTrustSummary(suggestions);
  if (summary.totalQuestions === 0) return null;

  const hasAei = summary.questionsWithAeiMetadata > 0;
  return (
    <div
      style={{
        display: "grid",
        gap: 10,
        padding: 12,
        marginBottom: 16,
        borderRadius: 12,
        border: "1px solid var(--border)",
        background: "rgba(92, 124, 250, 0.08)",
        fontSize: 12,
        color: "var(--text-muted)",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
        <strong style={{ color: "var(--text-primary)" }}>Teacher review guidance</strong>
        <span>
          AI suggestions are draft only. Final marks are published after teacher approval.
        </span>
      </div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
        <span style={trustChipStyle("neutral")}>{summary.totalQuestions} suggestion{summary.totalQuestions === 1 ? "" : "s"}</span>
        {hasAei ? (
          <>
            <span style={trustChipStyle("success")}>{summary.deterministicSupported} supported</span>
            <span style={trustChipStyle(summary.manualReviewRequired ? "warning" : "neutral")}>
              {summary.manualReviewRequired} need teacher review
            </span>
            <span style={trustChipStyle(summary.lowConfidence ? "warning" : "neutral")}>
              {summary.lowConfidence} low confidence
            </span>
            <span style={trustChipStyle(summary.assistOrChecklist ? "warning" : "neutral")}>
              {summary.assistOrChecklist} assist/checklist
            </span>
            <span style={trustChipStyle("neutral")}>
              {summary.questionsWithConfidence} with confidence
            </span>
          </>
        ) : (
          <span style={trustChipStyle("neutral")}>
            Legacy suggestion format - review and approve before publishing
          </span>
        )}
      </div>
    </div>
  );
}

function AeiSuggestionTrustMetadata({ suggestion }: { suggestion: EvalSuggestion }) {
  const badges = buildAeiSuggestionTrustBadges(suggestion);
  const evidenceRows = buildAeiEvidenceRows(suggestion);
  if (badges.length === 0 && evidenceRows.length === 0) return null;

  return (
    <div style={{ marginTop: 8, display: "grid", gap: 6 }}>
      {badges.length > 0 && (
        <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
          {badges.map((badge) => (
            <span key={`${badge.label}:${badge.tone}`} style={trustChipStyle(badge.tone)} title={badge.title}>
              {badge.label}
            </span>
          ))}
        </div>
      )}
      {evidenceRows.length > 0 && (
        <div style={{ display: "grid", gap: 3, color: "var(--text-muted)" }}>
          {evidenceRows.map((row) => (
            <div key={`${row.label}:${row.value}`}>
              <strong style={{ color: "var(--text-primary)" }}>{row.label}:</strong> {row.value}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

type EvaluationEvidence = {
  evidence_ledger?: {
    curriculum_pack_id?: unknown;
    question_paper_id?: unknown;
    citation_ids?: unknown;
    evaluation_status?: unknown;
    teacher_approved_by?: unknown;
    teacher_approved_at?: unknown;
    question_paper_grounded?: unknown;
    evaluation_grounded?: unknown;
    aei_v1_approved_evidence?: unknown;
    aei_v1_activation_trust?: unknown;
  };
  status?: string | null;
  ai_suggestions?: Record<string, unknown> | null;
  teacher_overrides?: Record<string, unknown> | null;
  approved_by?: string | null;
  approved_at?: string | null;
  curriculum_pack_id?: string | null;
  question_paper_id?: string | null;
  citation_ids?: string[] | null;
  question_paper_grounded?: boolean | null;
  evaluation_grounded?: boolean | null;
};

type EvidenceDecisionRow = {
  questionNo: string;
  aiMarks: string;
  finalMarks: string;
  maxMarks: string;
  overrideApplied: boolean;
  overrideReason: string;
  manualReviewRequired: boolean;
  manualReviewReason: string;
};

function EvaluationEvidencePanel({ evaluation }: { evaluation: EvaluationEvidence }) {
  const ledger = evaluation.evidence_ledger || {};
  const packId =
    evaluation.curriculum_pack_id ||
    (typeof ledger.curriculum_pack_id === "string" ? ledger.curriculum_pack_id : "");
  const paperId =
    evaluation.question_paper_id ||
    (typeof ledger.question_paper_id === "string" ? ledger.question_paper_id : "");
  const citations =
    evaluation.citation_ids ||
    (Array.isArray(ledger.citation_ids) ? ledger.citation_ids.map(String) : []);
  const approvedEvidence = asRecord(ledger.aei_v1_approved_evidence);
  const activationTrust = asRecord(ledger.aei_v1_activation_trust);
  const downstreamContract = asRecord(approvedEvidence?.downstream_contract);
  const approvedEvidenceAvailable = approvedEvidence?.approved_evidence === true;
  const approvedForDownstream =
    approvedEvidence?.approved_for_downstream === true || approvedEvidenceAvailable;
  const isApproved = evaluation.status === "approved" || ledger.evaluation_status === "approved";
  const questionPaperGrounded =
    evaluation.question_paper_grounded === true || ledger.question_paper_grounded === true;
  const evaluationGrounded =
    evaluation.evaluation_grounded === true || ledger.evaluation_grounded === true;
  const decisionRows = buildEvidenceDecisionRows(evaluation, approvedEvidence);
  if (!packId && !paperId && !approvedEvidence && !isApproved) return null;

  const postureTone: AeiBadgeTone = isApproved ? "success" : "warning";
  const postureLabel = isApproved
    ? approvedEvidenceAvailable
      ? "Teacher-approved evidence"
      : "Teacher approved"
    : "Draft AI suggestions";
  const postureText = isApproved
    ? approvedForDownstream
      ? "Teacher decision is the source of truth for downstream learning intelligence."
      : "Approved marks exist; detailed approved-evidence metadata is not available."
    : "Not approved for downstream use yet. Teacher approval is required before learning intelligence or parent/student visibility.";
  const sourceOfTruth =
    stringValue(downstreamContract?.source_of_truth) ||
    (approvedEvidenceAvailable ? "teacher_decision" : "");

  return (
    <div
      style={{
        display: "grid",
        gap: 10,
        padding: 12,
        marginBottom: 16,
        borderRadius: 12,
        border: "1px solid var(--border)",
        background: "var(--surface-muted)",
        fontSize: 12,
        color: "var(--text-muted)",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
        <strong style={{ color: "var(--text-primary)" }}>Evidence and approval posture</strong>
        <span style={trustChipStyle(postureTone)}>{postureLabel}</span>
      </div>
      <div>{postureText}</div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
        {packId && <span style={metaChip}>CurriculumPack {shortId(packId)}</span>}
        {paperId && <span style={metaChip}>Question paper {shortId(paperId)}</span>}
        <span style={trustChipStyle(questionPaperGrounded ? "success" : "warning")}>
          {questionPaperGrounded ? "Question paper grounded" : "Question paper grounding unclear"}
        </span>
        <span style={trustChipStyle(evaluationGrounded ? "success" : "warning")}>
          {evaluationGrounded ? "Grounded evaluation" : "Needs citation review"}
        </span>
        <span style={metaChip}>{citations.length} citation{citations.length === 1 ? "" : "s"}</span>
        {sourceOfTruth && <span style={trustChipStyle("success")}>Source: {sourceOfTruth}</span>}
        {activationTrust?.manual_review_acknowledgement_required === true && (
          <span style={trustChipStyle("warning")}>Manual-review acknowledgement enforced</span>
        )}
        {typeof activationTrust?.manual_review_required_count === "number" && (
          <span style={metaChip}>
            {activationTrust.manual_review_required_count} review-required question
            {activationTrust.manual_review_required_count === 1 ? "" : "s"}
          </span>
        )}
        {approvedEvidence?.raw_student_answer_excluded === true && (
          <span style={metaChip}>Raw answer excluded from approved evidence</span>
        )}
      </div>
      {decisionRows.length > 0 && (
        <div style={{ display: "grid", gap: 6 }}>
          <strong style={{ color: "var(--text-primary)" }}>Approved decision summary</strong>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
            <thead>
              <tr>
                <th style={rubricTh}>Q</th>
                <th style={rubricTh}>AI suggestion</th>
                <th style={rubricTh}>Teacher final</th>
                <th style={rubricTh}>Decision evidence</th>
              </tr>
            </thead>
            <tbody>
              {decisionRows.map((row) => (
                <tr key={row.questionNo}>
                  <td style={rubricTd}>{row.questionNo}</td>
                  <td style={rubricTd}>{row.aiMarks} / {row.maxMarks}</td>
                  <td style={rubricTd}>{row.finalMarks} / {row.maxMarks}</td>
                  <td style={rubricTd}>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                      <span style={trustChipStyle(row.overrideApplied ? "warning" : "success")}>
                        {row.overrideApplied ? "Teacher override" : "Suggestion accepted"}
                      </span>
                      {row.manualReviewRequired && <span style={trustChipStyle("warning")}>Manual review was required</span>}
                    </div>
                    {row.overrideApplied && (
                      <div style={{ marginTop: 4 }}>
                        <strong style={{ color: "var(--text-primary)" }}>Reason:</strong>{" "}
                        {row.overrideReason || "Reason not recorded."}
                      </div>
                    )}
                    {row.manualReviewReason && (
                      <div style={{ marginTop: 4 }}>
                        <strong style={{ color: "var(--text-primary)" }}>Review note:</strong> {row.manualReviewReason}
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function shortId(value: string) {
  return String(value).slice(0, 8);
}

type UnknownRecord = Record<string, unknown>;

function asRecord(value: unknown): UnknownRecord | null {
  return value && typeof value === "object" && !Array.isArray(value) ? (value as UnknownRecord) : null;
}

function stringValue(value: unknown): string {
  return typeof value === "string" ? value.trim() : "";
}

function displayValue(value: unknown): string {
  if (value === null || value === undefined || value === "") return "—";
  if (typeof value === "number") return Number.isInteger(value) ? String(value) : String(Number(value.toFixed(2)));
  return String(value);
}

function buildEvidenceDecisionRows(
  evaluation: EvaluationEvidence,
  approvedEvidence: UnknownRecord | null,
): EvidenceDecisionRow[] {
  const approvedQuestions = asRecord(approvedEvidence?.questions);
  if (approvedQuestions && Object.keys(approvedQuestions).length > 0) {
    return Object.entries(approvedQuestions)
      .sort(sortQuestionEntries)
      .map(([questionNo, raw]) => {
        const question = asRecord(raw);
        const original = asRecord(question?.original_suggestion);
        const finalDecision = asRecord(question?.final_teacher_decision);
        const maxMarks = displayValue(finalDecision?.max_marks ?? original?.max_marks);
        return {
          questionNo,
          aiMarks: displayValue(original?.marks_suggested),
          finalMarks: displayValue(finalDecision?.final_marks),
          maxMarks,
          overrideApplied: finalDecision?.override_applied === true,
          overrideReason: stringValue(finalDecision?.override_reason),
          manualReviewRequired:
            finalDecision?.manual_review_was_required === true ||
            original?.manual_review_required === true,
          manualReviewReason: stringValue(original?.manual_review_reason),
        };
      });
  }

  if (evaluation.status !== "approved") return [];

  return Object.entries(evaluation.ai_suggestions || {})
    .sort(sortQuestionEntries)
    .map(([questionNo, raw]) => {
      const suggestion = asRecord(raw);
      const override = asRecord(evaluation.teacher_overrides?.[questionNo]);
      const suggestedMarks = suggestion?.marks_suggested;
      const finalMarks = override?.marks ?? suggestedMarks;
      return {
        questionNo,
        aiMarks: displayValue(suggestedMarks),
        finalMarks: displayValue(finalMarks),
        maxMarks: displayValue(suggestion?.max_marks),
        overrideApplied: hasChangedMarks(suggestedMarks, finalMarks),
        overrideReason: stringValue(override?.reason),
        manualReviewRequired: suggestion?.manual_review_required === true,
        manualReviewReason: stringValue(suggestion?.manual_review_reason),
      };
    });
}

function sortQuestionEntries([left]: [string, unknown], [right]: [string, unknown]) {
  return left.localeCompare(right, undefined, { numeric: true, sensitivity: "base" });
}

const btn: React.CSSProperties = { width: "auto", padding: "8px 18px", borderRadius: "var(--radius-full)", fontSize: 13 };
const OVERRIDE_REASON_MAX_LENGTH = 240;

type EvalSuggestion = AeiSuggestionLike & {
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

type EvaluationWithOverrides = {
  ai_suggestions?: Record<string, { marks_suggested?: unknown }>;
  teacher_overrides?: Record<string, { marks?: unknown; reason?: unknown; aei_v1_manual_review_acknowledgement?: unknown }>;
  evidence_ledger?: { aei_v1_activation_trust?: unknown } | null;
};

function buildOverrideMarks(evaluation: EvaluationWithOverrides | null | undefined): Record<string, string> {
  const marks: Record<string, string> = {};
  Object.entries(evaluation?.ai_suggestions || {}).forEach(([qno, raw]) => {
    const override = evaluation?.teacher_overrides?.[qno]?.marks;
    marks[qno] = String(override ?? raw.marks_suggested);
  });
  return marks;
}

function buildOverrideReasons(evaluation: EvaluationWithOverrides | null | undefined): Record<string, string> {
  const reasons: Record<string, string> = {};
  Object.entries(evaluation?.teacher_overrides || {}).forEach(([qno, override]) => {
    if (typeof override?.reason === "string") {
      reasons[qno] = override.reason;
    }
  });
  return reasons;
}

function buildManualReviewAcknowledgements(evaluation: EvaluationWithOverrides | null | undefined): Record<string, boolean> {
  const acknowledgements: Record<string, boolean> = {};
  Object.entries(evaluation?.teacher_overrides || {}).forEach(([qno, override]) => {
    const ack = asRecord(override?.aei_v1_manual_review_acknowledgement);
    if (ack?.acknowledged === true) acknowledgements[qno] = true;
  });
  return acknowledgements;
}

function manualReviewQuestionNumbers(evaluation: EvaluationWithOverrides | null | undefined): string[] {
  return Object.entries(evaluation?.ai_suggestions || {})
    .filter(([, suggestion]) => suggestionRequiresManualReview(suggestion as AeiSuggestionLike))
    .map(([qno]) => qno);
}

function suggestionRequiresManualReview(suggestion: AeiSuggestionLike): boolean {
  const raw = suggestion as Record<string, unknown>;
  const capabilityMode = typeof suggestion.capability_mode === "string"
    ? suggestion.capability_mode.trim().toLowerCase()
    : "";
  return (
    suggestion.manual_review_required === true ||
    suggestion.visual_science_review_required === true ||
    suggestion.assist_only === true ||
    suggestion.checklist_only === true ||
    raw.teacher_correction_required === true ||
    raw.requires_language_teacher_review === true ||
    ["assist", "checklist", "manual_review", "unsupported", "expansion"].includes(capabilityMode)
  );
}

function manualReviewAcknowledgementRequired(evaluation: EvaluationWithOverrides | null | undefined): boolean {
  const ledger = evaluation?.evidence_ledger || {};
  const activationTrust = asRecord(ledger.aei_v1_activation_trust);
  return activationTrust?.manual_review_acknowledgement_required === true;
}

function hasChangedMarks(suggested: unknown, finalMarks: unknown): boolean {
  const suggestedNumber = Number(suggested);
  const finalNumber = Number(finalMarks);
  if (!Number.isFinite(suggestedNumber) || !Number.isFinite(finalNumber)) return false;
  return finalNumber !== suggestedNumber;
}

function hasSavedOverride(evaluation: EvaluationWithOverrides | null | undefined, qno: string): boolean {
  return Boolean(evaluation?.teacher_overrides && Object.prototype.hasOwnProperty.call(evaluation.teacher_overrides, qno));
}

function savedOverrideReason(evaluation: EvaluationWithOverrides | null | undefined, qno: string): string {
  const reason = evaluation?.teacher_overrides?.[qno]?.reason;
  return typeof reason === "string" ? reason.trim() : "";
}

function savedManualReviewAcknowledgement(evaluation: EvaluationWithOverrides | null | undefined, qno: string): boolean {
  const ack = asRecord(evaluation?.teacher_overrides?.[qno]?.aei_v1_manual_review_acknowledgement);
  return ack?.acknowledged === true;
}

function formatQuestionList(qnos: string[]): string {
  return qnos.map((qno) => `Q${qno}`).join(", ");
}

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

function trustChipStyle(tone: AeiBadgeTone): React.CSSProperties {
  const toneStyles: Record<AeiBadgeTone, React.CSSProperties> = {
    neutral: {
      color: "var(--text-muted)",
      borderColor: "var(--border)",
      background: "rgba(255, 255, 255, 0.02)",
    },
    success: {
      color: "var(--success, #2f9e44)",
      borderColor: "rgba(47, 158, 68, 0.45)",
      background: "rgba(47, 158, 68, 0.08)",
    },
    warning: {
      color: "var(--warning, #f59f00)",
      borderColor: "rgba(245, 159, 0, 0.45)",
      background: "rgba(245, 159, 0, 0.08)",
    },
    danger: {
      color: "var(--danger, #e03131)",
      borderColor: "rgba(224, 49, 49, 0.45)",
      background: "rgba(224, 49, 49, 0.08)",
    },
  };
  return {
    ...metaChip,
    ...toneStyles[tone],
  };
}

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
