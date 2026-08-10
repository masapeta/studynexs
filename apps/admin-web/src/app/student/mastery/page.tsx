"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { BookOpen, Sparkles, Target, TrendingUp } from "lucide-react";
import PortalShell from "@/components/PortalShell";
import { EmptyState, ProgressBar, Ring, SkeletonCard } from "@/components/ui/kit";
import { api, getApiErrorMessage } from "@/lib/api";
import { STUDENT_NAV } from "@/lib/student-portal";
import type { MasteryData, MasterySubject, PortalContext } from "@/lib/portal-types";

const NAV = STUDENT_NAV;

function subjectAverage(subject: MasterySubject): number {
  const topics = subject.topics || [];
  if (topics.length === 0) return 0;
  return topics.reduce((sum, t) => sum + (t.mastery_pct || 0), 0) / topics.length;
}

function masteryWord(pct: number): string {
  if (pct >= 85) return "Excellent";
  if (pct >= 70) return "Strong";
  if (pct >= 50) return "Growing";
  return "Needs practice";
}

function titleCase(s: string): string {
  return s.replace(/\b\w/g, (ch) => ch.toUpperCase());
}

export default function StudentMasteryPage() {
  const [mastery, setMastery] = useState<MasteryData | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    api<{ data: PortalContext }>("/api/v1/portal/context")
      .then(async (r) => {
        const sid = r.data?.children?.[0]?.student_id ?? r.data?.student_id;
        if (!sid) return null;
        return api<{ data: MasteryData }>(`/api/v1/mastery/students/${sid}`);
      })
      .then((m) => {
        if (active && m) setMastery(m.data);
      })
      .catch((e) => {
        if (active) setError(getApiErrorMessage(e, "Failed to load"));
      });
    return () => {
      active = false;
    };
  }, []);

  const subjects = useMemo(() => mastery?.subjects || [], [mastery]);
  const overall = useMemo(() => {
    if (subjects.length === 0) return 0;
    return Math.round(subjects.reduce((sum, s) => sum + subjectAverage(s), 0) / subjects.length);
  }, [subjects]);
  const strongestTopic = useMemo(() => {
    let best: { topic: string; pct: number } | null = null;
    for (const s of subjects) {
      for (const t of s.topics || []) {
        if (!best || t.mastery_pct > best.pct) best = { topic: t.topic, pct: t.mastery_pct };
      }
    }
    return best;
  }, [subjects]);

  return (
    <PortalShell title="Mastery" subtitle="Topic-wise progress" nav={NAV}>
      {error && <p style={{ color: "var(--danger)" }}>{error}</p>}
      {!mastery ? (
        <>
          <SkeletonCard />
          <SkeletonCard />
        </>
      ) : subjects.length === 0 ? (
        <EmptyState
          icon={Target}
          title="Your mastery map is coming"
          message="As your teachers mark exams, every topic you've learned shows up here with a progress score. Take your first test to light this up."
        />
      ) : (
        <>
          {/* Overall progress hero */}
          <div className="ui-card mastery-hero">
            <Ring pct={overall} size={84} label={`${overall}%`} />
            <div className="mastery-hero-copy">
              <div className="mastery-hero-title">
                {masteryWord(overall)}
                {overall >= 70 && <Sparkles size={16} aria-hidden className="mastery-hero-spark" />}
              </div>
              <p className="mastery-hero-sub">
                Overall mastery across {subjects.length} subject{subjects.length === 1 ? "" : "s"}
              </p>
              {strongestTopic && strongestTopic.pct >= 70 && (
                <p className="mastery-hero-best">
                  <TrendingUp size={13} aria-hidden /> Best topic: {titleCase(strongestTopic.topic)} (
                  {Math.round(strongestTopic.pct)}%)
                </p>
              )}
            </div>
          </div>

          {/* Per-subject breakdown */}
          {subjects.map((subject) => {
            const avg = Math.round(subjectAverage(subject));
            return (
              <div key={subject.subject_name} className="ui-card mastery-subject">
                <div className="mastery-subject-head">
                  <span className="mastery-subject-icon">
                    <BookOpen size={16} aria-hidden />
                  </span>
                  <span className="mastery-subject-name">{subject.subject_name}</span>
                  <span className="mastery-subject-avg">{avg}%</span>
                </div>
                <div className="mastery-topic-list">
                  {(subject.topics || []).slice(0, 6).map((topic) => {
                    const pct = Math.round(topic.mastery_pct);
                    return (
                      <div key={topic.topic} className="mastery-topic-row">
                        <span className="mastery-topic-name" title={topic.topic}>
                          {titleCase(topic.topic)}
                        </span>
                        <div className="mastery-topic-bar">
                          <ProgressBar pct={pct} />
                        </div>
                        <span className="mastery-topic-pct">{pct}%</span>
                      </div>
                    );
                  })}
                </div>
                {(subject.topics || []).some((t) => t.mastery_pct < 70) && (
                  <Link href="/student/tutor" className="mastery-subject-cta">
                    Practice weak topics with the AI Tutor →
                  </Link>
                )}
              </div>
            );
          })}
        </>
      )}
    </PortalShell>
  );
}
