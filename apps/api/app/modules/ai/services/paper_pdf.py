"""Question-paper renderer — clean exam-paper HTML, converted to a real PDF.

AI-generated content is HTML-escaped (math text contains <, >, & etc.).
"""
from __future__ import annotations

import html

from app.db.models.question_paper import QuestionPaper
from app.shared.pdf_renderer import render_pdf

_STYLES = """
  @page { size: A4; margin: 18mm; }
  body { font-family: 'Cambria','Georgia',serif; color:#111; font-size:12.5pt; line-height:1.5; }
  .head { text-align:center; border-bottom:2px solid #111; padding-bottom:8px; margin-bottom:10px; }
  .school { font-size:18pt; font-weight:700; }
  .examttl { font-size:10.5pt; letter-spacing:1px; color:#444; text-transform:uppercase; }
  .metarow { display:flex; justify-content:space-between; font-weight:600; margin-top:6px; }
  .instructions { font-size:10.5pt; color:#333; margin:10px 0; }
  .section-title { font-weight:700; text-align:center; background:#f0f0f0;
                   padding:4px; margin:14px 0 4px; }
  .section-instr { font-style:italic; font-size:10.5pt; color:#555; margin-bottom:6px; }
  .q { display:flex; gap:8px; margin:6px 0; }
  .qno { font-weight:700; } .qtext { flex:1; }
  .qmarks { color:#444; font-weight:600; white-space:nowrap; }
  .opts { list-style:none; padding-left:26px; margin:2px 0;
          display:flex; flex-wrap:wrap; gap:4px 28px; }
  .ans { margin-left:26px; color:#1d4ed8; font-size:10.5pt; }
  table { width:100%; border-collapse:collapse; margin:10px 0 18px; font-size:10pt; }
  th, td { border:1px solid #aaa; padding:5px 6px; text-align:left; vertical-align:top; }
  th { background:#eee; font-weight:700; }
  .summary { display:flex; gap:18px; margin:10px 0; }
  .summary > div { flex:1; }
"""


def _exam_type_label(paper: QuestionPaper) -> str:
    value = getattr(paper, "exam_type", None)
    raw = getattr(value, "value", value) or "unit_test"
    return str(raw).replace("_", " ").title()


def _questions_html(section: dict, include_answers: bool) -> str:
    out = []
    for q in section.get("questions", []):
        number = html.escape(str(q.get("number", "")))
        text = html.escape(str(q.get("text", "")))
        marks = q.get("marks", "")
        out.append(
            f'<div class="q"><span class="qno">{number}.</span>'
            f'<span class="qtext">{text}</span><span class="qmarks">[{marks}]</span></div>'
        )
        opts = q.get("options")
        if opts:
            letters = "abcdefgh"
            items = "".join(
                f"<li>({letters[i]}) {html.escape(str(o))}</li>" for i, o in enumerate(opts)
            )
            out.append(f'<ol class="opts">{items}</ol>')
        if include_answers and q.get("answer_key"):
            out.append(f'<div class="ans"><b>Ans:</b> {html.escape(str(q["answer_key"]))}</div>')
    return "".join(out)


def render_paper_html(
    paper: QuestionPaper, *, school_name: str | None = None, include_answers: bool = False
) -> str:
    body_parts = []
    for section in (paper.sections or []):
        body_parts.append(
            f'<div class="section-title">{html.escape(str(section.get("title", "")))}</div>'
        )
        if section.get("instructions"):
            body_parts.append(
                f'<div class="section-instr">{html.escape(str(section["instructions"]))}</div>'
            )
        body_parts.append(_questions_html(section, include_answers))
    sections_html = "".join(body_parts)

    gi_html = ""
    if paper.general_instructions:
        lines = [ln for ln in str(paper.general_instructions).split("\n") if ln.strip()]
        items = "".join(f"<li>{html.escape(ln)}</li>" for ln in lines)
        gi_html = f'<div class="instructions"><b>General Instructions:</b><ol>{items}</ol></div>'

    title_tag = "Answer Key" if include_answers else "Question Paper"
    school = html.escape(school_name or paper.board)
    return (
        '<!DOCTYPE html><html><head><meta charset="utf-8"><style>'
        + _STYLES
        + "</style></head><body>"
        + f'<div class="head"><div class="school">{school}</div>'
        + f'<div class="examttl">{html.escape(paper.board)} &middot; {title_tag}</div>'
        + f'<div class="metarow"><span>{html.escape(paper.title)}</span>'
        + f'<span>Assessment: {html.escape(_exam_type_label(paper))}</span></div>'
        + f'<div class="metarow"><span>Class: {html.escape(paper.grade)}</span>'
        + f"<span>Subject: {html.escape(paper.subject_name)}</span></div>"
        + f'<div class="metarow"><span>Time: {paper.duration_minutes or ""} min</span>'
        + f"<span>Max Marks: {float(paper.total_marks):g}</span></div></div>"
        + gi_html
        + sections_html
        + "</body></html>"
    )


def generate_paper_pdf(
    paper: QuestionPaper, *, school_name: str | None = None, include_answers: bool = False
) -> tuple[bytes, str]:
    """Return real PDF content and its media type."""
    doc = render_paper_html(paper, school_name=school_name, include_answers=include_answers)
    return render_pdf(doc, document_type="question_paper"), "application/pdf"


def _distribution_rows(values: dict[str, float]) -> str:
    if not values:
        return '<tr><td colspan="2">Not specified</td></tr>'
    return "".join(
        f"<tr><td>{html.escape(label)}</td><td>{marks:g}</td></tr>"
        for label, marks in sorted(values.items(), key=lambda item: item[0].casefold())
    )


def render_blueprint_html(
    paper: QuestionPaper, *, school_name: str | None = None
) -> str:
    """Render the saved paper's actual question-level blueprint (never regenerated by AI)."""
    question_rows: list[str] = []
    chapter_marks: dict[str, float] = {}
    bloom_marks: dict[str, float] = {}
    for section in paper.sections or []:
        section_title = str(section.get("title") or "Section")
        for question in section.get("questions") or []:
            marks = float(question.get("marks") or 0)
            chapter = str(question.get("chapter") or "Not specified")
            bloom = str(question.get("bloom") or "Not specified")
            chapter_marks[chapter] = chapter_marks.get(chapter, 0) + marks
            bloom_marks[bloom] = bloom_marks.get(bloom, 0) + marks
            question_rows.append(
                "<tr>"
                f"<td>{html.escape(section_title)}</td>"
                f"<td>{html.escape(str(question.get('number') or ''))}</td>"
                f"<td>{html.escape(str(question.get('type') or 'short'))}</td>"
                f"<td>{marks:g}</td>"
                f"<td>{html.escape(chapter)}</td>"
                f"<td>{html.escape(bloom)}</td>"
                "</tr>"
            )

    school = html.escape(school_name or paper.board)
    rows = "".join(question_rows) or '<tr><td colspan="6">No questions</td></tr>'
    return (
        '<!DOCTYPE html><html><head><meta charset="utf-8"><style>'
        + _STYLES
        + "</style></head><body>"
        + f'<div class="head"><div class="school">{school}</div>'
        + '<div class="examttl">Question Paper Blueprint</div>'
        + f'<div class="metarow"><span>Class: {html.escape(paper.grade)}</span>'
        + f"<span>Subject: {html.escape(paper.subject_name)}</span></div>"
        + f'<div class="metarow"><span>{html.escape(paper.title)}</span>'
        + f"<span>Assessment: {html.escape(_exam_type_label(paper))}</span></div>"
        + '<div class="metarow"><span>Blueprint</span>'
        + f"<span>Max Marks: {float(paper.total_marks):g}</span></div></div>"
        + '<div class="summary"><div><b>Chapter distribution</b><table>'
        + '<tr><th>Chapter</th><th>Marks</th></tr>'
        + _distribution_rows(chapter_marks)
        + '</table></div><div><b>Objective distribution</b><table>'
        + '<tr><th>Bloom level</th><th>Marks</th></tr>'
        + _distribution_rows(bloom_marks)
        + "</table></div></div>"
        + "<table><tr><th>Section</th><th>Q.</th><th>Type</th><th>Marks</th>"
        + f"<th>Chapter</th><th>Bloom</th></tr>{rows}</table>"
        + "</body></html>"
    )


def generate_blueprint_pdf(
    paper: QuestionPaper, *, school_name: str | None = None
) -> tuple[bytes, str]:
    """Return a PDF snapshot of the paper's persisted blueprint metadata."""
    doc = render_blueprint_html(paper, school_name=school_name)
    return render_pdf(doc, document_type="question_paper_blueprint"), "application/pdf"
