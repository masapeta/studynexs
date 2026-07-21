"use client";

import { useEffect, useState } from "react";
import { Check, RefreshCw, Sparkles } from "lucide-react";
import { api, fetchProtectedDocumentUrl, getApiErrorMessage } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { AppSelect } from "@/components/ui/AppSelect";
import { PageHeaderCard } from "@/components/layout/PageHeaderCard";
import {
  LessonPlanDocument,
  type LessonPlanDocumentData,
  type LessonPlanSegment,
} from "@/components/briefing/LessonPlanDocument";
import { LessonPlanEditor } from "@/components/teaching/LessonPlanEditor";
import { formatClassLabel, sortClasses } from "@/lib/format";

type Plan = LessonPlanDocumentData & {
  can_edit?: boolean;
  can_approve?: boolean;
};

type ApprovedPack = {
  id: string;
  status: string;
  version: number;
  board: string;
  book_title?: string | null;
};

const btn: React.CSSProperties = { width: "auto", padding: "8px 18px", borderRadius: "var(--radius-full)", fontSize: 13 };

export default function LessonPlansPage() {
  const { user } = useAuth();
  const [classes, setClasses] = useState<any[]>([]);
  const [subjects, setSubjects] = useState<any[]>([]);
  const [classId, setClassId] = useState("");
  const [subjectId, setSubjectId] = useState("");
  const [topic, setTopic] = useState("");
  const [packId, setPackId] = useState("");
  const [approvedPacks, setApprovedPacks] = useState<ApprovedPack[]>([]);
  const [useCopilot, setUseCopilot] = useState(false);
  const [plan, setPlan] = useState<Plan | null>(null);
  const [editing, setEditing] = useState(false);
  const [busy, setBusy] = useState(false);
  const [downloadingPdf, setDownloadingPdf] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api("/api/v1/academic/classes?page_size=100")
      .then((r) => {
        const items = sortClasses<any>(r.items || r.data || []);
        setClasses(items);
        if (items[0]) setClassId(items[0].id);
      })
      .catch(() => {});
    api("/api/v1/lesson-plans/next")
      .then((r) => setPlan(r.data || null))
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!classId) return;
    api(`/api/v1/academic/subjects?class_id=${classId}`)
      .then((r) => {
        const items = r.items || r.data || (Array.isArray(r) ? r : []);
        setSubjects(items);
        setSubjectId(items[0]?.id || "");
      })
      .catch(() => {});
  }, [classId]);

  useEffect(() => {
    if (!classId || !subjectId) {
      setApprovedPacks([]);
      setPackId("");
      return;
    }
    api(`/api/v1/curriculum/packs?class_id=${classId}&subject_id=${subjectId}`)
      .then((r) => {
        const approved = (r.data || []).filter((p: ApprovedPack) => p.status === "approved");
        setApprovedPacks(approved);
        setPackId(approved[0]?.id || "");
      })
      .catch(() => {
        setApprovedPacks([]);
        setPackId("");
      });
  }, [classId, subjectId]);

  async function generate() {
    if (!classId || !subjectId) {
      setError("Pick a class and subject first.");
      return;
    }
    if (useCopilot && !packId) {
      setError("Select an approved curriculum pack for Teacher Copilot generation.");
      return;
    }
    setBusy(true);
    setError("");
    setEditing(false);
    try {
      const body: Record<string, unknown> = {
        class_id: classId,
        subject_id: subjectId,
        topic: topic.trim() || null,
        generation_mode: useCopilot ? "copilot" : "template",
      };
      if (packId) body.pack_id = packId;
      const res = await api<Plan>("/api/v1/lesson-plans/generate", {
        method: "POST",
        body: JSON.stringify(body),
      });
      setPlan(res);
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to generate lesson plan"));
    } finally {
      setBusy(false);
    }
  }

  async function act(path: string) {
    if (!plan) return;
    setBusy(true);
    setError("");
    setEditing(false);
    try {
      const res = await api<Plan>(`/api/v1/lesson-plans/${plan.id}/${path}`, { method: "POST" });
      setPlan(res);
    } catch (e) {
      setError(getApiErrorMessage(e, "Action failed"));
    } finally {
      setBusy(false);
    }
  }

  async function savePlan(payload: {
    topic: string | null;
    scheduled_for: string | null;
    learning_objectives: string[];
    materials: string[];
    segments: LessonPlanSegment[];
    notes: string | null;
  }) {
    if (!plan) return;
    setBusy(true);
    setError("");
    try {
      const res = await api<Plan>(`/api/v1/lesson-plans/${plan.id}`, {
        method: "PUT",
        body: JSON.stringify(payload),
      });
      setPlan(res);
      setEditing(false);
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to save lesson plan"));
    } finally {
      setBusy(false);
    }
  }

  async function downloadPdf() {
    if (!plan) return;
    setDownloadingPdf(true);
    setError("");
    try {
      const url = await fetchProtectedDocumentUrl(`/api/v1/lesson-plans/${plan.id}/pdf`);
      window.open(url, "_blank", "noopener,noreferrer");
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to download lesson plan PDF"));
    } finally {
      setDownloadingPdf(false);
    }
  }

  const approved = plan?.status === "approved";
  const packOptions = approvedPacks.map((p) => ({
    value: p.id,
    label: `v${p.version} · ${p.book_title || "Approved pack"}`,
  }));

  const selectedClass = classes.find((c) => c.id === classId);
  const selectedSubject = subjects.find((s) => s.id === subjectId);
  const planWithLabels = plan
    ? {
        ...plan,
        teacher_name: plan.teacher_name || user?.full_name || null,
        class_label:
          plan.class_label ||
          (selectedClass ? formatClassLabel(selectedClass.grade, selectedClass.section) : null),
        subject_name: plan.subject_name || selectedSubject?.name || null,
      }
    : null;

  const canEditDraft = Boolean(planWithLabels?.can_edit && planWithLabels.status === "draft");

  return (
    <>
      <PageHeaderCard
        title="Lesson Plans"
        subtitle="Generate a standard school lesson plan, edit inline, then print or export to PDF."
      />

      {error && <div className="card sn-inline-alert sn-inline-alert--error">{error}</div>}

      <div className="card sn-content-card sn-form-row sn-form-row--lesson">
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
            options={subjects.map((s) => ({ value: s.id, label: s.name }))}
          />
        </div>
        <div>
          <label className="stat-label">Approved curriculum pack</label>
          <AppSelect
            variant="field"
            value={packId}
            onChange={setPackId}
            aria-label="Curriculum pack"
            placeholder={packOptions.length ? "Select pack…" : "No approved pack — ungrounded"}
            options={packOptions.length ? packOptions : [{ value: "", label: "No approved pack" }]}
          />
        </div>
        <div>
          <label className="stat-label">Topic (optional)</label>
          <input className="form-input sn-inline-field" value={topic} placeholder="e.g. Linear Equations" onChange={(e) => setTopic(e.target.value)} />
        </div>
        <div>
          <label className="stat-label">Generation mode</label>
          <AppSelect
            variant="field"
            value={useCopilot ? "copilot" : "template"}
            onChange={(v) => setUseCopilot(v === "copilot")}
            aria-label="Generation mode"
            options={[
              { value: "template", label: "Template + curriculum grounding" },
              { value: "copilot", label: "Teacher Copilot (AI credits)" },
            ]}
          />
        </div>
        <button className="btn btn-primary" style={btn} onClick={generate} disabled={busy}>
          <Sparkles size={15} style={{ marginRight: 6 }} />{busy ? "Working…" : "Generate"}
        </button>
      </div>

      {planWithLabels && (
        <div className="card" style={{ padding: 24 }}>
          {editing && canEditDraft ? (
            <LessonPlanEditor
              plan={planWithLabels}
              busy={busy}
              onSave={savePlan}
              onCancel={() => setEditing(false)}
            />
          ) : (
            <LessonPlanDocument
              plan={planWithLabels}
              teacherFallback={user?.full_name}
              canEdit={canEditDraft}
              onEdit={() => setEditing(true)}
              onDownloadPdf={downloadPdf}
              downloadingPdf={downloadingPdf}
            />
          )}

          {!approved && !editing && (
            <div style={{ display: "flex", gap: 10, marginTop: 18, justifyContent: "flex-end" }}>
              <button className="btn btn-ghost" style={btn} onClick={() => act("regenerate")} disabled={busy}>
                <RefreshCw size={15} style={{ marginRight: 6 }} /> Regenerate
              </button>
              {planWithLabels.can_approve && (
                <button className="btn btn-primary" style={btn} onClick={() => act("approve")} disabled={busy}>
                  <Check size={15} style={{ marginRight: 6 }} /> Approve
                </button>
              )}
            </div>
          )}
          {!approved && !editing && planWithLabels.can_approve === false && (
            <div style={{ marginTop: 12, fontSize: 12, color: "var(--text-muted)" }}>
              Your class incharge approves lesson plans.
            </div>
          )}
        </div>
      )}
    </>
  );
}
