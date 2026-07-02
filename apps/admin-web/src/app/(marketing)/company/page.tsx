"use client";

import Link from "next/link";
import { Building2, Sparkles } from "lucide-react";
import { MarketingPageHero } from "@/components/marketing/MarketingPageHero";
import { PlatformStackVisual } from "@/components/marketing/PlatformStackVisual";
import { AboutNoustriksSection, VisionSection } from "@/components/marketing/NoustriksSections";
import { FadeIn, MagneticButton } from "@/components/marketing/Motion";
import { CTASection, MarketingFooter } from "@/components/marketing/Sections";
import { NOUSTRIKS } from "@/lib/noustriks-content";

export default function CompanyPage() {
  return (
    <main>
      <MarketingPageHero
        id="company-heading"
        compact
        eyebrow={
          <>
            <Building2 size={14} aria-hidden />
            Company
          </>
        }
        title={
          <>
            Deep technology
            <br />
            <span className="mkt-gradient-text">built with purpose</span>
          </>
        }
        lead={NOUSTRIKS.description}
        actions={
          <>
            <MagneticButton href="/products" className="mkt-btn mkt-btn--primary mkt-btn--lg">
              Our products
            </MagneticButton>
            <MagneticButton href="/contact" className="mkt-btn mkt-btn--glass mkt-btn--lg">
              Contact
            </MagneticButton>
          </>
        }
        visual={<PlatformStackVisual />}
      />

      <section className="mkt-section mkt-section--alt" aria-labelledby="company-story">
        <div className="mkt-container">
          <FadeIn className="mkt-company-story mkt-glass-strong">
            <div className="mkt-eyebrow mkt-glass mkt-eyebrow--inline">
              <Sparkles size={12} aria-hidden />
              Our approach
            </div>
            <h2 id="company-story" className="mkt-h2 mkt-h2--section">
              Products over platforms-for-the-sake-of-platforms
            </h2>
            <p className="mkt-lead mkt-lead--section">{NOUSTRIKS.mission}</p>
            <p className="mkt-noustriks-body">
              StudyNexs brings intelligent school operations to education. Memory Fabric brings persistent
              organizational memory to enterprise AI. Both share a commitment to human approval, auditability,
              and systems that improve with use — not generic automation.
            </p>
            <div className="mkt-noustriks-actions">
              <Link href="/research" className="mkt-btn mkt-btn--glass">
                Research program
              </Link>
              <Link href="/technology" className="mkt-btn mkt-btn--ghost">
                Technology stack →
              </Link>
            </div>
          </FadeIn>
        </div>
      </section>

      <section className="mkt-section mkt-section--alt" aria-labelledby="company-legal">
        <div className="mkt-container">
          <FadeIn className="mkt-company-story mkt-glass-strong">
            <h2 id="company-legal" className="mkt-h2 mkt-h2--section">
              Ownership &amp; IP
            </h2>
            <p className="mkt-noustriks-body">
              {NOUSTRIKS.name} owns the intellectual property for StudyNexs, Memory Fabric, and
              related products in this platform. Founder and owner: {NOUSTRIKS.owner} (
              {NOUSTRIKS.ownerAlias}). All software is proprietary — licensed to schools under
              agreement, not open source.
            </p>
          </FadeIn>
        </div>
      </section>

      <AboutNoustriksSection />
      <VisionSection />
      <CTASection />
      <MarketingFooter />
    </main>
  );
}
