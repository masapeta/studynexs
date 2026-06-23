"use client";

import { useEffect, useState } from "react";
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

export default function StudentTutorPage() {
  const searchParams = useSearchParams();
  const lessonParam = searchParams.get("lesson");

  const [studentId, setStudentId] = useState<string | null>(null);
  const [recs, setRecs] = useState<Rec[]>([]);
  const [lesson, setLesson] = useState<TutorLesson | null>(null);
  const [activeKey, setActiveKey] = useState<string | null>(lessonParam);
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
        const recRes = await api(`/api/v1/tutor/students/${sid}/recommendations`);
        setRecs(recRes.data || []);
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

  return (
    <PortalShell title="AI Tutor" subtitle="Learn like your teacher explains" nav={STUDENT_NAV}>
      <p style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 16 }}>
        Mistake Recovery — voice, pictures, pause & replay. From your exam mistakes and weak topics.
      </p>

      {error && <p style={{ color: "var(--danger)" }}>{error}</p>}

      {recs.length > 1 && (
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
