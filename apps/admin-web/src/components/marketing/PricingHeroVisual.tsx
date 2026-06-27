"use client";

import { motion, useReducedMotion } from "framer-motion";
import { Check } from "lucide-react";

const PREVIEW_PLANS = [
  {
    name: "Pilot",
    price: "Free",
    offset: "mkt-plan-preview--back",
    rotate: -4,
    floatDelay: 0,
    duration: 5.5,
  },
  {
    name: "Pro",
    price: "₹—",
    offset: "mkt-plan-preview--front",
    featured: true,
    rotate: 0,
    floatDelay: 0.4,
    duration: 6,
  },
  {
    name: "Enterprise",
    price: "Custom",
    offset: "mkt-plan-preview--mid",
    rotate: 4,
    floatDelay: 0.8,
    duration: 5,
  },
];

const EASE = [0.22, 1, 0.36, 1] as const;

export function PricingHeroVisual() {
  const reduce = useReducedMotion();

  return (
    <div className="mkt-hero-scene mkt-hero-scene--pricing">
      <motion.div
        className="mkt-pricing-visual"
        animate={reduce ? undefined : { y: [0, -5, 0] }}
        transition={{ duration: 6.5, repeat: Infinity, ease: "easeInOut" }}
      >
        {PREVIEW_PLANS.map((plan, i) => (
          <motion.div
            key={plan.name}
            className={`mkt-plan-preview mkt-glass ${plan.offset}${plan.featured ? " mkt-plan-preview--featured" : ""}`}
            initial={
              reduce
                ? false
                : { opacity: 0, y: 36, rotate: plan.featured ? 0 : plan.rotate }
            }
            animate={
              reduce
                ? { opacity: 1, y: 0, rotate: plan.featured ? 0 : plan.rotate * 0.75 }
                : {
                    opacity: 1,
                    y: [0, plan.featured ? -8 : -5, 0],
                    rotate: plan.featured ? 0 : plan.rotate * 0.75,
                  }
            }
            transition={{
              opacity: { duration: 0.75, delay: 0.55 + i * 0.1, ease: EASE },
              rotate: { duration: 0.75, delay: 0.55 + i * 0.1, ease: EASE },
              y: {
                duration: plan.duration,
                repeat: Infinity,
                ease: "easeInOut",
                delay: plan.floatDelay,
              },
            }}
          >
            {plan.featured && <span className="mkt-plan-preview-badge">Most popular</span>}
            <div className="mkt-plan-preview-name">{plan.name}</div>
            <div className="mkt-plan-preview-price">{plan.price}</div>
            <div className="mkt-neural-line mkt-neural-line--compact" />
            <ul className="mkt-plan-preview-features">
              {["AI papers", "Mastery", "Portals"].slice(0, plan.featured ? 3 : 2).map((f) => (
                <li key={f}>
                  <Check size={12} aria-hidden />
                  {f}
                </li>
              ))}
            </ul>
          </motion.div>
        ))}
      </motion.div>
    </div>
  );
}
