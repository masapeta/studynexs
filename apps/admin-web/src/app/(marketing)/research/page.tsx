"use client";

import Link from "next/link";
import { FlaskConical } from "lucide-react";
import { MarketingPageHero } from "@/components/marketing/MarketingPageHero";
import { ResearchHeroVisual } from "@/components/marketing/ResearchHeroVisual";
import { FadeIn, MagneticButton } from "@/components/marketing/Motion";
import { CTASection, MarketingFooter } from "@/components/marketing/Sections";
import { RESEARCH_TOPICS } from "@/lib/noustriks-content";

export default function ResearchPage() {
  return (
    <main>
      <MarketingPageHero
        id="research-heading"
        compact
        eyebrow={
          <>
            <FlaskConical size={14} aria-hidden />
            Research
          </>
        }
        title={
          <>
            Investing in the
            <br />
            <span className="mkt-gradient-text">future of intelligence</span>
          </>
        }
        lead="Noustriks Research advances AI, persistent memory, human-AI collaboration, and next-generation computing — with products that translate research into production systems."
        actions={
          <MagneticButton href="/products" className="mkt-btn mkt-btn--glass mkt-btn--lg">
            View products
          </MagneticButton>
        }
        visual={<ResearchHeroVisual />}
      />

      <section className="mkt-section" aria-labelledby="research-topics-heading">
        <div className="mkt-container">
          <FadeIn className="mkt-section-header">
            <h2 id="research-topics-heading" className="mkt-h2">
              Research areas
            </h2>
            <p className="mkt-lead">
              Long-horizon work that shapes how intelligent systems understand, remember, and collaborate.
            </p>
          </FadeIn>

          <div className="mkt-research-grid">
            {RESEARCH_TOPICS.map((topic, i) => (
              <FadeIn key={topic.id} className="mkt-research-card mkt-glass" delay={i * 0.05}>
                <h3 className="mkt-h3">{topic.title}</h3>
                <p>{topic.description}</p>
              </FadeIn>
            ))}
          </div>

          <FadeIn delay={0.2} className="mkt-research-cta mkt-glass-strong">
            <p>
              Noustriks Labs explores experimental products at the edge of what&apos;s possible — with the same
              discipline we bring to production platforms.
            </p>
            <Link href="/products#roadmap" className="mkt-btn mkt-btn--glass">
              See what&apos;s next →
            </Link>
          </FadeIn>
        </div>
      </section>

      <CTASection />
      <MarketingFooter />
    </main>
  );
}
