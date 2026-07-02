"use client";

import { motion, useReducedMotion } from "framer-motion";
import { Building2 } from "lucide-react";
import { HOME_HERO } from "@/lib/noustriks-content";
import { NoustriksEcosystemVisual } from "./NoustriksEcosystemVisual";
import { MagneticButton } from "./Motion";

/** Company-level homepage hero — what Noustriks builds across products. */
export function HomeHeroSection() {
  const reduce = useReducedMotion();

  return (
    <section className="mkt-hero" aria-labelledby="home-hero-heading">
      <div className="mkt-hero-grid">
        <div className="mkt-hero-copy">
          <motion.div
            className="mkt-eyebrow mkt-glass"
            initial={reduce ? false : { opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.15 }}
          >
            <Building2 size={14} aria-hidden />
            {HOME_HERO.eyebrow}
          </motion.div>

          <motion.h1
            id="home-hero-heading"
            className="mkt-h1 mkt-h1--hero"
            initial={reduce ? false : { opacity: 0, y: 32, filter: "blur(10px)" }}
            animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
            transition={{ duration: 0.85, delay: 0.25, ease: [0.22, 1, 0.36, 1] }}
          >
            {HOME_HERO.titleLine1}
            <br />
            <span className="mkt-gradient-text">{HOME_HERO.titleAccent}</span>
          </motion.h1>

          <motion.p
            className="mkt-lead mkt-lead--hero"
            initial={reduce ? false : { opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.45 }}
          >
            {HOME_HERO.lead}
          </motion.p>

          <motion.div
            className="mkt-hero-actions mkt-hero-actions--left"
            initial={reduce ? false : { opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.65, delay: 0.55 }}
          >
            <MagneticButton href={HOME_HERO.primaryCta.href} className="mkt-btn mkt-btn--primary mkt-btn--lg">
              {HOME_HERO.primaryCta.label}
            </MagneticButton>
            <MagneticButton href={HOME_HERO.secondaryCta.href} className="mkt-btn mkt-btn--glass mkt-btn--lg">
              {HOME_HERO.secondaryCta.label}
            </MagneticButton>
          </motion.div>
        </div>

        <motion.div
          className="mkt-hero-visual"
          initial={reduce ? false : { opacity: 0, y: 48, rotateX: 8 }}
          animate={{ opacity: 1, y: 0, rotateX: 4 }}
          transition={{ duration: 1, delay: 0.65, ease: [0.22, 1, 0.36, 1] }}
        >
          <NoustriksEcosystemVisual />
        </motion.div>
      </div>
    </section>
  );
}
