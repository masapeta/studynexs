"use client";

import { Download, Pencil, Printer } from "lucide-react";
import { CurriculumGroundingBadge } from "@/components/curriculum/CurriculumGroundingBadge";

export type LessonPlanSegment = {
  duration_min: number;
  activity: string;
  description?: string | null;
  notes?: string | null;
  citations?: number[] | null;
  citation_sources?: { chapter?: string; topic?: string }[];
};

export type LessonPlanDocumentData = {
  id: string;
  title: string;
  chapter?: string | null;
  topic?: string | null;
  scheduled_for?: string | null;
  segments: LessonPlanSegment[];
  learning_objectives?: string[];
  materials?: string[];
  duration_minutes?: number;
  teacher_name?: string | null;
  class_label?: string | null;
  subject_name?: string | null;
  status: string;
  notes?: string | null;
  pack_id?: string | null;
  pack_status?: string | null;
  pack_version?: number | null;
  grounded?: boolean;
  grounded_at?: string | null;
  ai_model?: string | null;
};

type Props = {
  plan: LessonPlanDocumentData;
  teacherFallback?: string;
  showActions?: boolean;
  canEdit?: boolean;
  onEdit?: () => void;
  onPrint?: () => void;
  onDownloadPdf?: () => void;
  downloadingPdf?: boolean;
};

function formatDate(value?: string | null) {
  if (!value) return "—";
  return new Date(value).toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

function formatDuration(total?: number) {
  if (!total || total <= 0) return "—";
  return `${total} min`;
}

export function LessonPlanDocument({
  plan,
  teacherFallback,
  showActions = true,
  canEdit = false,
  onEdit,
  onPrint,
  onDownloadPdf,
  downloadingPdf = false,
}: Props) {
  const teacher = plan.teacher_name || teacherFallback || "—";
  const subject = plan.subject_name || "—";
  const grade = plan.class_label || "—";
  const topic = plan.topic || plan.title;
  const objectives = plan.learning_objectives?.length
    ? plan.learning_objectives
    : plan.notes?.includes("Learning objectives:")
      ? plan.notes
          .split("Learning objectives:")[1]
          ?.split("\n")
          .map((line) => line.replace(/^[•\-\s]+/, "").trim())
          .filter(Boolean) ?? []
      : [];
  const materials = plan.materials?.length ? plan.materials : [];

  function handlePrint() {
    if (onPrint) {
      onPrint();
      return;
    }
    window.print();
  }

  return (
    <article className="lesson-plan-doc" aria-label="School lesson plan">
      {showActions && (
        <div className="lesson-plan-doc__toolbar no-print">
          <span className={`badge ${plan.status === "approved" ? "badge-success" : "badge-warning"}`}>
            {plan.status}
          </span>
          <div className="lesson-plan-doc__toolbar-actions">
            {canEdit && onEdit ? (
              <button type="button" className="btn btn-ghost" onClick={onEdit}>
                <Pencil size={15} style={{ marginRight: 6 }} />
                Edit
              </button>
            ) : null}
            {onDownloadPdf ? (
              <button
                type="button"
                className="btn btn-ghost"
                onClick={onDownloadPdf}
                disabled={downloadingPdf}
              >
                <Download size={15} style={{ marginRight: 6 }} />
                {downloadingPdf ? "Preparing…" : "Download PDF"}
              </button>
            ) : null}
            <button type="button" className="btn btn-ghost" onClick={handlePrint}>
              <Printer size={15} style={{ marginRight: 6 }} />
              Print
            </button>
          </div>
        </div>
      )}

      <header className="lesson-plan-doc__header">
        <h2 className="lesson-plan-doc__title">School Lesson Plan</h2>
        <div className="lesson-plan-doc__rule" aria-hidden />
      </header>

      <div className="lesson-plan-doc__meta-grid">
        <div className="lesson-plan-doc__meta-row">
          <div className="lesson-plan-doc__field">
            <span className="lesson-plan-doc__label">Teacher:</span>
            <span className="lesson-plan-doc__value">{teacher}</span>
          </div>
          <div className="lesson-plan-doc__field">
            <span className="lesson-plan-doc__label">Subject:</span>
            <span className="lesson-plan-doc__value">{subject}</span>
          </div>
        </div>
        <div className="lesson-plan-doc__meta-row">
          <div className="lesson-plan-doc__field">
            <span className="lesson-plan-doc__label">Grade Level:</span>
            <span className="lesson-plan-doc__value">{grade}</span>
          </div>
          <div className="lesson-plan-doc__field">
            <span className="lesson-plan-doc__label">Date:</span>
            <span className="lesson-plan-doc__value">{formatDate(plan.scheduled_for)}</span>
          </div>
        </div>
      </div>

      <section className="lesson-plan-doc__section">
        <h3 className="lesson-plan-doc__section-title">Lesson Overview:</h3>
        <div className="lesson-plan-doc__rule lesson-plan-doc__rule--section" aria-hidden />
        <div className="lesson-plan-doc__overview-grid">
          <div className="lesson-plan-doc__field lesson-plan-doc__field--wide">
            <span className="lesson-plan-doc__label">Topic:</span>
            <span className="lesson-plan-doc__value">{topic}</span>
          </div>
          <div className="lesson-plan-doc__field">
            <span className="lesson-plan-doc__label">Duration:</span>
            <span className="lesson-plan-doc__value">{formatDuration(plan.duration_minutes)}</span>
          </div>
        </div>
        <div className="lesson-plan-doc__block">
          <span className="lesson-plan-doc__label">Objectives:</span>
          {objectives.length ? (
            <ul className="lesson-plan-doc__list">
              {objectives.map((item, index) => (
                <li key={index}>{item}</li>
              ))}
            </ul>
          ) : (
            <div className="lesson-plan-doc__lines" aria-hidden>
              <span />
              <span />
              <span />
            </div>
          )}
        </div>
      </section>

      <section className="lesson-plan-doc__section">
        <h3 className="lesson-plan-doc__section-title">Materials Needed:</h3>
        <div className="lesson-plan-doc__rule lesson-plan-doc__rule--section" aria-hidden />
        {materials.length ? (
          <ul className="lesson-plan-doc__list">
            {materials.map((item, index) => (
              <li key={index}>{item}</li>
            ))}
          </ul>
        ) : (
          <div className="lesson-plan-doc__lines" aria-hidden>
            <span />
            <span />
            <span />
          </div>
        )}
      </section>

      <section className="lesson-plan-doc__section">
        <h3 className="lesson-plan-doc__section-title">Procedure:</h3>
        <div className="lesson-plan-doc__rule lesson-plan-doc__rule--section" aria-hidden />
        <div className="lesson-plan-doc__table-wrap">
          <table className="lesson-plan-doc__table">
            <thead>
              <tr>
                <th scope="col">Time</th>
                <th scope="col">Activity/Step</th>
                <th scope="col">Description</th>
                <th scope="col">Notes/Resources</th>
              </tr>
            </thead>
            <tbody>
              {(plan.segments || []).map((segment, index) => (
                <tr key={index}>
                  <td>{segment.duration_min} min</td>
                  <td>{segment.activity}</td>
                  <td>{segment.description || segment.activity}</td>
                  <td>
                    {segment.notes ||
                      (segment.citation_sources?.length
                        ? segment.citation_sources
                            .map((source) =>
                              [source.chapter, source.topic].filter(Boolean).join(" › ")
                            )
                            .join(" · ")
                        : "—")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {plan.grounded && (
        <div className="lesson-plan-doc__provenance no-print">
          <CurriculumGroundingBadge
            packId={plan.pack_id}
            packStatus={plan.pack_status}
            packVersion={plan.pack_version}
            grounded={plan.grounded}
            groundedAt={plan.grounded_at}
          />
        </div>
      )}

      {plan.notes && !plan.notes.includes("Learning objectives:") && (
        <section className="lesson-plan-doc__section">
          <h3 className="lesson-plan-doc__section-title">Additional Notes:</h3>
          <div className="lesson-plan-doc__rule lesson-plan-doc__rule--section" aria-hidden />
          <p className="lesson-plan-doc__notes">{plan.notes}</p>
        </section>
      )}
    </article>
  );
}
