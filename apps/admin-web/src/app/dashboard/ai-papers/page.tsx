"use client";

import { useEffect, useState } from "react";
import {
  api,
  API_URL,
  TENANT_SLUG,
  getAccessToken,
  getApiErrorMessage,
} from "@/lib/api";

type Question = {
  number: string;
  text: string;
  marks: number;
  type: string;
  options?: string[];
  answer_key?: string;
};
type Section = { title: string; instructions?: string | null; questions: Question[] };
type Paper = {
  id: string;
  title: string;
  board: string;
  grade: string;
  subject_name: string;
  total_marks: number;
  duration_minutes?: number | null;
  general_instructions?: string | null;
  sections: Section[];
  status: string;
  ai_model?: string | null;
};

export default function AiPapersPage() {
  const [classes, setClasses] = useState<any[]>([]);
  const [subjects, setSubjects] = useState<any[]>([]);
  const [classId, setClassId] = useState("");
  const [subjectId, setSubjectId] = useState("");
  const [topics, setTopics] = useState("");
  const [totalMarks, setTotalMarks] = useState(100);
  const [duration, setDuration] = useState(180);
  const [difficulty, setDifficulty] = useState("balanced");

  const [generating, setGenerating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [paper, setPaper] = useState<Paper | null>(null);
  const [showAnswers, setShowAnswers] = useState(false);
  const [recent, setRecent] = useState<any[]>([]);
  const [usage, setUsage] = useState<any>(null);

  useEffect(() => {
    api("/api/v1/academic/classes?page_size=100")
      .then((r) => {
        const items = r.items || r.data || [];
        setClasses(items);
        if (items[0]) setClassId(items[0].id);
      })
      .catch((e) => console.error(e));
    loadRecent();
    api("/api/v1/ai/usage").then(setUsage).catch(() => {});
  }, []);

  useEffect(() => {
    if (!classId) {
      setSubjects([]);
      return;
    }
    api(`/api/v1/academic/subjects?class_id=${classId}`)
      .then((r) => {
        const items = r.items || r.data || (Array.isArray(r) ? r : []);
        setSubjects(items);
        setSubjectId(items[0]?.id || "");
      })
      .catch((e) => console.error(e));
  }, [classId]);

  function loadRecent() {
    api("/api/v1/ai/question-papers")
      .then((r) => setRecent(Array.isArray(r) ? r : r.items || []))
      .catch(() => {});
  }

  async function generate() {
    if (!classId || !subjectId) {
      setError("Pick a class and subject first.");
      return;
    }
    setError("");
    setGenerating(true);
    setPaper(null);
    try {
      const topicList = topics
        .split(/[\n,]/)
        .map((t) => t.trim())
        .filter(Boolean);
      const res = await api("/api/v1/ai/question-papers/generate", {
        method: "POST",
        body: JSON.stringify({
          class_id: classId,
          subject_id: subjectId,
          topics: topicList,
          total_marks: Number(totalMarks),
          duration_minutes: Number(duration),
          difficulty,
        }),
      });
      setPaper(res);
      setShowAnswers(false);
      loadRecent();
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to generate paper. Please try again."));
    } finally {
      setGenerating(false);
    }
  }

  function updateQuestion(si: number, qi: number, value: string) {
    setPaper((p) => {
      if (!p) return p;
      const sections = p.sections.map((s, i) =>
        i !== si
          ? s
          : { ...s, questions: s.questions.map((q, j) => (j !== qi ? q : { ...q, text: value })) }
      );
      return { ...p, sections };
    });
  }

  async function saveEdits() {
    if (!paper) return;
    setSaving(true);
    setError("");
    try {
      const res = await api(`/api/v1/ai/question-papers/${paper.id}`, {
        method: "PUT",
        body: JSON.stringify({
          title: paper.title,
          general_instructions: paper.general_instructions,
          sections: paper.sections,
        }),
      });
      setPaper(res);
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to save edits."));
    } finally {
      setSaving(false);
    }
  }

  async function approve() {
    if (!paper) return;
    try {
      const res = await api(`/api/v1/ai/question-papers/${paper.id}/approve`, { method: "POST" });
      setPaper(res);
      loadRecent();
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to approve."));
    }
  }

  async function openPdf(answers: boolean) {
    if (!paper) return;
    try {
      const res = await fetch(
        `${API_URL}/api/v1/ai/question-papers/${paper.id}/pdf?answers=${answers}`,
        {
          headers: { Authorization: `Bearer ${getAccessToken()}`, "X-Tenant-Slug": TENANT_SLUG },
          credentials: "include",
        }
      );
      const blob = await res.blob();
      window.open(URL.createObjectURL(blob), "_blank");
    } catch {
      setError("Could not open the paper.");
    }
  }

  async function openRecent(id: string) {
    try {
      const res = await api(`/api/v1/ai/question-papers/${id}`);
      setPaper(res);
      setShowAnswers(false);
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to load paper."));
    }
  }

  const approved = paper?.status === "approved";

  return (
    <>
      <div
        className="card bento-glass"
        style={{ marginBottom: 24, padding: "16px 24px" }}
      >
        <h1 style={{ fontSize: 20, fontWeight: 700, margin: 0 }}>AI Question Paper Generator</h1>
        <p style={{ margin: "4px 0 0", color: "var(--text-muted)", fontSize: 13 }}>
          Draft a board-style paper from your syllabus in seconds — then review, edit, and approve
          before it reaches students.
        </p>
      </div>

      {usage && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16, marginBottom: 24 }}>
          <div className="card" style={{ display: "flex", alignItems: "center", gap: 16, padding: 20 }}>
            <div className="stat-icon-container icon-blue">📄</div>
            <div>
              <div className="stat-label">Papers generated</div>
              <div style={{ fontSize: 24, fontWeight: 700 }}>{usage.papers_total}</div>
            </div>
          </div>
          <div className="card" style={{ display: "flex", alignItems: "center", gap: 16, padding: 20 }}>
            <div className="stat-icon-container icon-green">🗓️</div>
            <div>
              <div className="stat-label">This month</div>
              <div style={{ fontSize: 24, fontWeight: 700 }}>{usage.papers_this_month}</div>
            </div>
          </div>
          <div className="card" style={{ display: "flex", alignItems: "center", gap: 16, padding: 20 }}>
            <div className="stat-icon-container icon-purple">⏱️</div>
            <div>
              <div className="stat-label">Est. teacher-hours saved</div>
              <div style={{ fontSize: 24, fontWeight: 700 }}>~{usage.est_hours_saved}</div>
            </div>
          </div>
        </div>
      )}

      {/* Generator form */}
      <div className="card" style={{ marginBottom: 24, padding: 24 }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 }}>
          <div>
            <label className="stat-label">Class</label>
            <select
              className="form-input"
              value={classId}
              onChange={(e) => setClassId(e.target.value)}
              style={selStyle}
            >
              {classes.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.grade} - {c.section}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="stat-label">Subject</label>
            <select
              className="form-input"
              value={subjectId}
              onChange={(e) => setSubjectId(e.target.value)}
              style={selStyle}
            >
              {subjects.length === 0 && <option value="">No subjects for this class</option>}
              {subjects.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div style={{ marginBottom: 16 }}>
          <label className="stat-label">Topics / chapters (one per line or comma-separated)</label>
          <textarea
            className="form-input"
            value={topics}
            onChange={(e) => setTopics(e.target.value)}
            rows={3}
            placeholder="Real Numbers, Polynomials, Quadratic Equations, Triangles, Trigonometry"
            style={{ ...selStyle, resize: "vertical", fontFamily: "inherit" }}
          />
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr auto", gap: 16, alignItems: "end" }}>
          <div>
            <label className="stat-label">Total marks</label>
            <input
              type="number"
              className="form-input"
              value={totalMarks}
              onChange={(e) => setTotalMarks(Number(e.target.value))}
              style={selStyle}
            />
          </div>
          <div>
            <label className="stat-label">Duration (min)</label>
            <input
              type="number"
              className="form-input"
              value={duration}
              onChange={(e) => setDuration(Number(e.target.value))}
              style={selStyle}
            />
          </div>
          <div>
            <label className="stat-label">Difficulty</label>
            <select
              className="form-input"
              value={difficulty}
              onChange={(e) => setDifficulty(e.target.value)}
              style={selStyle}
            >
              <option value="easy">Easy</option>
              <option value="balanced">Balanced</option>
              <option value="hard">Hard</option>
            </select>
          </div>
          <button
            className="btn btn-primary"
            onClick={generate}
            disabled={generating}
            style={{ width: "auto", padding: "10px 24px", borderRadius: "var(--radius-full)" }}
          >
            {generating ? "Generating…" : "✨ Generate Paper"}
          </button>
        </div>

        {error && (
          <div style={{ marginTop: 14, color: "var(--danger)", fontSize: 13 }}>{error}</div>
        )}
        {generating && (
          <div style={{ marginTop: 16, display: "flex", alignItems: "center", gap: 12, color: "var(--text-muted)" }}>
            <div className="spinner" style={{ width: 20, height: 20 }} />
            Drafting your paper with AI — this usually takes 15–30 seconds…
          </div>
        )}
      </div>

      {/* Paper preview */}
      {paper && (
        <div className="card" style={{ padding: 24, marginBottom: 24 }}>
          <div
            style={{
              background: approved ? "rgba(5,150,105,0.08)" : "rgba(37,99,235,0.08)",
              border: `1px solid ${approved ? "var(--success)" : "var(--primary)"}`,
              borderRadius: "var(--radius-md)",
              padding: "10px 14px",
              marginBottom: 16,
              fontSize: 13,
            }}
          >
            {approved
              ? "✅ Teacher-approved. Ready to print and hand out."
              : "🤖 AI-generated draft — review and edit anything, then Approve. Nothing reaches students until you approve."}
          </div>

          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16 }}>
            <input
              className="form-input"
              value={paper.title}
              onChange={(e) => setPaper({ ...paper, title: e.target.value })}
              style={{ ...selStyle, fontSize: 18, fontWeight: 700, flex: 1 }}
            />
            <span className={`badge ${approved ? "badge-success" : "badge-warning"}`} style={{ whiteSpace: "nowrap" }}>
              {paper.status.toUpperCase()}
            </span>
          </div>

          <div style={{ color: "var(--text-muted)", fontSize: 13, margin: "8px 0 16px" }}>
            {paper.board} · {paper.grade} · {paper.subject_name} · {paper.total_marks} marks ·{" "}
            {paper.duration_minutes} min{paper.ai_model ? ` · ${paper.ai_model}` : ""}
          </div>

          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 20 }}>
            <button className="btn btn-primary" onClick={saveEdits} disabled={saving}
              style={btnSm}>{saving ? "Saving…" : "💾 Save edits"}</button>
            <button className="btn btn-primary" onClick={approve} disabled={approved}
              style={{ ...btnSm, background: approved ? "var(--text-muted)" : "var(--success)" }}>
              {approved ? "Approved" : "✔ Approve"}
            </button>
            <button className="btn btn-outline" onClick={() => openPdf(false)} style={btnSm}>
              🖨️ Open / print paper
            </button>
            <button className="btn btn-outline" onClick={() => openPdf(true)} style={btnSm}>
              🔑 Answer key (teacher)
            </button>
            <button className="btn btn-ghost" onClick={() => setShowAnswers((v) => !v)} style={btnSm}>
              {showAnswers ? "Hide answers" : "Show answers inline"}
            </button>
          </div>

          {paper.general_instructions && (
            <div style={{ marginBottom: 16 }}>
              <label className="stat-label">General instructions</label>
              <textarea
                className="form-input"
                value={paper.general_instructions}
                onChange={(e) => setPaper({ ...paper, general_instructions: e.target.value })}
                rows={3}
                style={{ ...selStyle, resize: "vertical", fontFamily: "inherit" }}
              />
            </div>
          )}

          {paper.sections.map((section, si) => (
            <div key={si} style={{ marginBottom: 20 }}>
              <div
                style={{
                  fontWeight: 700,
                  background: "var(--bg)",
                  padding: "6px 12px",
                  borderRadius: "var(--radius-sm)",
                  marginBottom: 8,
                }}
              >
                {section.title}
                {section.instructions && (
                  <span style={{ fontWeight: 400, fontStyle: "italic", color: "var(--text-muted)", marginLeft: 8 }}>
                    {section.instructions}
                  </span>
                )}
              </div>
              {section.questions.map((q, qi) => (
                <div key={qi} style={{ display: "flex", gap: 10, marginBottom: 10, alignItems: "flex-start" }}>
                  <span style={{ fontWeight: 700, minWidth: 28 }}>{q.number}.</span>
                  <div style={{ flex: 1 }}>
                    <textarea
                      value={q.text}
                      onChange={(e) => updateQuestion(si, qi, e.target.value)}
                      rows={Math.max(1, Math.ceil(q.text.length / 90))}
                      style={{
                        width: "100%",
                        border: "1px solid var(--border)",
                        borderRadius: "var(--radius-sm)",
                        padding: "6px 10px",
                        fontFamily: "inherit",
                        fontSize: 14,
                        resize: "vertical",
                      }}
                    />
                    {q.options && q.options.length > 0 && (
                      <div style={{ display: "flex", flexWrap: "wrap", gap: "4px 24px", margin: "4px 0 0 8px", fontSize: 13 }}>
                        {q.options.map((o, oi) => (
                          <span key={oi}>({"abcdefgh"[oi]}) {o}</span>
                        ))}
                      </div>
                    )}
                    {showAnswers && q.answer_key && (
                      <div style={{ marginTop: 4, color: "var(--primary)", fontSize: 13 }}>
                        <b>Ans:</b> {q.answer_key}
                      </div>
                    )}
                  </div>
                  <span style={{ color: "var(--text-muted)", fontWeight: 600, whiteSpace: "nowrap" }}>
                    [{q.marks}]
                  </span>
                </div>
              ))}
            </div>
          ))}
        </div>
      )}

      {/* Recent papers */}
      {recent.length > 0 && (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <div style={{ padding: "14px 24px", fontWeight: 700, borderBottom: "1px solid var(--border)" }}>
            Recent papers
          </div>
          <table className="data-table">
            <thead>
              <tr>
                <th>Title</th>
                <th>Class / Subject</th>
                <th>Marks</th>
                <th>Status</th>
                <th style={{ textAlign: "right" }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {recent.map((p) => (
                <tr key={p.id}>
                  <td style={{ fontWeight: 600 }}>{p.title}</td>
                  <td>{p.grade} · {p.subject_name}</td>
                  <td>{p.total_marks}</td>
                  <td>
                    <span className={`badge ${p.status === "approved" ? "badge-success" : "badge-warning"}`}>
                      {p.status}
                    </span>
                  </td>
                  <td style={{ textAlign: "right" }}>
                    <button className="btn btn-ghost" onClick={() => openRecent(p.id)} style={btnSm}>
                      Open
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
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
};
