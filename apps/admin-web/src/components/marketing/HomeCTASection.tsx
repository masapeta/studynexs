"use client";

import { HOME_CTA } from "@/lib/noustriks-content";
import { FadeIn, MagneticButton } from "./Motion";

export function HomeCTASection() {
  return (
    <section className="mkt-section" aria-labelledby="home-cta-heading">
      <div className="mkt-container">
        <FadeIn>
          <div className="mkt-cta mkt-glass-strong">
            <h2 id="home-cta-heading" className="mkt-h2" style={{ position: "relative" }}>
              {HOME_CTA.title}
            </h2>
            <p className="mkt-lead" style={{ margin: "1rem auto 0", position: "relative" }}>
              {HOME_CTA.lead}
            </p>
            <div className="mkt-hero-actions" style={{ position: "relative" }}>
              <MagneticButton href={HOME_CTA.primary.href} className="mkt-btn mkt-btn--primary mkt-btn--lg">
                {HOME_CTA.primary.label}
              </MagneticButton>
              <MagneticButton href={HOME_CTA.secondary.href} className="mkt-btn mkt-btn--glass mkt-btn--lg">
                {HOME_CTA.secondary.label}
              </MagneticButton>
            </div>
          </div>
        </FadeIn>
      </div>
    </section>
  );
}
