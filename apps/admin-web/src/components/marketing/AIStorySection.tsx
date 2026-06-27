"use client";

import type { CSSProperties } from "react";
import Link from "next/link";
import { FadeIn } from "./Motion";
import {
  BarChart3,
  BookOpen,
  GraduationCap,
  HeartHandshake,
  Sparkles,
} from "lucide-react";

const CHAPTERS = [
  {
    id: "principals",
    icon: BarChart3,
    tag: "Principals",
    title: "Lead with a live pulse on your entire school",
    desc: "Morning briefings surface attendance, fees, and mastery alerts before the first bell. Every AI insight is explainable — no black-box verdicts on children.",
    bullets: ["School-wide command center", "Fee & admissions health", "Audit-ready decisions"],
    accent: "rgba(59, 130, 246, 0.14)",
  },
  {
    id: "teachers",
    icon: BookOpen,
    tag: "Teachers",
    title: "Generate, assess, and communicate in one flow",
    desc: "Question papers in minutes. Answer-sheet evaluation with human approval. Report card remarks drafted — you edit every word before parents see it.",
    bullets: ["AI papers & rubrics", "Mastery weakness flags", "Time saved every exam week"],
    accent: "rgba(14, 165, 233, 0.12)",
  },
  {
    id: "students",
    icon: GraduationCap,
    tag: "Students",
    title: "A tutor that knows your syllabus — not the whole internet",
    desc: "Guided lessons tied to weak concepts after evaluations. Mastery tracking that builds confidence, not anxiety.",
    bullets: ["Concept remediation", "Mobile-first learning", "Age-appropriate guardrails"],
    accent: "rgba(99, 102, 241, 0.12)",
  },
  {
    id: "parents",
    icon: HeartHandshake,
    tag: "Parents",
    title: "Every child's story, clearly — in your pocket",
    desc: "Attendance, fees, teacher-approved remarks, and weak-topic alerts. One feed. No more chasing the school on WhatsApp.",
    bullets: ["Real-time progress feed", "Fee transparency", "Teacher-trusted messaging"],
    accent: "rgba(168, 85, 247, 0.1)",
  },
];

export function AIStorySection() {
  return (
    <section className="mkt-section mkt-story" id="roles" aria-labelledby="story-heading">
      <div className="mkt-container">
        <FadeIn className="mkt-section-header">
          <div className="mkt-eyebrow mkt-glass" style={{ marginInline: "auto" }}>
            <Sparkles size={14} aria-hidden />
            How AI helps everyone
          </div>
          <h2 id="story-heading" className="mkt-h2">
            Intelligence woven into every role
          </h2>
          <p className="mkt-lead">
            StudyNexs is not a chatbot on the side — it is the operating system where AI assists,
            humans approve, and schools stay in control.
          </p>
        </FadeIn>

        <div className="mkt-story-track">
          {CHAPTERS.map((ch, i) => (
            <FadeIn key={ch.id} delay={i * 0.08}>
              <article
                className="mkt-story-chapter mkt-glass"
                style={{ "--mkt-chapter-accent": ch.accent } as CSSProperties}
              >
                <div className="mkt-story-chapter-icon">
                  <ch.icon size={22} strokeWidth={1.75} aria-hidden />
                </div>
                <div className="mkt-story-chapter-body">
                  <span className="mkt-role-tag" style={{ position: "static", marginBottom: "0.75rem" }}>
                    {ch.tag}
                  </span>
                  <h3 className="mkt-h3">{ch.title}</h3>
                  <p className="mkt-story-desc">{ch.desc}</p>
                  <ul className="mkt-story-bullets">
                    {ch.bullets.map((b) => (
                      <li key={b}>{b}</li>
                    ))}
                  </ul>
                </div>
                <div className="mkt-story-visual" aria-hidden>
                  <div className="mkt-story-visual-ring" />
                  <div className="mkt-story-visual-core">
                    <ch.icon size={28} strokeWidth={1.5} />
                  </div>
                </div>
              </article>
            </FadeIn>
          ))}
        </div>

        <FadeIn>
          <p className="mkt-story-cta-line">
            See the full platform stack — academics, finance, and family portals.{" "}
            <Link href="/platform">Explore platform →</Link>
          </p>
        </FadeIn>
      </div>
    </section>
  );
}
