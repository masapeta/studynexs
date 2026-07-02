"use client";

import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { AIStorySection } from "@/components/marketing/AIStorySection";
import { StudyNexsHeroSection } from "@/components/marketing/StudyNexsHeroSection";
import { StudyNexsProductVisual } from "@/components/marketing/StudyNexsProductVisual";
import { TrustBar } from "@/components/marketing/TrustBar";
import { FeatureChipGrid } from "@/components/marketing/ComingSoonCard";
import { FadeIn, MagneticButton } from "@/components/marketing/Motion";
import {
  CTASection,
  FeaturesSection,
  MarketingFooter,
  StatsSection,
  TestimonialsSection,
} from "@/components/marketing/Sections";
import { STUDYNEXS, STUDYNEXS_FEATURES } from "@/lib/noustriks-content";

export default function StudyNexsProductPage() {
  return (
    <main>
      <StudyNexsHeroSection />
      <TrustBar />
      <StatsSection />
      <FeaturesSection />
      <AIStorySection />

      <section className="mkt-section mkt-section--alt" aria-labelledby="studynexs-teaching">
        <div className="mkt-container">
          <FadeIn>
            <Link href="/products" className="mkt-back-link">
              <ArrowLeft size={14} aria-hidden /> All products
            </Link>
            <p className="mkt-product-tagline mkt-product-tagline--page">{STUDYNEXS.tagline}</p>
            <h2 id="studynexs-teaching" className="mkt-h2 mkt-h2--section">
              Teaching hub in action
            </h2>
            <p className="mkt-lead mkt-lead--section">{STUDYNEXS.description}</p>
          </FadeIn>
          <FadeIn delay={0.1} className="mkt-product-visual-wrap" style={{ marginTop: "2rem" }}>
            <StudyNexsProductVisual />
          </FadeIn>
          <FadeIn delay={0.15}>
            <h3 className="mkt-h3 mkt-product-subhead">Full platform capabilities</h3>
            <FeatureChipGrid items={STUDYNEXS_FEATURES} />
          </FadeIn>
          <FadeIn delay={0.2} className="mkt-product-detail-cta mkt-glass">
            <p>
              StudyNexs is a flagship product of Noustriks — built for principals, teachers, and
              families who need intelligence without losing control.
            </p>
            <div className="mkt-product-actions">
              <MagneticButton href="/pricing" className="mkt-btn mkt-btn--glass">
                View pricing
              </MagneticButton>
              <MagneticButton href="/platform" className="mkt-btn mkt-btn--ghost">
                Platform architecture →
              </MagneticButton>
            </div>
          </FadeIn>
        </div>
      </section>

      <TestimonialsSection />
      <CTASection />
      <MarketingFooter />
    </main>
  );
}
