"use client";

import Link from "next/link";
import {
  Bot,
  Check,
  Cpu,
  Layers,
  Network,
  ScanLine,
  Sparkles,
  Workflow,
  Zap,
} from "lucide-react";
import { MarketingPageHero } from "@/components/marketing/MarketingPageHero";
import { PlatformStackVisual } from "@/components/marketing/PlatformStackVisual";
import { TrustBar } from "@/components/marketing/TrustBar";
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
      <MarketingPageHero
        id="platform-heading"
        compact
        eyebrow={
          <>
            <Cpu size={14} aria-hidden />
            Platform
          </>
        }
        title={
          <>
            Intelligence woven
            <br />
            <span className="mkt-gradient-text">through every layer</span>
          </>
        }
        lead="StudyNexs is not a single feature — it's an operating system where AI amplifies humans at the point of decision, never replacing their judgment."
        actions={
          <MagneticButton href="/login?portal=staff" className="mkt-btn mkt-btn--primary mkt-btn--lg">
            See it live
          </MagneticButton>
        }
        visual={<PlatformStackVisual />}
      />

      <TrustBar />

      <section className="mkt-section" aria-labelledby="bento-heading">
        <div className="mkt-container">
          <FadeIn className="mkt-section-header">
            <div className="mkt-eyebrow mkt-glass" style={{ marginInline: "auto" }}>
              <Sparkles size={14} aria-hidden />
              Core capabilities
            </div>
            <h2 id="bento-heading" className="mkt-h2">
              Architecture of trust
            </h2>
            <p className="mkt-lead">
              Every layer is designed for schools that need explainable AI, not black-box automation.
            </p>
          </FadeIn>
          <div className="mkt-bento">
            {BENTO.map((item, i) => (
              <FadeIn key={item.title} className={`mkt-bento-item mkt-glass ${item.className}`} delay={i * 0.08}>
                <div className="mkt-card-icon">
                  <item.icon size={20} aria-hidden />
                </div>
                <h3 className="mkt-h3">{item.title}</h3>
                <p className="mkt-bento-desc">{item.desc}</p>
              </FadeIn>
            ))}
          </div>
        </div>
      </section>

      <section className="mkt-section mkt-section--alt" aria-labelledby="stack-heading">
        <div className="mkt-container">
          <div className="mkt-grid-12 mkt-grid-12--align-center">
            <FadeIn className="mkt-col-5">
              <div className="mkt-eyebrow mkt-glass">Foundation</div>
              <h2 id="stack-heading" className="mkt-h2 mkt-h2--section">
                Enterprise-grade from day one
              </h2>
              <p className="mkt-lead mkt-lead--section">
                Built for schools that cannot afford downtime, data leaks, or AI runaway costs.
              </p>
            </FadeIn>
            <FadeIn delay={0.15} className="mkt-card mkt-glass mkt-col-7 mkt-stack-card">
              <ul className="mkt-stack-list">
                {STACK.map((line) => (
                  <li key={line} className="mkt-pricing-feature">
                    <Check size={16} aria-hidden />
                    {line}
                  </li>
                ))}
              </ul>
              <div className="mkt-stack-badges">
                <span className="mkt-eyebrow mkt-glass mkt-eyebrow--inline">
                  <Layers size={12} aria-hidden />
                  Modular SMS
                </span>
                <span className="mkt-eyebrow mkt-glass mkt-eyebrow--inline">
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
            <div className="mkt-roadmap-card mkt-glass-strong">
              <div className="mkt-roadmap-copy">
                <div className="mkt-eyebrow mkt-glass mkt-eyebrow--inline">
                  <Bot size={12} aria-hidden />
                  Roadmap
                </div>
                <h2 className="mkt-h3">Interactive AI assistant</h2>
                <p>
                  Text-first tutor for students, expanding to voice and visual explanations — always
                  grounded in your school&apos;s curriculum and mastery data.
                </p>
                <Link href="/login?portal=student" className="mkt-btn mkt-btn--glass">
                  Preview student portal →
                </Link>
              </div>
              <div className="mkt-roadmap-visual mkt-glass" aria-hidden>
                <div className="mkt-roadmap-bubble mkt-roadmap-bubble--user">
                  Explain photosynthesis for Class 8
                </div>
                <div className="mkt-roadmap-bubble mkt-roadmap-bubble--ai">
                  Based on your syllabus — here&apos;s a guided breakdown with practice questions…
                </div>
              </div>
            </div>
          </FadeIn>
        </div>
      </section>

      <CTASection />
      <MarketingFooter />
    </main>
  );
}
