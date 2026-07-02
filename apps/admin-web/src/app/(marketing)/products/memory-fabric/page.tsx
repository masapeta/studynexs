"use client";

import Link from "next/link";
import { ArrowLeft, Layers } from "lucide-react";
import { MarketingPageHero } from "@/components/marketing/MarketingPageHero";
import { MemoryFabricVisual } from "@/components/marketing/MemoryFabricVisual";
import { FeatureChipGrid } from "@/components/marketing/ComingSoonCard";
import { FadeIn, MagneticButton } from "@/components/marketing/Motion";
import { CTASection, MarketingFooter } from "@/components/marketing/Sections";
import {
  MEMORY_FABRIC,
  MEMORY_FABRIC_CAPABILITIES,
  MEMORY_FABRIC_INDUSTRIES,
} from "@/lib/noustriks-content";

export default function MemoryFabricProductPage() {
  return (
    <main>
      <MarketingPageHero
        id="memory-fabric-heading"
        compact
        eyebrow={
          <>
            <Layers size={14} aria-hidden />
            Flagship · Enterprise
          </>
        }
        title={
          <>
            Memory Fabric
            <br />
            <span className="mkt-gradient-text">shared intelligence</span>
          </>
        }
        lead={MEMORY_FABRIC.shortDescription}
        actions={
          <MagneticButton href="/contact" className="mkt-btn mkt-btn--primary mkt-btn--lg">
            Talk to us
          </MagneticButton>
        }
        visual={<MemoryFabricVisual />}
      />

      <section className="mkt-section" aria-labelledby="memory-about">
        <div className="mkt-container">
          <FadeIn>
            <Link href="/products" className="mkt-back-link">
              <ArrowLeft size={14} aria-hidden /> All products
            </Link>
            <p className="mkt-product-tagline mkt-product-tagline--page">{MEMORY_FABRIC.tagline}</p>
            <p className="mkt-lead mkt-lead--section" id="memory-about">
              {MEMORY_FABRIC.description}
            </p>
            <p className="mkt-noustriks-body">{MEMORY_FABRIC.extendedDescription}</p>
          </FadeIn>
          <FadeIn delay={0.12}>
            <h2 className="mkt-h3 mkt-product-subhead">Capabilities</h2>
            <FeatureChipGrid items={MEMORY_FABRIC_CAPABILITIES} />
          </FadeIn>
          <FadeIn delay={0.16}>
            <h2 className="mkt-h3 mkt-product-subhead">Supported industries</h2>
            <FeatureChipGrid items={MEMORY_FABRIC_INDUSTRIES} />
          </FadeIn>
          <FadeIn delay={0.2} className="mkt-product-detail-cta mkt-glass">
            <p>Memory Fabric is AI infrastructure — not another chatbot. It persists context across agents, teams, and workflows.</p>
            <MagneticButton href="/technology#memory" className="mkt-btn mkt-btn--glass">
              Memory technology →
            </MagneticButton>
          </FadeIn>
        </div>
      </section>

      <CTASection />
      <MarketingFooter />
    </main>
  );
}
