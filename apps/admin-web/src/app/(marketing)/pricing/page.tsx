"use client";

import { Check } from "lucide-react";
import { FadeIn, MagneticButton, Stagger, StaggerItem } from "@/components/marketing/Motion";
import { MarketingFooter } from "@/components/marketing/Sections";

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
      <section className="mkt-hero" style={{ minHeight: "70dvh" }} aria-labelledby="pricing-heading">
        <FadeIn>
          <div className="mkt-eyebrow mkt-glass" style={{ marginInline: "auto" }}>
            Pricing
          </div>
          <h1 id="pricing-heading" className="mkt-h1" style={{ fontSize: "clamp(2.5rem, 6vw, 4rem)" }}>
            Simple plans.
            <br />
            <span className="mkt-gradient-text">Serious schools.</span>
          </h1>
          <p className="mkt-lead" style={{ marginInline: "auto", marginTop: "1.25rem" }}>
            Start with a pilot. Scale when your staff and families are ready. No surprise AI bills —
            credits are metered and visible.
          </p>
        </FadeIn>
      </section>

      <section className="mkt-section" style={{ paddingTop: 0 }} aria-label="Pricing plans">
        <div className="mkt-container">
          <Stagger className="mkt-pricing-grid">
            {PLANS.map((plan) => (
              <StaggerItem key={plan.name}>
                <article
                  className={`mkt-card mkt-glass mkt-pricing-card${
                    plan.featured ? " mkt-pricing-card--featured" : ""
                  }`}
                  style={{ height: "100%", display: "flex", flexDirection: "column" }}
                >
                  {plan.featured && (
                    <span
                      className="mkt-eyebrow mkt-glass"
                      style={{ marginBottom: "1rem", alignSelf: "flex-start" }}
                    >
                      Most popular
                    </span>
                  )}
                  <h2 className="mkt-h3">{plan.name}</h2>
                  <div className="mkt-price" style={{ marginTop: "1rem" }}>
                    {plan.price}
                    {plan.period && <span> / {plan.period}</span>}
                  </div>
                  <p style={{ marginTop: "0.75rem", fontSize: "0.88rem", color: "var(--mkt-gray-500)" }}>
                    {plan.desc}
                  </p>
                  <ul style={{ listStyle: "none", padding: 0, margin: "1.5rem 0", flex: 1 }}>
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
            <p
              style={{
                textAlign: "center",
                marginTop: "2.5rem",
                fontSize: "0.85rem",
                color: "var(--mkt-gray-500)",
              }}
            >
              AI credits are charged at generation time, not approval. Final rupee pricing confirmed
              during pilot onboarding.
            </p>
          </FadeIn>
        </div>
      </section>

      <MarketingFooter />
    </main>
  );
}
