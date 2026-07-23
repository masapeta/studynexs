"use client";

import { Suspense, useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import { FileText, CalendarDays, Clock, Sparkles, Save, Check, Printer, KeyRound, Copy } from "lucide-react";
import { api, fetchProtectedDocumentUrl, getApiErrorMessage } from "@/lib/api";
import { parseTopicList, AI_INPUT } from "@/lib/ai-input-limits";
import { AppSelect } from "@/components/ui/AppSelect";
import { PageHeaderCard } from "@/components/layout/PageHeaderCard";
import { formatClassLabel, sortClasses } from "@/lib/format";
import { DocumentPreviewModal } from "@/components/DocumentPreviewModal";
import { CurriculumGroundingBadge } from "@/components/curriculum/CurriculumGroundingBadge";
import { AcademicIntelligenceBanner } from "@/components/curriculum/AcademicIntelligenceBanner";
import { useAuth } from "@/lib/auth-context";
import Link from "next/link";
import { TEACHING } from "@/lib/dashboard-routes";

type Question = {
  number: string;
  text: string;
  marks: number;
  type: string;
  options?: string[];
  answer_key?: string;
};
type Section = { title: string; instructions?: string | null; questions: Question[] };
type Paper = {
  id: string;
  title: string;
  board: string;
  grade: string;
  subject_name: string;
  total_marks: number;
  duration_minutes?: number | null;
  general_instructions?: string | null;
  sections: Section[];
  status: string;
  ai_model?: string | null;
  pack_id?: string | null;
  pack_status?: string | null;
  pack_version?: number | null;
  grounded?: boolean;
  grounded_at?: string | null;
  grounding_sources?: { chapter?: string; topic?: string; index?: number; pack_status?: string; pack_version?: number }[] | null;
  can_approve?: boolean;
  can_edit?: boolean;
  can_submit?: boolean;
  can_reject?: boolean;
  rejection_reason?: string | null;
  credits_used?: number | null;
};

type CopilotReview = {
  summary: string;
  overall_quality: string;
  suggestions: {
    section_title?: string | null;
    question_number?: string | null;
    issue?: string | null;
    suggestion?: string | null;
    citation_sources?: { chapter?: string; topic?: string }[];
  }[];
};

type CurriculumPack = { id: string; status: string; board: string; book_title?: string | null };
type ClassRow = { id: string; grade: string; section: string };
type SubjectRow = { id: string; name: string };
type RecentPaper = {
  id: string;
  title: string;
  grade: string;
  subject_name: string;
  total_marks: number;
  status: string;
};
type AiUsageSummary = {
  papers_total: number;
  papers_this_month: number;
  est_hours_saved: number;
};
type AiUsageLogRow = {
  usage_id: string;
  generated_by: string;
  class_label: string;
  subject: string;
  credits_used: number;
  approval_status: string;
  rejection_reason?: string | null;
};

function AiPapersPageInner() {
  const { permissions } = useAuth();
  // Deep-link prefill (e.g. from a mastery weakness flag):
  // /dashboard/ai-papers?class_id=…&subject_id=…&topics=Algebra&difficulty=easy
  const searchParams = useSearchParams();
  const prefill = useRef({
    classId: searchParams.get("class_id") || "",
    subjectId: searchParams.get("subject_id") || "",
    packId: searchParams.get("pack_id") || "",
  });

  const [classes, setClasses] = useState<ClassRow[]>([]);
  const [subjects, setSubjects] = useState<SubjectRow[]>([]);
  const [classId, setClassId] = useState("");
  const [subjectId, setSubjectId] = useState("");
  const [topics, setTopics] = useState(searchParams.get("topics") || "");
  const [totalMarks, setTotalMarks] = useState(80);
  const [duration, setDuration] = useState(180);
  const [difficulty, setDifficulty] = useState(searchParams.get("difficulty") || "balanced");
  const [generateMode, setGenerateMode] = useState<"full" | "from_bank">("full");
  const [packId, setPackId] = useState("");
  const [packs, setPacks] = useState<CurriculumPack[]>([]);
  const [useGrounding, setUseGrounding] = useState(
    Boolean(searchParams.get("pack_id") || searchParams.get("grounded"))
  );
  const [copilotReview, setCopilotReview] = useState<CopilotReview | null>(null);
  const [reviewBusy, setReviewBusy] = useState(false);
  const [bankCount, setBankCount] = useState<number | null>(null);

  const [generating, setGenerating] = useState(false);
  const [openingDoc, setOpeningDoc] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [paper, setPaper] = useState<Paper | null>(null);
  const [showAnswers, setShowAnswers] = useState(false);
  const [recent, setRecent] = useState<RecentPaper[]>([]);
  const [usage, setUsage] = useState<AiUsageSummary | null>(null);
  const [credits, setCredits] = useState<{
    credits_remaining: number;
    monthly_limit: number;
    user_credits_remaining?: number | null;
    user_monthly_limit?: number | null;
    at_soft_limit?: boolean;
    at_hard_limit?: boolean;
    purpose_costs?: Record<string, number>;
  } | null>(null);
  const [usageLog, setUsageLog] = useState<AiUsageLogRow[]>([]);
  const [docPreview, setDocPreview] = useState<{ url: string; title: string } | null>(null);
  const openDocRef = useRef(false);
  const isAdmin = permissions?.role === "admin" || permissions?.role === "super_admin";

  useEffect(() => {
    api("/api/v1/academic/classes?page_size=100")
      .then((r) => {
        const items = sortClasses<ClassRow>((r.items || r.data || []) as ClassRow[]);
        setClasses(items);
        const wanted = prefill.current.classId;
        const match = wanted && items.find((c) => c.id === wanted);
        if (match) setClassId(match.id);
        else if (items[0]) setClassId(items[0].id);
      })
      .catch((e) => console.error(e));
    loadRecent();
    api<AiUsageSummary>("/api/v1/ai/usage").then(setUsage).catch(() => {});
    api("/api/v1/ai/credits").then(setCredits).catch(() => {});
    if (permissions?.role === "admin" || permissions?.role === "super_admin") {
      api("/api/v1/ai/credits/usage-log")
        .then((r) => setUsageLog((r.items || []) as AiUsageLogRow[]))
        .catch(() => {});
    }
  }, [permissions?.role]);

  useEffect(() => {
    if (!classId) return;
    api(`/api/v1/academic/subjects?class_id=${classId}`)
      .then((r) => {
        const items = (r.items || r.data || (Array.isArray(r) ? r : [])) as SubjectRow[];
        setSubjects(items);
        // Consume the subject prefill once; later class changes pick the first subject.
        const wanted = prefill.current.subjectId;
        prefill.current.subjectId = "";
        const match = wanted && items.find((s) => s.id === wanted);
        setSubjectId(match ? match.id : items[0]?.id || "");
      })
      .catch((e) => console.error(e));
  }, [classId]);

  useEffect(() => {
    if (!classId || !subjectId) return;
    api(`/api/v1/ai/question-bank/summary?class_id=${classId}&subject_id=${subjectId}`)
      .then((r) => setBankCount(typeof r.count === "number" ? r.count : 0))
      .catch(() => setBankCount(null));
    api(`/api/v1/curriculum/packs?class_id=${classId}&subject_id=${subjectId}`)
      .then((r) => {
        const items: CurriculumPack[] = (r.data || []).filter(
          (p: CurriculumPack) => p.status === "approved"
        );
        setPacks(items);
        const wanted = prefill.current.packId;
        prefill.current.packId = "";
        const match = wanted && items.find((p: CurriculumPack) => p.id === wanted);
        setPackId(match ? match.id : items[0]?.id || "");
      })
      .catch(() => setPacks([]));
  }, [classId, subjectId]);

  useEffect(() => {
    return () => {
      if (docPreview?.url) URL.revokeObjectURL(docPreview.url);
    };
  }, [docPreview?.url]);

  function closeDocPreview() {
    setDocPreview((prev) => {
      if (prev?.url) URL.revokeObjectURL(prev.url);
      return null;
    });
  }

  function loadRecent() {
    api<RecentPaper[] | { items?: RecentPaper[] }>("/api/v1/ai/question-papers")
      .then((r) => setRecent(Array.isArray(r) ? r : r.items || []))
      .catch(() => {});
  }

  async function generate() {
    if (!classId || !subjectId) {
      setError("Pick a class and subject first.");
      return;
    }
    if (useGrounding && generateMode === "full" && !packId) {
      setError("Select an approved curriculum pack for grounded generation.");
      return;
    }
    const cost =
      generateMode === "from_bank"
        ? (credits?.purpose_costs?.qp_from_bank ?? 2)
        : (credits?.purpose_costs?.qp_full ?? 5);
    const remaining = credits?.user_credits_remaining ?? credits?.credits_remaining;
    if (remaining !== undefined && remaining !== null && remaining < cost) {
      setError("Not enough AI credits remaining this month. Contact your class incharge or principal.");
      return;
    }
    if (generateMode === "from_bank" && (bankCount === 0 || bankCount === null)) {
      setError(
        bankCount === 0
          ? "No approved questions in the bank for this class and subject. Approve a paper first."
          : "Could not load question bank status. Try again."
      );
      return;
    }
    const modeLabel =
      generateMode === "from_bank"
        ? "From question bank (reuses approved questions; AI fills gaps only)"
        : "Full AI generate";
    if (
      !window.confirm(
        `Mode: ${modeLabel}\nThis will use ${cost} AI credits.\n\nGenerated drafts consume credits even if not approved.\n\nDraft papers need class-incharge approval before use in exams.\n\nGenerate paper?`
      )
    ) {
      return;
    }
    setError("");
    setGenerating(true);
    setPaper(null);
    setCopilotReview(null);
    try {
      let topicList: string[];
      try {
        topicList = parseTopicList(topics);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Invalid topics");
        setGenerating(false);
        return;
      }
      const endpoint =
        generateMode === "from_bank"
          ? "/api/v1/ai/question-papers/generate-from-bank"
          : "/api/v1/ai/question-papers/generate";
      const res = await api<Paper>(endpoint, {
        method: "POST",
        body: JSON.stringify({
          class_id: classId,
          subject_id: subjectId,
          topics: topicList,
          total_marks: Number(totalMarks),
          duration_minutes: Number(duration),
          difficulty,
          ...(useGrounding && generateMode === "full" && packId ? { pack_id: packId } : {}),
        }),
      });
      setPaper(res);
      setShowAnswers(false);
      loadRecent();
      api("/api/v1/ai/credits").then(setCredits).catch(() => {});
      api<AiUsageSummary>("/api/v1/ai/usage").then(setUsage).catch(() => {});
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to generate paper. Please try again."));
    } finally {
      setGenerating(false);
    }
  }

  async function runCopilotReview() {
    if (!paper?.id || !paper.grounded) return;
    const cost = credits?.purpose_costs?.quality_check ?? 1;
    const remaining = credits?.user_credits_remaining ?? credits?.credits_remaining;
    if (remaining !== undefined && remaining !== null && remaining < cost) {
      setError("Not enough AI credits for Teacher Copilot review.");
      return;
    }
    setReviewBusy(true);
    setError("");
    try {
      const res = await api<CopilotReview>(`/api/v1/ai/copilot/question-papers/${paper.id}/review`, {
        method: "POST",
      });
      setCopilotReview(res);
      api("/api/v1/ai/credits").then(setCredits).catch(() => {});
    } catch (e) {
      setError(getApiErrorMessage(e, "Copilot review failed."));
    } finally {
      setReviewBusy(false);
    }
  }

  function updateQuestion(si: number, qi: number, value: string) {
    setPaper((p) => {
      if (!p) return p;
      const sections = p.sections.map((s, i) =>
        i !== si
          ? s
          : { ...s, questions: s.questions.map((q, j) => (j !== qi ? q : { ...q, text: value })) }
      );
      return { ...p, sections };
    });
  }

  async function saveEdits() {
    if (!paper) return;
    setSaving(true);
    setError("");
    try {
      const res = await api<Paper>(`/api/v1/ai/question-papers/${paper.id}`, {
        method: "PUT",
        body: JSON.stringify({
          title: paper.title,
          general_instructions: paper.general_instructions,
          sections: paper.sections,
        }),
      });
      setPaper(res);
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to save edits."));
    } finally {
      setSaving(false);
    }
  }

  async function submitForApproval() {
    if (!paper) return;
    try {
      const res = await api<Paper>(`/api/v1/ai/question-papers/${paper.id}/submit`, { method: "POST" });
      setPaper(res);
      loadRecent();
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to submit for approval."));
    }
  }

  async function rejectPaper() {
    if (!paper) return;
    const reason = window.prompt("Reason for rejection (shown to teacher):", "Difficulty too high");
    if (!reason?.trim()) return;
    try {
      const res = await api(`/api/v1/ai/question-papers/${paper.id}/reject`, {
        method: "POST",
        body: JSON.stringify({ reason: reason.trim() }),
      });
      setPaper(res);
      loadRecent();
      if (isAdmin) {
        api("/api/v1/ai/credits/usage-log")
          .then((r) => setUsageLog(r.items || []))
          .catch(() => {});
      }
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to reject."));
    }
  }

  async function approve() {
    if (!paper) return;
    try {
      const res = await api(`/api/v1/ai/question-papers/${paper.id}/approve`, { method: "POST" });
      setPaper(res);
      loadRecent();
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to approve."));
    }
  }

  async function openPdf(answers: boolean) {
    if (!paper || openingDoc || openDocRef.current) return;
    openDocRef.current = true;
    setOpeningDoc(true);
    setError("");
    try {
      const url = await fetchProtectedDocumentUrl(
        `/api/v1/ai/question-papers/${paper.id}/pdf?answers=${answers}`
      );
      setDocPreview((prev) => {
        if (prev?.url) URL.revokeObjectURL(prev.url);
        return {
          url,
          title: answers ? "Answer key (teacher)" : "Question paper",
        };
      });
    } catch (e) {
      setError(getApiErrorMessage(e, "Could not open the paper."));
    } finally {
      openDocRef.current = false;
      setOpeningDoc(false);
    }
  }

  async function openRecent(id: string) {
    try {
      const res = await api(`/api/v1/ai/question-papers/${id}`);
      setPaper(res);
      setShowAnswers(false);
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to load paper."));
    }
  }

  async function duplicate() {
    if (!paper) return;
    setError("");
    try {
      // Clone into a fresh editable DRAFT (same class) — no AI call. Edit, then Approve.
      const res = await api(`/api/v1/ai/question-papers/${paper.id}/duplicate`, {
        method: "POST",
        body: JSON.stringify({}),
      });
      setPaper(res);
      setShowAnswers(false);
      loadRecent();
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to duplicate."));
    }
  }

  const approved = paper?.status === "approved" || paper?.status === "published";
  const rejected = paper?.status === "rejected";
  const pending = paper?.status === "pending_approval";
  const locked = approved || pending;
  const canApprove = paper?.can_approve ?? permissions?.can_approve_question_papers ?? false;
  const canReject = paper?.can_reject ?? false;
  const canSubmit = paper?.can_submit ?? false;
  const canEdit = paper?.can_edit !== false && !locked;

  function statusBadgeClass(status: string) {
    if (status === "approved" || status === "published") return "badge-success";
    if (status === "rejected") return "badge-danger";
    if (status === "pending_approval") return "badge-info";
    return "badge-warning";
  }

  return (
    <>
      {docPreview && (
        <DocumentPreviewModal
          title={docPreview.title}
          blobUrl={docPreview.url}
          onClose={closeDocPreview}
        />
      )}
      <PageHeaderCard
        title="AI Question Paper Generator"
        subtitle="Draft a board-style paper from your syllabus — review, edit, submit for approval. AI credits are charged when you generate, not when the paper is approved."
      />

      {credits && (
        <div className="card sn-credits-banner">
          <div
            className={`stat-icon-container ${credits.at_soft_limit ? "icon-orange" : "icon-blue"}`}
          >
            <Sparkles size={20} />
          </div>
          <div style={{ flex: 1, minWidth: 200 }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase" }}>
              AI Credits Remaining
            </div>
            <div style={{ fontSize: 22, fontWeight: 800 }}>
              {credits.user_credits_remaining ?? credits.credits_remaining}
              <span style={{ fontSize: 14, fontWeight: 500, color: "var(--text-muted)" }}>
                {" "}/ {credits.user_monthly_limit ?? credits.monthly_limit} this month
              </span>
            </div>
            {credits.at_soft_limit && !credits.at_hard_limit && (
              <div style={{ fontSize: 12, color: "var(--warning)", marginTop: 4 }}>
                School is above 80% of monthly AI budget — principal has been notified.
              </div>
            )}
          </div>
          <div style={{ fontSize: 13, color: "var(--text-secondary)", maxWidth: 420 }}>
            Full paper: <strong>{credits.purpose_costs?.qp_full ?? 5} credits</strong>
            {" · "}Regen section: {credits.purpose_costs?.qp_regen_section ?? 2}
            {" · "}Generated drafts consume credits even if rejected
          </div>
        </div>
      )}

      {usage && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16, marginBottom: 24 }}>
          <div className="card" style={{ display: "flex", alignItems: "center", gap: 16, padding: 20 }}>
            <div className="stat-icon-container icon-blue"><FileText size={20} /></div>
            <div>
              <div className="stat-label">Papers generated</div>
              <div style={{ fontSize: 24, fontWeight: 700 }}>{usage.papers_total}</div>
            </div>
          </div>
          <div className="card" style={{ display: "flex", alignItems: "center", gap: 16, padding: 20 }}>
            <div className="stat-icon-container icon-green"><CalendarDays size={20} /></div>
            <div>
              <div className="stat-label">This month</div>
              <div style={{ fontSize: 24, fontWeight: 700 }}>{usage.papers_this_month}</div>
            </div>
          </div>
          <div className="card" style={{ display: "flex", alignItems: "center", gap: 16, padding: 20 }}>
            <div className="stat-icon-container icon-purple"><Clock size={20} /></div>
            <div>
              <div className="stat-label">Est. teacher-hours saved</div>
              <div style={{ fontSize: 24, fontWeight: 700 }}>~{usage.est_hours_saved}</div>
            </div>
          </div>
        </div>
      )}

      {/* Generator form */}
      <div className="card" style={{ marginBottom: 24, padding: 24 }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 }}>
          <div>
            <label className="stat-label">Class</label>
            <AppSelect
              variant="field"
              value={classId}
              onChange={setClassId}
              aria-label="Class"
              options={classes.map((c) => ({
                value: c.id,
                label: formatClassLabel(c.grade, c.section),
              }))}
            />
          </div>
          <div>
            <label className="stat-label">Subject</label>
            <AppSelect
              variant="field"
              value={subjectId}
              onChange={setSubjectId}
              aria-label="Subject"
              placeholder={subjects.length === 0 ? "No subjects for this class" : "Select…"}
              options={subjects.map((s) => ({ value: s.id, label: s.name }))}
            />
          </div>
        </div>

        <div style={{ marginBottom: 16 }}>
          <label className="stat-label">Topics / chapters (one per line or comma-separated)</label>
          <p style={{ fontSize: 12, color: "var(--text-muted)", margin: "0 0 6px" }}>
            With curriculum grounding, topics steer RAG retrieval from the approved pack.
          </p>
          <textarea
            className="form-input"
            value={topics}
            onChange={(e) => setTopics(e.target.value.slice(0, AI_INPUT.topicsRawMaxLength))}
            maxLength={AI_INPUT.topicsRawMaxLength}
            rows={3}
            placeholder="Real Numbers, Polynomials, Quadratic Equations, Triangles, Trigonometry"
            style={{ ...selStyle, resize: "vertical", fontFamily: "inherit" }}
          />
        </div>

        {generateMode === "full" && (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 }}>
            <div>
              <label className="stat-label">Curriculum grounding</label>
              <AppSelect
                variant="field"
                value={useGrounding ? "grounded" : "free"}
                onChange={(v) => setUseGrounding(v === "grounded")}
                aria-label="Curriculum grounding"
                options={[
                  { value: "free", label: "Free-text topics (legacy)" },
                  { value: "grounded", label: "Grounded in approved pack" },
                ]}
              />
            </div>
            {useGrounding && (
              <div>
                <label className="stat-label">Approved curriculum pack</label>
                <AppSelect
                  variant="field"
                  value={packId}
                  onChange={setPackId}
                  aria-label="Curriculum pack"
                  options={
                    packs.length
                      ? packs.map((p) => ({
                          value: p.id,
                          label: p.book_title ? `${p.board} — ${p.book_title}` : `${p.board} pack`,
                        }))
                      : [{ value: "", label: "No approved packs" }]
                  }
                />
              </div>
            )}
          </div>
        )}

        {useGrounding && packId ? (
          <div style={{ marginBottom: 16 }}>
            <AcademicIntelligenceBanner packId={packId} />
          </div>
        ) : useGrounding && !packs.length && classId && subjectId ? (
          <p style={{ fontSize: 13, color: "var(--text-secondary)", marginBottom: 16 }}>
            No approved pack for grounding.
            {permissions?.can_edit_curriculum_draft ? (
              <>
                {" "}
                <Link href={TEACHING.curriculumOnboarding}>Complete academic onboarding</Link> first.
              </>
            ) : (
              " Ask your class incharge or school administrator to approve a curriculum pack."
            )}
          </p>
        ) : null}

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr auto", gap: 16, alignItems: "end" }}>
          <div>
            <label className="stat-label">Generation mode</label>
            <AppSelect
              variant="field"
              value={generateMode}
              onChange={(v) => setGenerateMode(v as "full" | "from_bank")}
              aria-label="Generation mode"
              options={[
                { value: "full", label: `Full AI (${credits?.purpose_costs?.qp_full ?? 5} credits)` },
                {
                  value: "from_bank",
                  label: `From question bank (${credits?.purpose_costs?.qp_from_bank ?? 2} credits)`,
                },
              ]}
            />
            {generateMode === "from_bank" && bankCount !== null && (
              <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 4 }}>
                {bankCount} approved question{bankCount === 1 ? "" : "s"} in bank
              </div>
            )}
          </div>
          <div>
            <label className="stat-label">Total marks</label>
            <input
              type="number"
              className="form-input"
              value={totalMarks}
              onChange={(e) => setTotalMarks(Number(e.target.value))}
              style={selStyle}
            />
          </div>
          <div>
            <label className="stat-label">Duration (min)</label>
            <input
              type="number"
              className="form-input"
              value={duration}
              onChange={(e) => setDuration(Number(e.target.value))}
              style={selStyle}
            />
          </div>
          <div>
            <label className="stat-label">Difficulty</label>
            <AppSelect
              variant="field"
              value={difficulty}
              onChange={setDifficulty}
              aria-label="Difficulty"
              options={[
                { value: "easy", label: "Easy" },
                { value: "balanced", label: "Balanced" },
                { value: "hard", label: "Hard" },
              ]}
            />
          </div>
          <button
            className="btn btn-primary"
            onClick={generate}
            disabled={generating}
            style={{ width: "auto", padding: "10px 24px", borderRadius: "var(--radius-full)" }}
          >
            {generating ? "Generating…" : <><Sparkles size={16} /> {generateMode === "from_bank" ? "Compose from bank" : "Generate Paper"}</>}
          </button>
        </div>

        {error && (
          <div style={{ marginTop: 14, color: "var(--danger)", fontSize: 13 }}>{error}</div>
        )}
        {generating && (
          <div style={{ marginTop: 16, display: "flex", alignItems: "center", gap: 12, color: "var(--text-muted)" }}>
            <div className="spinner" style={{ width: 20, height: 20 }} />
            Drafting your paper{generateMode === "from_bank" ? " from the bank" : " with AI"} — this usually takes 15–30 seconds…
          </div>
        )}
      </div>

      {/* Paper preview */}
      {paper && (
        <div className="card" style={{ padding: 24, marginBottom: 24 }}>
          <div
            style={{
              background: approved ? "var(--success-light)" : "var(--accent-50)",
              border: `1px solid ${approved ? "var(--success)" : "var(--accent-100)"}`,
              borderRadius: "var(--radius-md)",
              padding: "10px 14px",
              marginBottom: 16,
              fontSize: 13,
              color: approved ? "#0a6b4b" : "var(--accent-dark)",
            }}
          >
            {approved
              ? "Class teacher approved — ready to print and hand out."
              : rejected
                ? `Rejected${paper.rejection_reason ? `: ${paper.rejection_reason}` : ""}. Saved for audit — you can still edit, duplicate, or resubmit. Re-approval adds it to the question bank.`
                : pending
                  ? "Awaiting class-incharge approval."
                  : canApprove
                    ? "Draft ready for review. Approve or reject — credits were charged at generation."
                    : "Edit if needed, then submit for class-incharge approval."}
          </div>

          {paper.credits_used != null && paper.credits_used > 0 && (
            <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 12 }}>
              AI credits used for this paper: <strong>{paper.credits_used}</strong> (charged at generation)
            </div>
          )}

          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16 }}>
            <input
              className="form-input"
              value={paper.title}
              onChange={(e) => setPaper({ ...paper, title: e.target.value })}
              disabled={!canEdit}
              style={{ ...selStyle, fontSize: 18, fontWeight: 700, flex: 1 }}
            />
            <span className={`badge ${statusBadgeClass(paper.status)}`} style={{ whiteSpace: "nowrap" }}>
              {paper.status.replace(/_/g, " ")}
            </span>
          </div>

          <div style={{ color: "var(--text-muted)", fontSize: 13, margin: "8px 0 16px" }}>
            {paper.board} · {paper.grade} · {paper.subject_name} · {paper.total_marks} marks ·{" "}
            {paper.duration_minutes} min{paper.ai_model ? ` · ${paper.ai_model}` : ""}
          </div>

          <CurriculumGroundingBadge
            packId={paper.pack_id}
            packStatus={paper.pack_status ?? (paper.grounding_sources?.[0]?.pack_status as string | undefined)}
            packVersion={paper.pack_version ?? (paper.grounding_sources?.[0]?.pack_version as number | undefined)}
            grounded={paper.grounded}
            groundedAt={paper.grounded_at}
          />

          {paper.grounded && paper.grounding_sources && paper.grounding_sources.length > 0 && (
            <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 12 }}>
              Curriculum sources: {paper.grounding_sources.slice(0, 4).map((s, i) => (
                <span key={i}>{i ? " · " : ""}{s.chapter}{s.topic ? ` › ${s.topic}` : ""}</span>
              ))}
            </div>
          )}

          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 20 }}>
            {canEdit && (
            <button className="btn btn-primary" onClick={saveEdits} disabled={saving}
              style={btnSm}>{saving ? "Saving…" : <><Save size={15} /> Save edits</>}</button>
            )}
            {canSubmit && (
            <button className="btn btn-primary" onClick={submitForApproval} style={btnSm}>
              Submit for approval
            </button>
            )}
            {canApprove && (
            <button className="btn btn-primary" onClick={approve} disabled={approved}
              style={{ ...btnSm, background: approved ? "var(--text-muted)" : "var(--success)" }}>
              {approved ? "Approved" : <><Check size={15} /> Approve</>}
            </button>
            )}
            {canReject && !approved && (
            <button className="btn btn-outline" onClick={rejectPaper} style={{ ...btnSm, color: "var(--danger)", borderColor: "var(--danger)" }}>
              Reject
            </button>
            )}
            <button className="btn btn-outline" onClick={duplicate} style={btnSm} title="Reuse this paper as a new editable draft (no AI cost)">
              <Copy size={15} /> Duplicate
            </button>
            {paper.grounded && canEdit && (
              <button className="btn btn-outline" onClick={runCopilotReview} disabled={reviewBusy} style={btnSm}>
                <Sparkles size={15} /> {reviewBusy ? "Reviewing…" : "Copilot review"}
              </button>
            )}
            <button type="button" className="btn btn-outline" onClick={() => openPdf(false)} disabled={openingDoc} style={btnSm}>
              <Printer size={15} /> {openingDoc ? "Opening…" : "Open / print paper"}
            </button>
            <button type="button" className="btn btn-outline" onClick={() => openPdf(true)} disabled={openingDoc} style={btnSm}>
              <KeyRound size={15} /> Answer key (teacher)
            </button>
            <button className="btn btn-ghost" onClick={() => setShowAnswers((v) => !v)} style={btnSm}>
              {showAnswers ? "Hide answers" : "Show answers inline"}
            </button>
          </div>

          {copilotReview && (
            <div
              className="card"
              style={{
                marginBottom: 20,
                padding: 16,
                background: "var(--bg)",
                border: "1px solid var(--border-light)",
              }}
            >
              <div style={{ fontWeight: 700, marginBottom: 8 }}>Teacher Copilot review</div>
              <p style={{ fontSize: 14, margin: "0 0 12px" }}>{copilotReview.summary}</p>
              <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 12 }}>
                Overall: {copilotReview.overall_quality.replace(/_/g, " ")}
              </div>
              {copilotReview.suggestions.map((s, i) => (
                <div key={i} style={{ fontSize: 13, padding: "8px 0", borderTop: i ? "1px solid var(--border-light)" : "none" }}>
                  <strong>{s.section_title}{s.question_number ? ` · Q${s.question_number}` : ""}</strong>
                  {s.issue && <div style={{ color: "var(--text-muted)" }}>{s.issue}</div>}
                  {s.suggestion && <div>{s.suggestion}</div>}
                </div>
              ))}
            </div>
          )}

          {paper.general_instructions && (
            <div style={{ marginBottom: 16 }}>
              <label className="stat-label">General instructions</label>
              <textarea
                className="form-input"
                value={paper.general_instructions}
                onChange={(e) => setPaper({ ...paper, general_instructions: e.target.value })}
                rows={3}
                style={{ ...selStyle, resize: "vertical", fontFamily: "inherit" }}
              />
            </div>
          )}

          {paper.sections.map((section, si) => (
            <div key={si} style={{ marginBottom: 20 }}>
              <div
                style={{
                  fontWeight: 700,
                  background: "var(--bg)",
                  padding: "6px 12px",
                  borderRadius: "var(--radius-sm)",
                  marginBottom: 8,
                }}
              >
                {section.title}
                {section.instructions && (
                  <span style={{ fontWeight: 400, fontStyle: "italic", color: "var(--text-muted)", marginLeft: 8 }}>
                    {section.instructions}
                  </span>
                )}
              </div>
              {section.questions.map((q, qi) => (
                <div key={qi} style={{ display: "flex", gap: 10, marginBottom: 10, alignItems: "flex-start" }}>
                  <span style={{ fontWeight: 700, minWidth: 28 }}>{q.number}.</span>
                  <div style={{ flex: 1 }}>
                    <textarea
                      value={q.text}
                      onChange={(e) => updateQuestion(si, qi, e.target.value)}
                      rows={Math.max(1, Math.ceil(q.text.length / 90))}
                      style={{
                        width: "100%",
                        border: "1px solid var(--border)",
                        borderRadius: "var(--radius-sm)",
                        padding: "6px 10px",
                        fontFamily: "inherit",
                        fontSize: 14,
                        resize: "vertical",
                      }}
                    />
                    {q.options && q.options.length > 0 && (
                      <div style={{ display: "flex", flexWrap: "wrap", gap: "4px 24px", margin: "4px 0 0 8px", fontSize: 13 }}>
                        {q.options.map((o, oi) => (
                          <span key={oi}>({"abcdefgh"[oi]}) {o}</span>
                        ))}
                      </div>
                    )}
                    {showAnswers && q.answer_key && (
                      <div style={{ marginTop: 4, color: "var(--primary)", fontSize: 13 }}>
                        <b>Ans:</b> {q.answer_key}
                      </div>
                    )}
                  </div>
                  <span style={{ color: "var(--text-muted)", fontWeight: 600, whiteSpace: "nowrap" }}>
                    [{q.marks}]
                  </span>
                </div>
              ))}
            </div>
          ))}
        </div>
      )}

      {/* Recent papers */}
      {recent.length > 0 && (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <div style={{ padding: "14px 24px", fontWeight: 700, borderBottom: "1px solid var(--border)" }}>
            Recent papers
          </div>
          <table className="data-table">
            <thead>
              <tr>
                <th>Title</th>
                <th>Class / Subject</th>
                <th>Marks</th>
                <th>Status</th>
                <th style={{ textAlign: "right" }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {recent.map((p) => (
                <tr key={p.id}>
                  <td style={{ fontWeight: 600 }}>{p.title}</td>
                  <td>{p.grade} · {p.subject_name}</td>
                  <td>{p.total_marks}</td>
                  <td>
                    <span className={`badge ${statusBadgeClass(p.status)}`}>
                      {p.status.replace(/_/g, " ")}
                    </span>
                  </td>
                  <td style={{ textAlign: "right" }}>
                    <button className="btn btn-ghost" onClick={() => openRecent(p.id)} style={btnSm}>
                      Open
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {isAdmin && usageLog.length > 0 && (
        <div className="card" style={{ padding: 0, overflow: "hidden", marginTop: 24 }}>
          <div style={{ padding: "14px 24px", fontWeight: 700, borderBottom: "1px solid var(--border)" }}>
            AI usage log (this month)
          </div>
          <table className="data-table">
            <thead>
              <tr>
                <th>Generated by</th>
                <th>Class</th>
                <th>Subject</th>
                <th>Credits</th>
                <th>Status</th>
                <th>Reason</th>
              </tr>
            </thead>
            <tbody>
              {usageLog.map((row) => (
                <tr key={row.usage_id}>
                  <td>{row.generated_by}</td>
                  <td>{row.class_label}</td>
                  <td>{row.subject}</td>
                  <td>{row.credits_used}</td>
                  <td>
                    <span className={`badge ${statusBadgeClass(row.approval_status)}`}>
                      {row.approval_status.replace(/_/g, " ")}
                    </span>
                  </td>
                  <td style={{ fontSize: 13, color: "var(--text-muted)" }}>{row.rejection_reason || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}

const selStyle: React.CSSProperties = {
  width: "100%",
  padding: "8px 12px",
  borderRadius: "var(--radius-sm)",
  border: "1px solid var(--border)",
  background: "white",
  marginTop: 4,
};

const btnSm: React.CSSProperties = {
  width: "auto",
  padding: "8px 16px",
  borderRadius: "var(--radius-full)",
  fontSize: 13,
};

// useSearchParams needs a Suspense boundary so the rest of the route can prerender
// (node_modules/next/dist/docs/01-app/03-api-reference/04-functions/use-search-params.md).
export default function AiPapersPage() {
  return (
    <Suspense fallback={<div className="loading-screen" style={{ minHeight: "50vh" }}><div className="spinner" /></div>}>
      <AiPapersPageInner />
    </Suspense>
  );
}
