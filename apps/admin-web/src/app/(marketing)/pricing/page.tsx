"use client";

import { Check, Sparkles } from "lucide-react";
import { MarketingPageHero } from "@/components/marketing/MarketingPageHero";
import { PricingHeroVisual } from "@/components/marketing/PricingHeroVisual";
import { TrustBar } from "@/components/marketing/TrustBar";
import { FadeIn, MagneticButton, Stagger, StaggerItem } from "@/components/marketing/Motion";
import { CTASection, MarketingFooter } from "@/components/marketing/Sections";

const PLANS = [
  {
    name: "Pilot",
    price: "Free",
    period: "controlled trial",
    desc: "For schools evaluating AI papers and core SMS.",
    featured: false,
    features: [
      "Core SMS modules",
      "AI question papers (metered)",
      "Parent & student portals",
      "100 AI credits / month",
      "Email support",
    ],
  },
  {
    name: "Pro",
    price: "₹—",
    period: "per school / month",
    desc: "Full platform for growing schools ready to scale AI.",
    featured: true,
    features: [
      "Everything in Pilot",
      "Mastery intelligence",
      "Answer sheet evaluation",
      "Report card AI remarks",
      "Priority onboarding",
      "Higher AI credit pool",
    ],
  },
  {
    name: "Enterprise",
    price: "Custom",
    period: "multi-branch",
    desc: "For groups, chains, and institutions with compliance needs.",
    featured: false,
    features: [
      "Multi-branch tenancy",
      "Custom AI budgets & overrides",
      "Dedicated success manager",
      "SLA & audit exports",
      "On-prem / data residency options",
      "Curriculum pack integration",
    ],
  },
];

export default function PricingPage() {
  return (
    <main>
      <MarketingPageHero
        id="pricing-heading"
        compact
        eyebrow={
          <>
            <Sparkles size={14} aria-hidden />
            Pricing
          </>
        }
        title={
          <>
            Simple plans.
            <br />
            <span className="mkt-gradient-text">Serious schools.</span>
          </>
        }
        lead="Start with a pilot. Scale when your staff and families are ready. No surprise AI bills — credits are metered and visible."
        visual={<PricingHeroVisual />}
      />

      <TrustBar />

      <section className="mkt-section mkt-section--pricing" aria-labelledby="plans-heading">
        <div className="mkt-container">
          <FadeIn className="mkt-section-header">
            <h2 id="plans-heading" className="mkt-h2">
              Choose your starting point
            </h2>
            <p className="mkt-lead">
              Every plan includes tenant isolation, role-based access, and human-in-the-loop AI controls.
            </p>
          </FadeIn>

          <Stagger className="mkt-pricing-grid">
            {PLANS.map((plan) => (
              <StaggerItem key={plan.name}>
                <article
                  className={`mkt-card mkt-glass mkt-pricing-card${
                    plan.featured ? " mkt-pricing-card--featured" : ""
                  }`}
                >
                  {plan.featured && (
                    <span className="mkt-eyebrow mkt-glass mkt-pricing-badge">Most popular</span>
                  )}
                  <h3 className="mkt-h3">{plan.name}</h3>
                  <div className="mkt-price">
                    {plan.price}
                    {plan.period && <span> / {plan.period}</span>}
                  </div>
                  <p className="mkt-pricing-desc">{plan.desc}</p>
                  <ul className="mkt-pricing-list">
                    {plan.features.map((f) => (
                      <li key={f} className="mkt-pricing-feature">
                        <Check size={16} aria-hidden />
                        {f}
                      </li>
                    ))}
                  </ul>
                  <MagneticButton
                    href="/login?portal=staff"
                    className={`mkt-btn mkt-btn--lg mkt-btn--block${plan.featured ? " mkt-btn--primary" : " mkt-btn--glass"}`}
                  >
                    {plan.name === "Enterprise" ? "Contact sales" : "Get started"}
                  </MagneticButton>
                </article>
              </StaggerItem>
            ))}
          </Stagger>

          <FadeIn delay={0.2}>
            <p className="mkt-pricing-footnote">
              AI credits are charged at generation time, not approval. Final rupee pricing confirmed
              during pilot onboarding.
            </p>
          </FadeIn>
        </div>
      </section>

      <CTASection />
      <MarketingFooter />
    </main>
  );
}
