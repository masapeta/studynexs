"use client";

import { Boxes } from "lucide-react";
import { MarketingPageHero } from "@/components/marketing/MarketingPageHero";
import { ProductHubCard } from "@/components/marketing/ProductHubCard";
import { ComingSoonCard } from "@/components/marketing/ComingSoonCard";
import { PlatformStackVisual } from "@/components/marketing/PlatformStackVisual";
import { FadeIn } from "@/components/marketing/Motion";
import { CTASection, MarketingFooter } from "@/components/marketing/Sections";
import { COMING_SOON_PRODUCTS, FLAGSHIP_PRODUCTS, NOUSTRIKS } from "@/lib/noustriks-content";

export default function ProductsPage() {
  return (
    <main>
      <MarketingPageHero
        id="products-heading"
        compact
        eyebrow={
          <>
            <Boxes size={14} aria-hidden />
            Products
          </>
        }
        title={
          <>
            Platforms from
            <br />
            <span className="mkt-gradient-text">{NOUSTRIKS.name}</span>
          </>
        }
        lead="Each product is a complete operating layer — built on shared intelligence infrastructure, designed for the domain it serves."
        visual={<PlatformStackVisual />}
      />

      <section className="mkt-section" aria-labelledby="flagship-heading">
        <div className="mkt-container">
          <FadeIn className="mkt-section-header">
            <h2 id="flagship-heading" className="mkt-h2">
              Flagship products
            </h2>
            <p className="mkt-lead">Select a product to explore capabilities, architecture, and use cases.</p>
          </FadeIn>
          <div className="mkt-product-hub-grid">
            {FLAGSHIP_PRODUCTS.map((product, i) => (
              <ProductHubCard
                key={product.slug}
                name={product.name}
                tagline={product.tagline}
                description={product.shortDescription}
                href={product.href}
                category={product.category}
                accent={product.accent}
                delay={i * 0.1}
              />
            ))}
          </div>
        </div>
      </section>

      <section className="mkt-section mkt-section--alt" id="roadmap" aria-labelledby="roadmap-heading">
        <div className="mkt-container">
          <FadeIn className="mkt-section-header">
            <div className="mkt-eyebrow mkt-glass" style={{ marginInline: "auto" }}>
              Roadmap
            </div>
            <h2 id="roadmap-heading" className="mkt-h2">
              Future platforms
            </h2>
            <p className="mkt-lead">Noustriks Labs and Research — investing in what comes next.</p>
          </FadeIn>
          <div className="mkt-coming-soon-grid">
            {COMING_SOON_PRODUCTS.map((product, i) => (
              <ComingSoonCard
                key={product.id}
                name={product.name}
                tagline={product.tagline}
                status={product.status}
                href={"href" in product ? product.href : undefined}
                delay={i * 0.08}
              />
            ))}
          </div>
        </div>
      </section>

      <CTASection />
      <MarketingFooter />
    </main>
  );
}
