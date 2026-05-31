"""Question-paper renderer — clean exam-paper HTML, converted to PDF via WeasyPrint when available.

Falls back to print-ready HTML (browser Print-to-PDF) in dev, like the fee-receipt renderer.
AI-generated content is HTML-escaped (math text contains <, >, & etc.).
"""
from __future__ import annotations

import html

from app.db.models.question_paper import QuestionPaper

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
"""


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
    """Return (content, media_type). PDF if WeasyPrint is installed, else print-ready HTML."""
    doc = render_paper_html(paper, school_name=school_name, include_answers=include_answers)
    try:
        from weasyprint import HTML

        return HTML(string=doc).write_pdf(), "application/pdf"
    except (ImportError, OSError):
        return doc.encode("utf-8"), "text/html"
