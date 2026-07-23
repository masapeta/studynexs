"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Sparkles, ArrowRight } from "lucide-react";
import { api, getApiErrorMessage } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { AppSelect } from "@/components/ui/AppSelect";
import { PageHeaderCard } from "@/components/layout/PageHeaderCard";
import { AcademicIntelligenceBanner } from "@/components/curriculum/AcademicIntelligenceBanner";
import { OnboardingReviewPanel, type PackDetail } from "@/components/curriculum/OnboardingReviewPanel";
import { formatClassLabel, sortClasses } from "@/lib/format";
import { TEACHING } from "@/lib/dashboard-routes";

type AcademicYear = { id: string; name: string; is_active?: boolean };
type ClassRow = { id: string; grade: string; section: string };
type SubjectRow = { id: string; name: string };
type TeachingAssignment = { class_id: string; subject_id: string };

const EMPTY_IDS: string[] = [];
const EMPTY_TEACHING_ASSIGNMENTS: TeachingAssignment[] = [];

const inputStyle: React.CSSProperties = {
  width: "100%",
  padding: "8px 12px",
  fontSize: 13,
  borderRadius: 6,
  border: "1px solid var(--border-subtle)",
};

const btn: React.CSSProperties = {
  width: "auto",
  padding: "10px 20px",
  borderRadius: "var(--radius-full)",
  fontSize: 13,
};

function curriculumBuilderHref(classId: string, subjectId: string, packId: string) {
  const q = new URLSearchParams({
    class_id: classId,
    subject_id: subjectId,
    pack_id: packId,
  });
  return `${TEACHING.curriculum}?${q.toString()}`;
}

export default function CurriculumOnboardingPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { permissions, user, loading: authLoading } = useAuth();
  const canEditDraft = Boolean(permissions?.can_edit_curriculum_draft);
  const canApproveCurriculum = Boolean(permissions?.can_approve_curriculum);
  const isAdmin = Boolean(permissions?.is_admin);
  const inchargeClassIds = permissions?.incharge_class_ids ?? EMPTY_IDS;
  const teachingClassIds = permissions?.teaching_class_ids ?? EMPTY_IDS;
  const teachingAssignments = permissions?.teaching_assignments ?? EMPTY_TEACHING_ASSIGNMENTS;
  const requestedPackId = searchParams.get("pack_id");
  const requestedStep = searchParams.get("step");
  const [step, setStep] = useState(() =>
    requestedStep === "3" || requestedStep === "4" ? Number(requestedStep) : 1
  );
  const [classes, setClasses] = useState<ClassRow[]>([]);
  const [subjects, setSubjects] = useState<SubjectRow[]>([]);
  const [years, setYears] = useState<AcademicYear[]>([]);
  const [classId, setClassId] = useState("");
  const [subjectId, setSubjectId] = useState("");
  const [yearId, setYearId] = useState("");
  const [board, setBoard] = useState("SSC");
  const [bookTitle, setBookTitle] = useState("");
  const [publisher, setPublisher] = useState("");
  const [edition, setEdition] = useState("");
  const [inputType, setInputType] = useState("chapter_list");
  const [curriculumText, setCurriculumText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [packId, setPackId] = useState<string | null>(requestedPackId);
  const [proposalNote, setProposalNote] = useState("");
  const [reviewDetail, setReviewDetail] = useState<PackDetail | null>(null);
  const [canApprovePack, setCanApprovePack] = useState(false);

  const selectableClasses = useMemo(() => {
    if (isAdmin) return classes;
    const allowed = new Set([...inchargeClassIds, ...teachingClassIds]);
    if (allowed.size === 0) return [];
    return classes.filter((c) => allowed.has(c.id));
  }, [classes, inchargeClassIds, teachingClassIds, isAdmin]);

  const selectedClassId =
    selectableClasses.find((item) => item.id === classId)?.id || selectableClasses[0]?.id || "";

  const selectableSubjects = useMemo(() => {
    if (isAdmin || inchargeClassIds.includes(selectedClassId)) return subjects;
    const assignedSubjectIds = new Set(
      teachingAssignments
        .filter((assignment) => assignment.class_id === selectedClassId)
        .map((assignment) => assignment.subject_id)
    );
    return subjects.filter((subject) => assignedSubjectIds.has(subject.id));
  }, [inchargeClassIds, isAdmin, selectedClassId, subjects, teachingAssignments]);

  const selectedSubjectId =
    selectableSubjects.find((item) => item.id === subjectId)?.id || selectableSubjects[0]?.id || "";

  const contextLabel = useMemo(() => {
    const cls = classes.find((c) => c.id === selectedClassId);
    const sub = subjects.find((s) => s.id === selectedSubjectId);
    if (!cls || !sub) return "";
    return `${formatClassLabel(cls.grade, cls.section)} · ${sub.name}`;
  }, [classes, selectedClassId, selectedSubjectId, subjects]);

  const canApproveThisPack = Boolean(
    reviewDetail &&
      canApproveCurriculum &&
      (isAdmin || inchargeClassIds.includes(reviewDetail.class_id)) &&
      (!reviewDetail.created_by || !user?.id || reviewDetail.created_by !== user.id || isAdmin)
  );

  const canEditThisPack = Boolean(
    reviewDetail &&
      (
      isAdmin ||
      inchargeClassIds.includes(reviewDetail.class_id) ||
      teachingAssignments.some(
        (assignment) =>
          assignment.class_id === reviewDetail.class_id &&
          assignment.subject_id === reviewDetail.subject_id
      )
      )
  );

  const handleStructureChange = useCallback((detail: PackDetail) => {
    setReviewDetail(detail);
    setClassId(detail.class_id);
    setSubjectId(detail.subject_id);
  }, []);

  useEffect(() => {
    api("/api/v1/academic/classes?page_size=100")
      .then((r) => {
        const items = sortClasses<ClassRow>(r.items || r.data || []);
        setClasses(items);
      })
      .catch(() => {});
    api("/api/v1/school/academic-years")
      .then((r) => {
        const items = r.data || r.items || [];
        setYears(items);
        const active = items.find((y: AcademicYear) => y.is_active) || items[0];
        if (active) setYearId(active.id);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!selectedClassId) return;
    api(`/api/v1/academic/subjects?class_id=${selectedClassId}`)
      .then((r) => {
        const items = (r.items || r.data || []) as SubjectRow[];
        setSubjects(items);
      })
      .catch(() => {});
  }, [selectedClassId]);

  async function proposeDraft() {
    if (!canEditDraft) {
      setError("You need a subject assignment or class incharge role to create curriculum drafts.");
      return;
    }
    if (!selectedClassId || !selectedSubjectId || !yearId) {
      setError("Select class, subject, and academic year.");
      return;
    }
    if (!curriculumText.trim()) {
      setError("Paste a chapter list, syllabus outline, or table of contents.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const r = await api<{
        data: {
          pack: { id: string };
          chapters_proposed: number;
          topics_proposed: number;
          low_confidence_notes: string[];
        };
      }>("/api/v1/curriculum/onboarding/propose", {
        method: "POST",
        body: JSON.stringify({
          class_id: selectedClassId,
          subject_id: selectedSubjectId,
          academic_year_id: yearId,
          board,
          book_title: bookTitle || undefined,
          publisher: publisher || undefined,
          edition: edition || undefined,
          input_type: inputType,
          curriculum_text: curriculumText,
        }),
      });
      setPackId(r.data.pack.id);
      setProposalNote(
        `AI proposed ${r.data.chapters_proposed} chapter(s) and ${r.data.topics_proposed} topic(s) for ${contextLabel}.` +
          (r.data.low_confidence_notes?.length
            ? ` Notes: ${r.data.low_confidence_notes.join("; ")}`
            : "")
      );
      setStep(3);
    } catch (e) {
      setError(getApiErrorMessage(e, "Could not generate draft pack."));
    } finally {
      setBusy(false);
    }
  }

  async function approvePack() {
    if (!packId || !canApproveThisPack) return;
    setBusy(true);
    setError("");
    try {
      await api(`/api/v1/curriculum/packs/${packId}/approve`, { method: "POST" });
      setStep(4);
    } catch (e) {
      setError(getApiErrorMessage(e, "Approval failed — add topics before approving."));
    } finally {
      setBusy(false);
    }
  }

  if (authLoading) {
    return (
      <div className="sn-workspace sn-workspace--primary" style={{ maxWidth: 720, margin: "0 auto" }}>
        <PageHeaderCard title="Academic Onboarding" subtitle="Loading your session…" />
      </div>
    );
  }

  if (!canEditDraft) {
    return (
      <div className="sn-workspace sn-workspace--primary" style={{ maxWidth: 720, margin: "0 auto" }}>
        <PageHeaderCard
          title="Academic Onboarding"
          subtitle="Curriculum onboarding requires a subject assignment, class incharge role, or admin access."
        />
        <p style={{ fontSize: 13, color: "var(--text-secondary)" }}>
          Mapped subject teachers can draft curriculum for their class and subject. Class incharges and principals review and approve before packs become institutional memory.
        </p>
        <Link href={TEACHING.curriculum} className="sn-btn sn-btn--ghost" style={btn}>
          View curriculum packs
        </Link>
      </div>
    );
  }

  return (
    <div className="sn-workspace sn-workspace--primary" style={{ maxWidth: 880, margin: "0 auto" }}>
      <PageHeaderCard
        title="Academic Onboarding"
        subtitle="Subject teachers build the curriculum; class incharges and administrators approve it."
      />

      <div style={{ display: "flex", gap: 8, marginBottom: 20, flexWrap: "wrap" }}>
        {[1, 2, 3, 4].map((n) => (
          <span
            key={n}
            style={{
              fontSize: 12,
              padding: "4px 12px",
              borderRadius: "var(--radius-full)",
              background: step >= n ? "var(--accent)" : "var(--sn-glass-c)",
              color: step >= n ? "#fff" : "var(--text-muted)",
            }}
          >
            {n === 1 ? "School context" : n === 2 ? "Curriculum input" : n === 3 ? "Review draft" : "Approve"}
          </span>
        ))}
      </div>

      {error ? (
        <p role="alert" style={{ color: "var(--danger)", fontSize: 13, marginBottom: 12 }}>
          {error}
        </p>
      ) : null}

      {step === 1 ? (
        <section className="sn-workspace-zone" style={{ display: "grid", gap: 14 }}>
          <h2 style={{ fontSize: 15, margin: 0 }}>Board, class, and textbook</h2>
          <label>
            Class
            <AppSelect
              aria-label="Class"
              variant="field"
              value={selectedClassId}
              onChange={setClassId}
              options={selectableClasses.map((c) => ({
                value: c.id,
                label: formatClassLabel(c.grade, c.section),
              }))}
            />
          </label>
          <label>
            Subject
            <AppSelect
              aria-label="Subject"
              variant="field"
              value={selectedSubjectId}
              onChange={setSubjectId}
              options={selectableSubjects.map((s) => ({ value: s.id, label: s.name }))}
            />
          </label>
          {selectedClassId && selectableSubjects.length === 0 ? (
            <p role="status" style={{ margin: 0, fontSize: 13, color: "var(--text-secondary)" }}>
              You are not assigned to a subject in this class. Choose one of your assigned classes.
            </p>
          ) : null}
          <label>
            Academic year
            <AppSelect
              aria-label="Academic year"
              variant="field"
              value={yearId}
              onChange={setYearId}
              options={years.map((y) => ({ value: y.id, label: y.name }))}
            />
          </label>
          <label>
            Board
            <input style={inputStyle} value={board} onChange={(e) => setBoard(e.target.value)} />
          </label>
          <label>
            Textbook title
            <input style={inputStyle} value={bookTitle} onChange={(e) => setBookTitle(e.target.value)} placeholder="e.g. Mathematics Part I" />
          </label>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <label>
              Publisher
              <input style={inputStyle} value={publisher} onChange={(e) => setPublisher(e.target.value)} />
            </label>
            <label>
              Edition
              <input style={inputStyle} value={edition} onChange={(e) => setEdition(e.target.value)} />
            </label>
          </div>
          <button
            type="button"
            className="sn-btn sn-btn--primary"
            style={btn}
            onClick={() => setStep(2)}
            disabled={!selectedClassId || !selectedSubjectId}
          >
            Continue <ArrowRight size={14} style={{ marginLeft: 6 }} />
          </button>
        </section>
      ) : null}

      {step === 2 ? (
        <section className="sn-workspace-zone" style={{ display: "grid", gap: 14 }}>
          <h2 style={{ fontSize: 15, margin: 0 }}>Curriculum input for {contextLabel || "selected class"}</h2>
          <p style={{ fontSize: 13, color: "var(--text-secondary)", margin: 0 }}>
            Paste a chapter list, syllabus outline, or table of contents. StudyNexs stores structured metadata only — not copyrighted textbook text. File upload is coming later; paste text for now.
          </p>
          <label>
            Input type
            <AppSelect
              aria-label="Input type"
              variant="field"
              value={inputType}
              onChange={setInputType}
              options={[
                { value: "chapter_list", label: "Chapter list" },
                { value: "syllabus", label: "Syllabus outline" },
                { value: "toc", label: "Table of contents" },
                { value: "free_text", label: "Free text" },
              ]}
            />
          </label>
          <label>
            Curriculum text
            <textarea
              style={{ ...inputStyle, minHeight: 200, fontFamily: "inherit" }}
              value={curriculumText}
              onChange={(e) => setCurriculumText(e.target.value)}
            />
          </label>
          <div style={{ display: "flex", gap: 10 }}>
            <button type="button" className="sn-btn sn-btn--ghost" style={btn} onClick={() => setStep(1)}>
              Back
            </button>
            <button
              type="button"
              className="sn-btn sn-btn--primary"
              style={btn}
              disabled={busy}
              onClick={proposeDraft}
            >
              <Sparkles size={14} style={{ marginRight: 6 }} />
              {busy ? "Analysing…" : "Generate draft pack"}
            </button>
          </div>
        </section>
      ) : null}

      {step >= 3 && packId ? (
        <section className="sn-workspace-zone" style={{ display: "grid", gap: 14 }}>
          <h2 style={{ fontSize: 15, margin: 0 }}>Review and approve — {contextLabel}</h2>
          {proposalNote ? (
            <p style={{ fontSize: 13, color: "var(--text-secondary)", margin: 0 }}>{proposalNote}</p>
          ) : null}
          <AcademicIntelligenceBanner
            packId={packId}
            canRetry={canEditThisPack}
            onReadyChange={(ready) => setCanApprovePack(ready)}
          />
          <OnboardingReviewPanel
            packId={packId}
            editable={canEditThisPack}
            onStructureChange={handleStructureChange}
          />
          {canEditThisPack ? (
            <p style={{ fontSize: 13, margin: 0 }}>
              Open the full curriculum builder for chapter-level edits while keeping this class and pack selected.
            </p>
          ) : null}
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            {canEditThisPack ? (
              <Link
                href={curriculumBuilderHref(selectedClassId, selectedSubjectId, packId)}
                className="sn-btn sn-btn--ghost"
                style={btn}
              >
                Edit in curriculum builder
              </Link>
            ) : null}
            {step === 3 ? (
              <>
                <button type="button" className="sn-btn sn-btn--ghost" style={btn} onClick={() => setStep(2)}>
                  Back
                </button>
                {canApproveThisPack ? (
                  <button
                    type="button"
                    className="sn-btn sn-btn--primary"
                    style={btn}
                    disabled={
                      busy ||
                      !(reviewDetail?.chapters || []).some((ch) => (ch.topics || []).length > 0)
                    }
                    onClick={approvePack}
                  >
                    {busy ? "Approving…" : "Approve curriculum pack"}
                  </button>
                ) : (
                  <p role="status" style={{ margin: 0, fontSize: 13, color: "var(--text-secondary)" }}>
                    This draft is ready for review. Its class incharge or a school administrator can approve it.
                  </p>
                )}
              </>
            ) : (
              <button
                type="button"
                className="sn-btn sn-btn--primary"
                style={btn}
                disabled={!canApprovePack}
                onClick={() => router.push(TEACHING.aiPapers)}
              >
                Use in question papers
              </button>
            )}
          </div>
        </section>
      ) : null}

      {step === 4 && packId ? (
        <section className="sn-workspace-zone" style={{ marginTop: 16, display: "grid", gap: 12 }}>
          <AcademicIntelligenceBanner packId={packId} canRetry={canEditThisPack} />
          <p style={{ fontSize: 13, color: "var(--text-secondary)", margin: 0 }}>
            Lesson plans and question papers on the teaching hub now use this approved pack when you select it for {contextLabel}.
          </p>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <Link href={TEACHING.lessonPlans} className="sn-btn sn-btn--ghost" style={btn}>
              Lesson plans
            </Link>
            <Link href={TEACHING.aiPapers} className="sn-btn sn-btn--ghost" style={btn}>
              Question papers
            </Link>
          </div>
        </section>
      ) : null}
    </div>
  );
}
