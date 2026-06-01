"""Report-card renderer — clean printable HTML, converted to PDF via WeasyPrint when available.

Falls back to print-ready HTML (browser Print-to-PDF) in dev, like the paper/receipt renderers.
All stored text is HTML-escaped.
"""
from __future__ import annotations

import html

from app.db.models.report_card import ReportCard

_STYLES = """
  @page { size: A4; margin: 16mm; }
  body { font-family: 'Cambria','Georgia',serif; color:#111; font-size:12pt; line-height:1.5; }
  .head { text-align:center; border-bottom:2px solid #111; padding-bottom:8px; margin-bottom:12px; }
  .school { font-size:19pt; font-weight:700; }
  .doc { font-size:10.5pt; letter-spacing:1px; color:#444; text-transform:uppercase;
         margin-top:2px; }
  .meta { display:flex; justify-content:space-between; font-weight:600; margin:12px 0; }
  table { width:100%; border-collapse:collapse; margin:8px 0; }
  th, td { border:1px solid #999; padding:7px 10px; text-align:left; }
  th { background:#f0f0f0; }
  td.num, th.num { text-align:center; width:18%; }
  tr.total td { font-weight:700; background:#fafafa; }
  .summary { display:flex; gap:20px; margin:12px 0; font-weight:600; }
  .summary .box { border:1px solid #999; border-radius:6px; padding:8px 14px; }
  .summary .box span { display:block; font-size:9pt; color:#666; font-weight:400;
                       text-transform:uppercase; letter-spacing:.5px; }
  .remark { border:1px solid #999; border-radius:6px; padding:10px 12px; margin-top:8px; }
  .remark h4 { margin:0 0 4px; font-size:10pt; text-transform:uppercase;
               letter-spacing:.5px; color:#444; }
  .signs { display:flex; justify-content:space-between; margin-top:44px; font-size:10.5pt; }
  .signs div { border-top:1px solid #111; padding-top:4px; width:30%; text-align:center; }
"""


def _rows_html(report: ReportCard) -> str:
    out = []
    for s in (report.subjects or []):
        obtained = s.get("marks_obtained", 0)
        total = s.get("total_marks", 0)
        pct = (obtained / total * 100) if total else 0
        out.append(
            f"<tr><td>{html.escape(str(s.get('subject', '')))}</td>"
            f'<td class="num">{obtained:g}</td>'
            f'<td class="num">{total:g}</td>'
            f'<td class="num">{pct:.0f}%</td></tr>'
        )
    out.append(
        '<tr class="total"><td>Total</td>'
        f'<td class="num">{float(report.total_obtained or 0):g}</td>'
        f'<td class="num">{float(report.total_max or 0):g}</td>'
        f'<td class="num">{float(report.percentage or 0):.0f}%</td></tr>'
    )
    return "".join(out)


def render_report_html(report: ReportCard, *, school_name: str | None = None) -> str:
    school = html.escape(school_name or "School")
    att = (
        f"{float(report.attendance_percentage):g}%"
        if report.attendance_percentage is not None
        else "—"
    )
    remark_html = ""
    if report.ai_remark:
        remark_html = (
            '<div class="remark"><h4>Class Teacher\'s Remark</h4>'
            f"<div>{html.escape(report.ai_remark)}</div></div>"
        )
    return (
        '<!DOCTYPE html><html><head><meta charset="utf-8"><style>'
        + _STYLES
        + "</style></head><body>"
        + f'<div class="head"><div class="school">{school}</div>'
        + f'<div class="doc">{html.escape(report.title)}</div></div>'
        + '<div class="meta">'
        + f"<span>Name: {html.escape(report.student_name)}</span>"
        + f"<span>Class: {html.escape(report.class_name)}</span></div>"
        + '<table><thead><tr><th>Subject</th><th class="num">Marks</th>'
        + '<th class="num">Max</th><th class="num">%</th></tr></thead>'
        + f"<tbody>{_rows_html(report)}</tbody></table>"
        + '<div class="summary">'
        + f'<div class="box"><span>Percentage</span>{float(report.percentage or 0):g}%</div>'
        + f'<div class="box"><span>Grade</span>{html.escape(report.overall_grade or "—")}</div>'
        + f'<div class="box"><span>Attendance</span>{att}</div></div>'
        + remark_html
        + '<div class="signs"><div>Class Teacher</div><div>Principal</div>'
        + "<div>Parent / Guardian</div></div>"
        + "</body></html>"
    )


def generate_report_pdf(
    report: ReportCard, *, school_name: str | None = None
) -> tuple[bytes, str]:
    """Return (content, media_type). PDF if WeasyPrint is installed, else print-ready HTML."""
    doc = render_report_html(report, school_name=school_name)
    try:
        from weasyprint import HTML

        return HTML(string=doc).write_pdf(), "application/pdf"
    except (ImportError, OSError):
        return doc.encode("utf-8"), "text/html"
