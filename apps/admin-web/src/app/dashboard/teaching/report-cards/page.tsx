"use client";

import { useEffect, useRef, useState } from "react";
import { Award, CalendarDays, Clock, Save, Check, Printer, Sparkles } from "lucide-react";
import { api, fetchProtectedDocumentUrl, getApiErrorMessage } from "@/lib/api";
import { DocumentPreviewModal } from "@/components/DocumentPreviewModal";
import { AppSelect } from "@/components/ui/AppSelect";
import { PageHeaderCard } from "@/components/layout/PageHeaderCard";
import { formatClassLabel } from "@/lib/format";
import { AI_INPUT, clampText } from "@/lib/ai-input-limits";

type SubjectRow = { subject: string; marks_obtained: number; total_marks: number };
type Report = {
  id: string;
  student_id: string;
  title: string;
  student_name: string;
  class_name: string;
  subjects: SubjectRow[];
  not_assessed?: string[];
  total_obtained: number;
  total_max: number;
  percentage: number;
  overall_grade?: string | null;
  attendance_percentage?: number | null;
  ai_remark?: string | null;
  status: string;
  ai_model?: string | null;
};

export default function ReportCardsPage() {
  const [classes, setClasses] = useState<any[]>([]);
  const [classId, setClassId] = useState("");
  const [students, setStudents] = useState<any[]>([]);
  const [reports, setReports] = useState<Report[]>([]);
  const [title, setTitle] = useState("Term Report Card");

  const [generatingId, setGeneratingId] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [report, setReport] = useState<Report | null>(null);
  const [usage, setUsage] = useState<any>(null);
  const [credits, setCredits] = useState<{
    user_credits_remaining?: number | null;
    credits_remaining?: number;
    purpose_costs?: { report_card?: number };
  } | null>(null);
  const [docPreview, setDocPreview] = useState<{ url: string; title: string } | null>(null);
  const [openingDoc, setOpeningDoc] = useState(false);
  const openDocRef = useRef(false);

  useEffect(() => {
    api("/api/v1/academic/classes?page_size=100")
      .then((r) => {
        const items = r.items || r.data || [];
        setClasses(items);
        if (items[0]) setClassId(items[0].id);
      })
      .catch((e) => console.error(e));
    api("/api/v1/ai/usage").then(setUsage).catch(() => {});
    api("/api/v1/ai/credits").then(setCredits).catch(() => {});
  }, []);

  useEffect(() => {
    if (!classId) {
      setStudents([]);
      setReports([]);
      return;
    }
    api(`/api/v1/academic/students?class_id=${classId}&page_size=100`)
      .then((r) => setStudents(r.items || r.data || []))
      .catch((e) => console.error(e));
    loadReports();
  }, [classId]);

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

  function loadReports() {
    if (!classId) return;
    api(`/api/v1/ai/report-cards?class_id=${classId}`)
      .then((r) => setReports(Array.isArray(r) ? r : r.items || []))
      .catch(() => {});
  }

  function reportFor(studentId: string): Report | undefined {
    return reports.find((r) => r.student_id === studentId);
  }

  async function generate(studentId: string) {
    const cost = credits?.purpose_costs?.report_card ?? 3;
    const remaining = credits?.user_credits_remaining ?? credits?.credits_remaining;
    if (remaining !== undefined && remaining !== null && remaining < cost) {
      setError("Not enough AI credits remaining this month. Contact your class incharge or principal.");
      return;
    }
    setError("");
    setGeneratingId(studentId);
    try {
      const res = await api("/api/v1/ai/report-cards/generate", {
        method: "POST",
        body: JSON.stringify({ student_id: studentId, title }),
      });
      setReport(res);
      loadReports();
      api("/api/v1/ai/usage").then(setUsage).catch(() => {});
      api("/api/v1/ai/credits").then(setCredits).catch(() => {});
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to generate report card."));
    } finally {
      setGeneratingId("");
    }
  }

  async function openExisting(id: string) {
    try {
      const res = await api(`/api/v1/ai/report-cards/${id}`);
      setReport(res);
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to load report card."));
    }
  }

  async function saveRemark() {
    if (!report) return;
    setSaving(true);
    setError("");
    try {
      const res = await api(`/api/v1/ai/report-cards/${report.id}`, {
        method: "PUT",
        body: JSON.stringify({ title: report.title, ai_remark: report.ai_remark }),
      });
      setReport(res);
      loadReports();
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to save."));
    } finally {
      setSaving(false);
    }
  }

  async function approve() {
    if (!report) return;
    try {
      const res = await api(`/api/v1/ai/report-cards/${report.id}/approve`, { method: "POST" });
      setReport(res);
      loadReports();
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to approve."));
    }
  }

  async function openPdf() {
    if (!report || openingDoc || openDocRef.current) return;
    openDocRef.current = true;
    setOpeningDoc(true);
    setError("");
    try {
      const url = await fetchProtectedDocumentUrl(
        `/api/v1/ai/report-cards/${report.id}/pdf`
      );
      setDocPreview((prev) => {
        if (prev?.url) URL.revokeObjectURL(prev.url);
        return { url, title: `Report card — ${report.student_name}` };
      });
    } catch (e) {
      setError(getApiErrorMessage(e, "Could not open the report card."));
    } finally {
      openDocRef.current = false;
      setOpeningDoc(false);
    }
  }

  const approved = report?.status === "approved";

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
        title="Report Cards"
        subtitle="Consolidate each student's marks and attendance into a report card, with a draft remark written for you — review, edit, and approve before issuing."
      />

      {credits && (
        <div className="card sn-credits-banner">
          <div className="stat-icon-container icon-blue">
            <Sparkles size={20} />
          </div>
          <div style={{ flex: 1, minWidth: 200 }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase" }}>
              AI Credits Remaining
            </div>
            <div style={{ fontSize: 22, fontWeight: 800 }}>
              {credits.user_credits_remaining ?? credits.credits_remaining}
              <span style={{ fontSize: 14, fontWeight: 500, color: "var(--text-muted)" }}>
                {" "}
                · {credits.purpose_costs?.report_card ?? 3} credits per report card
              </span>
            </div>
          </div>
        </div>
      )}

      {usage && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16, marginBottom: 24 }}>
          <div className="card" style={{ display: "flex", alignItems: "center", gap: 16, padding: 20 }}>
            <div className="stat-icon-container icon-blue"><Award size={20} /></div>
            <div>
              <div className="stat-label">Report cards generated</div>
              <div style={{ fontSize: 24, fontWeight: 700 }}>{usage.reports_total ?? 0}</div>
            </div>
          </div>
          <div className="card" style={{ display: "flex", alignItems: "center", gap: 16, padding: 20 }}>
            <div className="stat-icon-container icon-green"><CalendarDays size={20} /></div>
            <div>
              <div className="stat-label">This month</div>
              <div style={{ fontSize: 24, fontWeight: 700 }}>{usage.reports_this_month ?? 0}</div>
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

      {/* Report preview */}
      {report && (
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
              ? "Approved — ready to print and issue."
              : "Draft — the remark below was AI-written from this student's marks. Edit it freely, then Approve. Nothing is issued until you do."}
          </div>

          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16 }}>
            <div>
              <div style={{ fontSize: 18, fontWeight: 700 }}>{report.student_name}</div>
              <div style={{ color: "var(--text-muted)", fontSize: 13, marginTop: 2 }}>
                {report.title} · Class {report.class_name}
                {report.ai_model ? ` · ${report.ai_model}` : ""}
              </div>
            </div>
            <span className={`badge ${approved ? "badge-success" : "badge-warning"}`} style={{ whiteSpace: "nowrap" }}>
              {report.status.toUpperCase()}
            </span>
          </div>

          {/* Marks table */}
          <table className="data-table" style={{ margin: "16px 0" }}>
            <thead>
              <tr>
                <th>Subject</th>
                <th style={{ textAlign: "center" }}>Marks</th>
                <th style={{ textAlign: "center" }}>Max</th>
                <th style={{ textAlign: "center" }}>%</th>
              </tr>
            </thead>
            <tbody>
              {report.subjects.map((s, i) => (
                <tr key={i}>
                  <td style={{ fontWeight: 600 }}>{s.subject}</td>
                  <td style={{ textAlign: "center" }}>{s.marks_obtained}</td>
                  <td style={{ textAlign: "center" }}>{s.total_marks}</td>
                  <td style={{ textAlign: "center" }}>
                    {s.total_marks ? Math.round((s.marks_obtained / s.total_marks) * 100) : 0}%
                  </td>
                </tr>
              ))}
              <tr style={{ fontWeight: 700, background: "var(--bg)" }}>
                <td>Total</td>
                <td style={{ textAlign: "center" }}>{report.total_obtained}</td>
                <td style={{ textAlign: "center" }}>{report.total_max}</td>
                <td style={{ textAlign: "center" }}>{Math.round(report.percentage)}%</td>
              </tr>
            </tbody>
          </table>

          {report.not_assessed && report.not_assessed.length > 0 && (
            <div
              style={{
                border: "1px dashed var(--border)",
                borderRadius: "var(--radius-md)",
                padding: "8px 14px",
                margin: "0 0 16px",
                fontSize: 13,
                color: "var(--text-muted)",
              }}
            >
              <strong style={{ color: "var(--text)" }}>Not assessed this term:</strong>{" "}
              {report.not_assessed.join(", ")}
            </div>
          )}

          <div style={{ display: "flex", gap: 24, marginBottom: 16, flexWrap: "wrap" }}>
            <Stat label="Percentage" value={`${report.percentage}%`} />
            <Stat label="Grade" value={report.overall_grade || "—"} />
            <Stat
              label="Attendance"
              value={report.attendance_percentage != null ? `${report.attendance_percentage}%` : "—"}
            />
          </div>

          <label className="stat-label">Class teacher&apos;s remark</label>
          <textarea
            className="form-input"
            value={report.ai_remark || ""}
            onChange={(e) =>
              setReport({ ...report, ai_remark: clampText(e.target.value, AI_INPUT.reportRemarkMaxLength) })
            }
            maxLength={AI_INPUT.reportRemarkMaxLength}
            rows={4}
            style={{ ...selStyle, resize: "vertical", fontFamily: "inherit" }}
          />

          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 16 }}>
            <button className="btn btn-primary" onClick={saveRemark} disabled={saving} style={btnSm}>
              {saving ? "Saving…" : <><Save size={15} /> Save remark</>}
            </button>
            <button
              className="btn btn-primary"
              onClick={approve}
              disabled={approved}
              style={{ ...btnSm, background: approved ? "var(--text-muted)" : "var(--success)" }}
            >
              {approved ? "Approved" : <><Check size={15} /> Approve</>}
            </button>
            <button type="button" className="btn btn-outline" onClick={openPdf} disabled={openingDoc} style={btnSm}>
              <Printer size={15} /> {openingDoc ? "Opening…" : "Open / print"}
            </button>
            <button className="btn btn-ghost" onClick={() => setReport(null)} style={btnSm}>
              Close
            </button>
          </div>
        </div>
      )}

      {/* Class picker + roster */}
      <div className="card" style={{ padding: 24 }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 20 }}>
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
            <label className="stat-label">Report title</label>
            <input className="form-input" value={title} onChange={(e) => setTitle(e.target.value)} style={selStyle} />
          </div>
        </div>

        {error && <div style={{ marginBottom: 14, color: "var(--danger)", fontSize: 13 }}>{error}</div>}

        {students.length === 0 ? (
          <div style={{ color: "var(--text-muted)", fontSize: 14, padding: "12px 0" }}>
            No students in this class.
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Roll</th>
                <th>Student</th>
                <th>Status</th>
                <th style={{ textAlign: "right" }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {students.map((st) => {
                const existing = reportFor(st.id);
                const busy = generatingId === st.id;
                return (
                  <tr key={st.id}>
                    <td>{st.roll_no || "—"}</td>
                    <td style={{ fontWeight: 600 }}>{st.student_name || "—"}</td>
                    <td>
                      {existing ? (
                        <span className={`badge ${existing.status === "approved" ? "badge-success" : "badge-warning"}`}>
                          {existing.status}
                        </span>
                      ) : (
                        <span style={{ color: "var(--text-muted)", fontSize: 13 }}>—</span>
                      )}
                    </td>
                    <td style={{ textAlign: "right" }}>
                      {existing && (
                        <button className="btn btn-ghost" onClick={() => openExisting(existing.id)} style={btnSm}>
                          Open
                        </button>
                      )}
                      <button className="btn btn-primary" onClick={() => generate(st.id)} disabled={busy} style={btnSm}>
                        {busy ? "Generating…" : existing ? "Regenerate" : "Generate"}
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ border: "1px solid var(--border)", borderRadius: "var(--radius-md)", padding: "8px 16px" }}>
      <div className="stat-label">{label}</div>
      <div style={{ fontSize: 20, fontWeight: 700 }}>{value}</div>
    </div>
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
  marginLeft: 8,
};
