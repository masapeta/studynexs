"use client";

import { Cpu } from "lucide-react";
import { MarketingPageHero } from "@/components/marketing/MarketingPageHero";
import { PlatformStackVisual } from "@/components/marketing/PlatformStackVisual";
import { FadeIn } from "@/components/marketing/Motion";
import { CTASection, MarketingFooter } from "@/components/marketing/Sections";
import { TECHNOLOGY_CATEGORIES } from "@/lib/noustriks-content";

export default function TechnologyPage() {
  return (
    <main>
      <MarketingPageHero
        id="technology-heading"
        compact
        eyebrow={
          <>
            <Cpu size={14} aria-hidden />
            Technology
          </>
        }
        title={
          <>
            Engineering depth
            <br />
            <span className="mkt-gradient-text">across every layer</span>
          </>
        }
        lead="The technical foundation behind StudyNexs, Memory Fabric, and future Noustriks platforms."
        visual={<PlatformStackVisual />}
      />

      <section className="mkt-section" aria-labelledby="tech-stack-heading">
        <div className="mkt-container">
          <FadeIn className="mkt-section-header">
            <h2 id="tech-stack-heading" className="mkt-h2">
              Technology stack
            </h2>
            <p className="mkt-lead">Organized by capability — not buzzword bingo.</p>
          </FadeIn>

          <div className="mkt-tech-grid">
            {TECHNOLOGY_CATEGORIES.map((category, i) => (
              <FadeIn key={category.id} delay={i * 0.06}>
                <article id={category.id} className="mkt-tech-category mkt-glass mkt-tech-category--interactive">
                  <h3 className="mkt-h3">{category.title}</h3>
                  <ul className="mkt-tech-list">
                    {category.items.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </article>
              </FadeIn>
            ))}
          </div>
        </div>
      </section>

      <CTASection />
      <MarketingFooter />
    </main>
  );
}
