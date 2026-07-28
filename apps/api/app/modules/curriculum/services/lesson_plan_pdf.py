"""School lesson plan renderer — HTML template matching the standard document layout."""
from __future__ import annotations

import html
from datetime import date

from app.shared.pdf_renderer import render_pdf

_STYLES = """
  @page { size: A4; margin: 16mm; }
  body {
    font-family: 'Segoe UI', Arial, sans-serif;
    color: #111; font-size: 11pt; line-height: 1.45;
  }
  h1 {
    font-family: 'Times New Roman', Georgia, serif;
    font-size: 22pt; margin: 0 0 6px; letter-spacing: 0.02em;
  }
  h2 { font-family: 'Times New Roman', Georgia, serif; font-size: 12pt; margin: 18px 0 4px; }
  .rule { border-top: 2px solid #111; margin: 6px 0 14px; }
  .rule-thin { border-top: 1px solid #888; margin: 4px 0 10px; }
  .meta-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px 24px; margin-bottom: 8px; }
  .field { display: grid; grid-template-columns: auto 1fr; gap: 6px; align-items: end; }
  .label { font-weight: 700; white-space: nowrap; }
  .value { border-bottom: 1px solid #888; min-height: 18px; padding-bottom: 2px; }
  .overview { display: grid; grid-template-columns: 2fr 1fr; gap: 10px 24px; margin-bottom: 8px; }
  ul { margin: 6px 0 0; padding-left: 18px; }
  li { margin: 2px 0; }
  table { width: 100%; border-collapse: collapse; margin-top: 4px; font-size: 10.5pt; }
  th, td { border: 1px solid #888; padding: 6px 8px; vertical-align: top; text-align: left; }
  th { background: #f3f4f6; font-weight: 700; }
  td.time { width: 56px; white-space: nowrap; }
  td.step { width: 110px; font-weight: 600; }
  .notes-block { margin-top: 14px; white-space: pre-wrap; }
"""


def _fmt_date(value: date | None) -> str:
    if not value:
        return "—"
    return value.strftime("%d %b %Y")


def _list_html(items: list[str]) -> str:
    if not items:
        return "<ul><li>&nbsp;</li><li>&nbsp;</li><li>&nbsp;</li></ul>"
    return "<ul>" + "".join(f"<li>{html.escape(str(item))}</li>" for item in items) + "</ul>"


def _field_html(label: str, value: str) -> str:
    return (
        f"<div class='field'><span class='label'>{html.escape(label)}:</span>"
        f"<span class='value'>{html.escape(value)}</span></div>"
    )


def _segment_notes(segment: dict) -> str:
    notes = str(segment.get("notes") or "").strip()
    if notes:
        return notes
    sources = segment.get("citation_sources") or []
    if sources:
        parts = []
        for source in sources:
            if not isinstance(source, dict):
                continue
            label = " › ".join(
                p for p in (source.get("chapter"), source.get("topic")) if p
            )
            if label:
                parts.append(label)
        if parts:
            return " · ".join(parts)
    return "—"


def render_lesson_plan_html(
    *,
    teacher_name: str,
    subject_name: str,
    class_label: str,
    scheduled_for: date | None,
    topic: str,
    duration_minutes: int,
    learning_objectives: list[str],
    materials: list[str],
    segments: list[dict],
    notes: str | None = None,
) -> str:
    rows = []
    for segment in segments or []:
        duration = int(segment.get("duration_min") or 0)
        activity = html.escape(str(segment.get("activity") or ""))
        description = html.escape(str(segment.get("description") or segment.get("activity") or ""))
        row_notes = html.escape(_segment_notes(segment))
        rows.append(
            f"<tr><td class='time'>{duration} min</td>"
            f"<td class='step'>{activity}</td>"
            f"<td>{description}</td>"
            f"<td>{row_notes}</td></tr>"
        )
    table_body = "".join(rows) or (
        "<tr><td colspan='4'>&nbsp;</td></tr>"
    )

    notes_html = ""
    if notes and notes.strip():
        notes_html = (
            f"<h2>Additional Notes:</h2><div class='rule-thin'></div>"
            f"<div class='notes-block'>{html.escape(notes.strip())}</div>"
        )

    duration_label = f"{duration_minutes} min" if duration_minutes > 0 else "—"

    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'><style>"
        + _STYLES
        + "</style></head><body>"
        + "<h1>SCHOOL LESSON PLAN</h1><div class='rule'></div>"
        + "<div class='meta-grid'>"
        + _field_html("Teacher", teacher_name)
        + _field_html("Subject", subject_name)
        + _field_html("Grade Level", class_label)
        + _field_html("Date", _fmt_date(scheduled_for))
        + "</div>"
        + "<h2>Lesson Overview:</h2><div class='rule-thin'></div>"
        + "<div class='overview'>"
        + _field_html("Topic", topic)
        + _field_html("Duration", duration_label)
        + "</div>"
        + (
            "<div class='field' style='display:block;margin-top:8px;'>"
            "<span class='label'>Objectives:</span>"
        )
        + _list_html(learning_objectives)
        + "</div>"
        + "<h2>Materials Needed:</h2><div class='rule-thin'></div>"
        + _list_html(materials)
        + "<h2>Procedure:</h2><div class='rule-thin'></div>"
        + "<table><thead><tr>"
        + "<th>Time</th><th>Activity/Step</th><th>Description</th><th>Notes/Resources</th>"
        + "</tr></thead><tbody>"
        + table_body
        + "</tbody></table>"
        + notes_html
        + "</body></html>"
    )


def generate_lesson_plan_pdf(**kwargs) -> tuple[bytes, str]:
    """Return real PDF content and its media type."""
    doc = render_lesson_plan_html(**kwargs)
    return render_pdf(doc, document_type="lesson_plan"), "application/pdf"
