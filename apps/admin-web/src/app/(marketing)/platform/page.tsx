"use client";

import Link from "next/link";
import {
  Bot,
  Check,
  Cpu,
  Layers,
  Network,
  ScanLine,
  Workflow,
  Zap,
} from "lucide-react";
import { FadeIn, MagneticButton } from "@/components/marketing/Motion";
import { CTASection, MarketingFooter } from "@/components/marketing/Sections";

const BENTO = [
  {
    className: "mkt-bento-item--wide",
    icon: Bot,
    title: "Human-in-the-loop AI",
    desc: "Every AI output is a draft. Teachers approve papers, narratives, and grades before they reach families.",
  },
  {
    className: "mkt-bento-item--tall",
    icon: Network,
    title: "Neural mastery graph",
    desc: "Topic-level understanding built from real assessments — not guesswork. Flags surface automatically when patterns emerge.",
  },
  {
    className: "mkt-bento-item--tall",
    icon: ScanLine,
    title: "Vision evaluation",
    desc: "Snap answer sheets. AI grades, teachers confirm. Marks flow to report cards without re-entry.",
  },
  {
    className: "mkt-bento-item--wide",
    icon: Workflow,
    title: "Operations orchestration",
    desc: "Admissions, fees, attendance, transport, residential — unified data model with AI layered on top.",
  },
];

const STACK = [
  "Multi-tenant isolation with school-scoped queries",
  "Credit-metered AI with principal overrides",
  "Audit logging for compliance workflows",
  "Role-based portals for staff, teachers, parents, students",
  "Outbox pattern for reliable notifications",
  "Provider-agnostic LLM gateway",
];

export default function PlatformPage() {
  return (
    <main>
      <section className="mkt-hero" style={{ minHeight: "85dvh" }} aria-labelledby="platform-heading">
        <FadeIn>
          <div className="mkt-eyebrow mkt-glass" style={{ marginInline: "auto" }}>
            <Cpu size={14} aria-hidden />
            Platform
          </div>
          <h1 id="platform-heading" className="mkt-h1">
            Intelligence woven
            <br />
            <span className="mkt-gradient-text">through every layer</span>
          </h1>
          <p className="mkt-lead" style={{ marginInline: "auto", marginTop: "1.25rem" }}>
            StudyNexs is not a single feature — it&apos;s an operating system where AI amplifies
            humans at the point of decision, never replacing their judgment.
          </p>
          <div className="mkt-hero-actions">
            <MagneticButton href="/login?portal=staff" className="mkt-btn mkt-btn--primary mkt-btn--lg">
              See it live
            </MagneticButton>
          </div>
        </FadeIn>
      </section>

      <section className="mkt-section" aria-labelledby="bento-heading">
        <div className="mkt-container">
          <FadeIn className="mkt-section-header">
            <h2 id="bento-heading" className="mkt-h2">
              Architecture of trust
            </h2>
          </FadeIn>
          <div className="mkt-bento">
            {BENTO.map((item, i) => (
              <FadeIn key={item.title} className={`mkt-bento-item mkt-glass ${item.className}`} delay={i * 0.08}>
                <div className="mkt-card-icon">
                  <item.icon size={20} aria-hidden />
                </div>
                <h3 className="mkt-h3">{item.title}</h3>
                <p style={{ marginTop: "0.65rem", fontSize: "0.92rem", color: "var(--mkt-gray-500)", lineHeight: 1.65 }}>
                  {item.desc}
                </p>
              </FadeIn>
            ))}
          </div>
        </div>
      </section>

      <section className="mkt-section" aria-labelledby="stack-heading">
        <div className="mkt-container">
          <div className="mkt-grid-12">
            <FadeIn className="mkt-col-5">
              <div className="mkt-eyebrow mkt-glass">Foundation</div>
              <h2 id="stack-heading" className="mkt-h2" style={{ fontSize: "clamp(1.75rem, 3vw, 2.5rem)" }}>
                Enterprise-grade from day one
              </h2>
              <p className="mkt-lead" style={{ marginTop: "1rem" }}>
                Built for schools that cannot afford downtime, data leaks, or AI runaway costs.
              </p>
            </FadeIn>
            <FadeIn delay={0.15} className="mkt-card mkt-glass mkt-col-7">
              <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
                {STACK.map((line) => (
                  <li key={line} className="mkt-pricing-feature">
                    <Check size={16} aria-hidden />
                    {line}
                  </li>
                ))}
              </ul>
              <div style={{ marginTop: "1.5rem", display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
                <span className="mkt-eyebrow mkt-glass" style={{ margin: 0 }}>
                  <Layers size={12} aria-hidden />
                  Modular SMS
                </span>
                <span className="mkt-eyebrow mkt-glass" style={{ margin: 0 }}>
                  <Zap size={12} aria-hidden />
                  Metered AI
                </span>
              </div>
            </FadeIn>
          </div>
        </div>
      </section>

      <section className="mkt-section">
        <div className="mkt-container">
          <FadeIn>
            <div className="mkt-cta mkt-glass" style={{ textAlign: "left", padding: "2.5rem" }}>
              <h2 className="mkt-h3">Interactive AI assistant (roadmap)</h2>
              <p style={{ marginTop: "0.75rem", color: "var(--mkt-gray-500)", maxWidth: "36rem", lineHeight: 1.65 }}>
                Text-first tutor for students, expanding to voice and visual explanations — always
                grounded in your school&apos;s curriculum and mastery data.
              </p>
              <Link href="/login?portal=student" className="mkt-btn mkt-btn--glass" style={{ marginTop: "1.25rem" }}>
                Preview student portal →
              </Link>
            </div>
          </FadeIn>
        </div>
      </section>

      <CTASection />
      <MarketingFooter />
    </main>
  );
}
