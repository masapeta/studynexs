"use client";

import Link from "next/link";
import { Brain, Building2, Network } from "lucide-react";
import { NOUSTRIKS } from "@/lib/noustriks-content";
import { FadeIn, MagneticButton } from "./Motion";

const PILLARS = [
  { icon: Brain, label: NOUSTRIKS.focusAreas[0].title, desc: NOUSTRIKS.focusAreas[0].description },
  { icon: Network, label: NOUSTRIKS.focusAreas[1].title, desc: NOUSTRIKS.focusAreas[1].description },
  { icon: Building2, label: NOUSTRIKS.focusAreas[2].title, desc: NOUSTRIKS.focusAreas[2].description },
];

/** Homepage bridge: StudyNexs product story → Noustriks company focus. */
export function CompanyFocusSection() {
  return (
    <section className="mkt-section mkt-section--company-focus" aria-labelledby="company-focus-heading">
      <div className="mkt-container">
        <FadeIn className="mkt-section-header">
          <div className="mkt-eyebrow mkt-glass" style={{ marginInline: "auto" }}>
            <Building2 size={14} aria-hidden />
            Built by {NOUSTRIKS.name}
          </div>
          <h2 id="company-focus-heading" className="mkt-h2">
            {NOUSTRIKS.aboutTitle}
          </h2>
          <p className="mkt-lead">{NOUSTRIKS.description}</p>
        </FadeIn>

        <div className="mkt-company-pillars">
          {PILLARS.map((pillar, i) => (
            <FadeIn key={pillar.label} className="mkt-company-pillar mkt-glass" delay={i * 0.08}>
              <span className="mkt-company-pillar-icon">
                <pillar.icon size={18} strokeWidth={1.75} aria-hidden />
              </span>
              <h3 className="mkt-h3">{pillar.label}</h3>
              <p>{pillar.desc}</p>
            </FadeIn>
          ))}
        </div>

        <FadeIn delay={0.2} className="mkt-company-focus-cta">
          <p className="mkt-noustriks-body">{NOUSTRIKS.mission}</p>
          <div className="mkt-noustriks-actions" style={{ justifyContent: "center", marginTop: "1.5rem" }}>
            <MagneticButton href="/company" className="mkt-btn mkt-btn--glass">
              About Noustriks
            </MagneticButton>
            <MagneticButton href="/products" className="mkt-btn mkt-btn--ghost">
              View all products →
            </MagneticButton>
          </div>
        </FadeIn>
      </div>
    </section>
  );
}
