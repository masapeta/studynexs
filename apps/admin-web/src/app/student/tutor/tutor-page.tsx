"use client";

import { FormEvent, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import PortalShell from "@/components/PortalShell";
import TutorLessonPlayer from "@/components/tutor/TutorLessonPlayer";
import { api, getApiErrorMessage } from "@/lib/api";
import { STUDENT_NAV, TutorLesson } from "@/lib/student-portal";

type Rec = {
  lesson_key: string;
  topic: string;
  subject_name: string;
  mastery_pct?: number;
  reason: string;
};

type StudyContext = {
  primary_concept_slug?: string;
  weak_concepts: { slug: string; title: string; mastery_pct?: number }[];
};

type CopilotAnswer = {
  answer: string;
  concept_title?: string;
  follow_up_hints?: string[];
  grounded: boolean;
};

export default function StudentTutorPage() {
  const searchParams = useSearchParams();
  const lessonParam = searchParams.get("lesson");

  const [studentId, setStudentId] = useState<string | null>(null);
  const [recs, setRecs] = useState<Rec[]>([]);
  const [studyContext, setStudyContext] = useState<StudyContext | null>(null);
  const [lesson, setLesson] = useState<TutorLesson | null>(null);
  const [activeKey, setActiveKey] = useState<string | null>(lessonParam);
  const [question, setQuestion] = useState("");
  const [copilotAnswer, setCopilotAnswer] = useState<CopilotAnswer | null>(null);
  const [asking, setAsking] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api("/api/v1/portal/context")
      .then(async (ctx) => {
        const sid = ctx.data?.children?.[0]?.student_id ?? ctx.data?.student_id;
        if (!sid) {
          setError("No student profile linked.");
          setLoading(false);
          return;
        }
        setStudentId(sid);
        const [recRes, ctxRes] = await Promise.all([
          api(`/api/v1/tutor/students/${sid}/recommendations`),
          api(`/api/v1/tutor/students/${sid}/study-context`).catch(() => ({ data: null })),
        ]);
        setRecs(recRes.data || []);
        setStudyContext(ctxRes.data);
        const key = lessonParam || recRes.data?.[0]?.lesson_key;
        if (key) {
          setActiveKey(key);
          const les = await api(`/api/v1/tutor/students/${sid}/lessons/${key}`);
          setLesson(les.data);
        }
      })
      .catch((e) => setError(getApiErrorMessage(e, "Failed to load tutor")))
      .finally(() => setLoading(false));
  }, [lessonParam]);

  async function openLesson(key: string) {
    if (!studentId) return;
    setLoading(true);
    setError("");
    setActiveKey(key);
    setCopilotAnswer(null);
    try {
      const les = await api(`/api/v1/tutor/students/${studentId}/lessons/${key}`);
      setLesson(les.data);
      window.history.replaceState(null, "", `/student/tutor?lesson=${key}`);
    } catch (e) {
      setError(getApiErrorMessage(e, "Could not load lesson"));
    } finally {
      setLoading(false);
    }
  }

  async function askCopilot(e: FormEvent) {
    e.preventDefault();
    if (!studentId || !question.trim()) return;
    setAsking(true);
    setError("");
    setCopilotAnswer(null);
    try {
      const res = await api(`/api/v1/tutor/students/${studentId}/ask`, {
        method: "POST",
        body: JSON.stringify({
          question: question.trim(),
          concept_slug: studyContext?.primary_concept_slug || activeKey || undefined,
        }),
      });
      setCopilotAnswer(res.data);
    } catch (err) {
      setError(getApiErrorMessage(err, "Could not get an answer"));
    } finally {
      setAsking(false);
    }
  }

  return (
    <PortalShell title="AI Tutor" subtitle="Learn like your teacher explains" nav={STUDENT_NAV}>
      <p style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 16 }}>
        Mistake Recovery — grounded in your curriculum. Ask a question or follow a lesson.
      </p>

      {error && <p style={{ color: "var(--danger)" }}>{error}</p>}

      {studyContext?.weak_concepts?.length ? (
        <div className="portal-card" style={{ marginBottom: 16, padding: 14 }}>
          <div style={{ fontSize: 12, fontWeight: 700, color: "var(--text-muted)", marginBottom: 8 }}>
            Focus areas from your mastery
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            {studyContext.weak_concepts.slice(0, 4).map((c) => (
              <span
                key={c.slug}
                style={{
                  fontSize: 12,
                  padding: "4px 10px",
                  borderRadius: 999,
                  background: "var(--surface-muted, rgba(0,0,0,0.04))",
                }}
              >
                {c.title}
                {c.mastery_pct != null ? ` · ${Math.round(c.mastery_pct)}%` : ""}
              </span>
            ))}
          </div>
        </div>
      ) : null}

      <form onSubmit={askCopilot} className="portal-card" style={{ marginBottom: 16, padding: 14 }}>
        <label htmlFor="copilot-question" style={{ fontSize: 12, fontWeight: 700, color: "var(--text-muted)" }}>
          Ask Student Copilot
        </label>
        <textarea
          id="copilot-question"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="What is slope in a linear equation?"
          rows={2}
          maxLength={800}
          style={{ width: "100%", marginTop: 8, marginBottom: 8, resize: "vertical" }}
        />
        <button type="submit" className="btn btn-primary" disabled={asking || !question.trim()}>
          {asking ? "Thinking…" : "Ask"}
        </button>
        {copilotAnswer ? (
          <div style={{ marginTop: 12, fontSize: 14, lineHeight: 1.5 }}>
            {copilotAnswer.concept_title ? (
              <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 4 }}>
                About: {copilotAnswer.concept_title}
              </div>
            ) : null}
            <p style={{ margin: 0 }}>{copilotAnswer.answer}</p>
            {copilotAnswer.follow_up_hints?.length ? (
              <ul style={{ marginTop: 8, paddingLeft: 18, fontSize: 13, color: "var(--text-muted)" }}>
                {copilotAnswer.follow_up_hints.map((h) => (
                  <li key={h}>{h}</li>
                ))}
              </ul>
            ) : null}
          </div>
        ) : null}
      </form>

      {recs.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <div style={{ fontSize: 12, fontWeight: 700, color: "var(--text-muted)", marginBottom: 8 }}>Your topics</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {recs.map((r) => (
              <button
                key={r.lesson_key}
                type="button"
                className={`portal-card tutor-rec-card${activeKey === r.lesson_key ? " active" : ""}`}
                onClick={() => openLesson(r.lesson_key)}
                style={{ textAlign: "left", cursor: "pointer", width: "100%" }}
              >
                <div style={{ fontWeight: 700, fontSize: 14 }}>{r.topic}</div>
                <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 4 }}>{r.reason}</div>
              </button>
            ))}
          </div>
        </div>
      )}

      {loading && !lesson ? (
        <div className="spinner" style={{ margin: "40px auto" }} />
      ) : lesson ? (
        <TutorLessonPlayer lesson={lesson} />
      ) : null}
    </PortalShell>
  );
}
