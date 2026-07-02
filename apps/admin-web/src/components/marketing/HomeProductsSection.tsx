"use client";

import { ProductHubCard } from "@/components/marketing/ProductHubCard";
import { FadeIn } from "@/components/marketing/Motion";
import { FLAGSHIP_PRODUCTS } from "@/lib/noustriks-content";

export function HomeProductsSection() {
  return (
    <section className="mkt-section" id="what-we-build" aria-labelledby="what-we-build-heading">
      <div className="mkt-container">
        <FadeIn className="mkt-section-header">
          <div className="mkt-eyebrow mkt-glass" style={{ marginInline: "auto" }}>
            What we build
          </div>
          <h2 id="what-we-build-heading" className="mkt-h2">
            Flagship platforms
          </h2>
          <p className="mkt-lead">
            Each product is a complete operating layer — education and enterprise, sharing the same
            intelligence infrastructure.
          </p>
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
  );
}
