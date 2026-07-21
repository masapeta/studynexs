"use client";

import { useMemo, useState } from "react";
import { Save, X } from "lucide-react";
import type { LessonPlanDocumentData, LessonPlanSegment } from "@/components/briefing/LessonPlanDocument";

export type LessonPlanEditable = LessonPlanDocumentData & {
  can_edit?: boolean;
};

type Props = {
  plan: LessonPlanEditable;
  busy?: boolean;
  onSave: (payload: {
    topic: string | null;
    scheduled_for: string | null;
    learning_objectives: string[];
    materials: string[];
    segments: LessonPlanSegment[];
    notes: string | null;
  }) => Promise<void>;
  onCancel: () => void;
};

function listToText(items?: string[]) {
  return (items || []).join("\n");
}

function textToList(value: string) {
  return value
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
}

function toDateInput(value?: string | null) {
  if (!value) return "";
  return value.slice(0, 10);
}

export function LessonPlanEditor({ plan, busy = false, onSave, onCancel }: Props) {
  const [topic, setTopic] = useState(plan.topic || "");
  const [scheduledFor, setScheduledFor] = useState(toDateInput(plan.scheduled_for));
  const [objectivesText, setObjectivesText] = useState(
    listToText(plan.learning_objectives?.length ? plan.learning_objectives : undefined)
  );
  const [materialsText, setMaterialsText] = useState(listToText(plan.materials));
  const [notes, setNotes] = useState(plan.notes || "");
  const [segments, setSegments] = useState<LessonPlanSegment[]>(
    () => (plan.segments || []).map((segment) => ({ ...segment }))
  );

  const durationMinutes = useMemo(
    () => segments.reduce((sum, segment) => sum + (Number(segment.duration_min) || 0), 0),
    [segments]
  );

  function updateSegment(index: number, patch: Partial<LessonPlanSegment>) {
    setSegments((current) =>
      current.map((segment, i) => (i === index ? { ...segment, ...patch } : segment))
    );
  }

  async function handleSave() {
    await onSave({
      topic: topic.trim() || null,
      scheduled_for: scheduledFor || null,
      learning_objectives: textToList(objectivesText),
      materials: textToList(materialsText),
      notes: notes.trim() || null,
      segments: segments.map((segment, index) => ({
        duration_min: Math.max(1, Number(segment.duration_min) || 1),
        activity: segment.activity.trim(),
        description: segment.description?.trim() || null,
        notes: segment.notes?.trim() || null,
        citations: plan.segments[index]?.citations,
        citation_sources: plan.segments[index]?.citation_sources,
      })),
    });
  }

  return (
    <div className="lesson-plan-editor">
      <div className="lesson-plan-editor__toolbar">
        <span className="badge badge-warning">Editing draft</span>
        <div className="lesson-plan-editor__actions">
          <button type="button" className="btn btn-ghost" onClick={onCancel} disabled={busy}>
            <X size={15} style={{ marginRight: 6 }} />
            Cancel
          </button>
          <button type="button" className="btn btn-primary" onClick={handleSave} disabled={busy}>
            <Save size={15} style={{ marginRight: 6 }} />
            {busy ? "Saving…" : "Save changes"}
          </button>
        </div>
      </div>

      <header className="lesson-plan-doc__header">
        <h2 className="lesson-plan-doc__title">School Lesson Plan</h2>
        <div className="lesson-plan-doc__rule" aria-hidden />
      </header>

      <div className="lesson-plan-doc__meta-grid">
        <div className="lesson-plan-doc__meta-row">
          <div className="lesson-plan-doc__field">
            <span className="lesson-plan-doc__label">Teacher:</span>
            <span className="lesson-plan-doc__value">{plan.teacher_name || "—"}</span>
          </div>
          <div className="lesson-plan-doc__field">
            <span className="lesson-plan-doc__label">Subject:</span>
            <span className="lesson-plan-doc__value">{plan.subject_name || "—"}</span>
          </div>
        </div>
        <div className="lesson-plan-doc__meta-row">
          <div className="lesson-plan-doc__field">
            <span className="lesson-plan-doc__label">Grade Level:</span>
            <span className="lesson-plan-doc__value">{plan.class_label || "—"}</span>
          </div>
          <div className="lesson-plan-doc__field lesson-plan-editor__field-input">
            <label className="lesson-plan-doc__label" htmlFor="lesson-plan-date">
              Date:
            </label>
            <input
              id="lesson-plan-date"
              type="date"
              className="form-input lesson-plan-editor__input"
              value={scheduledFor}
              onChange={(e) => setScheduledFor(e.target.value)}
            />
          </div>
        </div>
      </div>

      <section className="lesson-plan-doc__section">
        <h3 className="lesson-plan-doc__section-title">Lesson Overview:</h3>
        <div className="lesson-plan-doc__rule lesson-plan-doc__rule--section" aria-hidden />
        <div className="lesson-plan-doc__overview-grid">
          <div className="lesson-plan-editor__field-input lesson-plan-editor__field-input--wide">
            <label className="lesson-plan-doc__label" htmlFor="lesson-plan-topic">
              Topic:
            </label>
            <input
              id="lesson-plan-topic"
              className="form-input lesson-plan-editor__input"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
            />
          </div>
          <div className="lesson-plan-doc__field">
            <span className="lesson-plan-doc__label">Duration:</span>
            <span className="lesson-plan-doc__value">{durationMinutes > 0 ? `${durationMinutes} min` : "—"}</span>
          </div>
        </div>
        <div className="lesson-plan-editor__field-input lesson-plan-editor__field-input--stack">
          <label className="lesson-plan-doc__label" htmlFor="lesson-plan-objectives">
            Objectives:
          </label>
          <textarea
            id="lesson-plan-objectives"
            className="form-input lesson-plan-editor__textarea"
            rows={4}
            placeholder="One objective per line"
            value={objectivesText}
            onChange={(e) => setObjectivesText(e.target.value)}
          />
        </div>
      </section>

      <section className="lesson-plan-doc__section">
        <h3 className="lesson-plan-doc__section-title">Materials Needed:</h3>
        <div className="lesson-plan-doc__rule lesson-plan-doc__rule--section" aria-hidden />
        <div className="lesson-plan-editor__field-input lesson-plan-editor__field-input--stack">
          <label className="sr-only" htmlFor="lesson-plan-materials">
            Materials needed
          </label>
          <textarea
            id="lesson-plan-materials"
            className="form-input lesson-plan-editor__textarea"
            rows={4}
            placeholder="One material per line"
            value={materialsText}
            onChange={(e) => setMaterialsText(e.target.value)}
          />
        </div>
      </section>

      <section className="lesson-plan-doc__section">
        <h3 className="lesson-plan-doc__section-title">Procedure:</h3>
        <div className="lesson-plan-doc__rule lesson-plan-doc__rule--section" aria-hidden />
        <div className="lesson-plan-doc__table-wrap">
          <table className="lesson-plan-doc__table lesson-plan-editor__table">
            <thead>
              <tr>
                <th scope="col">Time</th>
                <th scope="col">Activity/Step</th>
                <th scope="col">Description</th>
                <th scope="col">Notes/Resources</th>
              </tr>
            </thead>
            <tbody>
              {segments.map((segment, index) => (
                <tr key={index}>
                  <td>
                    <input
                      type="number"
                      min={1}
                      max={120}
                      className="form-input lesson-plan-editor__cell-input"
                      value={segment.duration_min}
                      aria-label={`Duration for step ${index + 1}`}
                      onChange={(e) =>
                        updateSegment(index, { duration_min: Number(e.target.value) || 1 })
                      }
                    />
                    <span className="lesson-plan-editor__unit">min</span>
                  </td>
                  <td>
                    <input
                      className="form-input lesson-plan-editor__cell-input"
                      value={segment.activity}
                      aria-label={`Activity for step ${index + 1}`}
                      onChange={(e) => updateSegment(index, { activity: e.target.value })}
                    />
                  </td>
                  <td>
                    <textarea
                      className="form-input lesson-plan-editor__cell-textarea"
                      rows={2}
                      value={segment.description || ""}
                      aria-label={`Description for step ${index + 1}`}
                      onChange={(e) => updateSegment(index, { description: e.target.value })}
                    />
                  </td>
                  <td>
                    <textarea
                      className="form-input lesson-plan-editor__cell-textarea"
                      rows={2}
                      value={segment.notes || ""}
                      aria-label={`Notes for step ${index + 1}`}
                      onChange={(e) => updateSegment(index, { notes: e.target.value })}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="lesson-plan-doc__section">
        <h3 className="lesson-plan-doc__section-title">Additional Notes:</h3>
        <div className="lesson-plan-doc__rule lesson-plan-doc__rule--section" aria-hidden />
        <textarea
          className="form-input lesson-plan-editor__textarea"
          rows={3}
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Optional notes for the incharge or substitute teacher"
        />
      </section>
    </div>
  );
}
