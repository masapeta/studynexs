"use client";

import { useEffect, useState } from "react";
import { Check, Clock, NotebookPen, RefreshCw, Sparkles } from "lucide-react";
import { api, getApiErrorMessage } from "@/lib/api";
import { AppSelect } from "@/components/ui/AppSelect";
import { formatClassLabel, sortClasses } from "@/lib/format";

type Segment = { duration_min: number; activity: string };
type Plan = {
  id: string;
  title: string;
  chapter?: string | null;
  topic?: string | null;
  scheduled_for?: string | null;
  segments: Segment[];
  status: string;
  notes?: string | null;
  can_edit?: boolean;
  can_approve?: boolean;
};

const sel: React.CSSProperties = { width: "100%", padding: "8px 12px", borderRadius: "var(--radius-sm)", border: "1px solid var(--border)", background: "white", marginTop: 4 };
const btn: React.CSSProperties = { width: "auto", padding: "8px 18px", borderRadius: "var(--radius-full)", fontSize: 13 };

export default function LessonPlansPage() {
  const [classes, setClasses] = useState<any[]>([]);
  const [subjects, setSubjects] = useState<any[]>([]);
  const [classId, setClassId] = useState("");
  const [subjectId, setSubjectId] = useState("");
  const [topic, setTopic] = useState("");
  const [plan, setPlan] = useState<Plan | null>(null);
  const [busy, setBusy] = useState(false);
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

  async function generate() {
    if (!classId || !subjectId) { setError("Pick a class and subject first."); return; }
    setBusy(true);
    setError("");
    try {
      const res = await api<Plan>("/api/v1/lesson-plans/generate", {
        method: "POST",
        body: JSON.stringify({ class_id: classId, subject_id: subjectId, topic: topic.trim() || null }),
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
    try {
      const res = await api<Plan>(`/api/v1/lesson-plans/${plan.id}/${path}`, { method: "POST" });
      setPlan(res);
    } catch (e) {
      setError(getApiErrorMessage(e, "Action failed"));
    } finally {
      setBusy(false);
    }
  }

  const approved = plan?.status === "approved";

  return (
    <>
      <div className="card bento-glass" style={{ marginBottom: 24, padding: "16px 24px" }}>
        <h1 style={{ fontSize: 20, fontWeight: 700, margin: 0, display: "flex", alignItems: "center", gap: 8 }}>
          <NotebookPen size={20} /> Lesson Plans
        </h1>
        <p style={{ margin: "4px 0 0", color: "var(--text-muted)", fontSize: 13 }}>
          Generate a period plan from a topic (or your class&apos;s weakest topic), edit, and approve.
        </p>
      </div>

      {error && <div className="card" style={{ marginBottom: 16, padding: 12, color: "var(--danger)" }}>{error}</div>}

      <div className="card" style={{ marginBottom: 24, padding: 24, display: "grid", gridTemplateColumns: "1fr 1fr 1.5fr auto", gap: 12, alignItems: "end" }}>
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
          <label className="stat-label">Topic (optional — defaults to weakest)</label>
          <input className="form-input" style={sel} value={topic} placeholder="e.g. Quadratic Equations" onChange={(e) => setTopic(e.target.value)} />
        </div>
        <button className="btn btn-primary" style={btn} onClick={generate} disabled={busy}>
          <Sparkles size={15} style={{ marginRight: 6 }} />{busy ? "Working…" : "Generate"}
        </button>
      </div>

      {plan && (
        <div className="card" style={{ padding: 24 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12, flexWrap: "wrap" }}>
            <div>
              <div style={{ fontWeight: 700, fontSize: 17 }}>{plan.title}</div>
              <div style={{ fontSize: 13, color: "var(--text-muted)", marginTop: 2 }}>
                {plan.chapter ? `${plan.chapter} · ` : ""}{plan.topic}
                {plan.scheduled_for ? ` · ${new Date(plan.scheduled_for).toLocaleDateString("en-IN", { day: "numeric", month: "short" })}` : ""}
              </div>
            </div>
            <span className={`badge ${approved ? "badge-success" : "badge-warning"}`} style={{ textTransform: "capitalize" }}>{plan.status}</span>
          </div>

          <div style={{ marginTop: 16 }}>
            {(plan.segments || []).map((s, i) => (
              <div key={i} style={{ display: "flex", alignItems: "center", gap: 12, padding: "10px 0", borderTop: i ? "1px solid var(--border-light)" : "none" }}>
                <span style={{ display: "inline-flex", alignItems: "center", gap: 4, fontSize: 12, fontWeight: 700, color: "var(--info)", minWidth: 54 }}>
                  <Clock size={13} /> {s.duration_min}m
                </span>
                <span style={{ fontSize: 14 }}>{s.activity}</span>
              </div>
            ))}
          </div>

          {!approved && (
            <div style={{ display: "flex", gap: 10, marginTop: 18, justifyContent: "flex-end" }}>
              <button className="btn btn-ghost" style={btn} onClick={() => act("regenerate")} disabled={busy}>
                <RefreshCw size={15} style={{ marginRight: 6 }} /> Regenerate
              </button>
              {plan.can_approve && (
                <button className="btn btn-primary" style={btn} onClick={() => act("approve")} disabled={busy}>
                  <Check size={15} style={{ marginRight: 6 }} /> Approve
                </button>
              )}
            </div>
          )}
          {!approved && plan.can_approve === false && (
            <div style={{ marginTop: 12, fontSize: 12, color: "var(--text-muted)" }}>
              Your class incharge approves lesson plans.
            </div>
          )}
        </div>
      )}
    </>
  );
}
