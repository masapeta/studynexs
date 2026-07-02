"use client";

import { motion, useReducedMotion } from "framer-motion";
import { Sparkles } from "lucide-react";
import { HOME_HERO } from "@/lib/noustriks-content";
import { HeroDashboardScene } from "./HeroDashboardScene";
import { MagneticButton } from "./Motion";

/** Approved StudyNexs hero — school OS headline + dashboard scene. Used on /products/studynexs. */
export function StudyNexsHeroSection() {
  const reduce = useReducedMotion();

  return (
    <section className="mkt-hero" aria-labelledby="studynexs-hero-heading">
      <div className="mkt-hero-grid">
        <div className="mkt-hero-copy">
          <motion.div
            className="mkt-eyebrow mkt-glass"
            initial={reduce ? false : { opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.15 }}
          >
            <Sparkles size={14} aria-hidden />
            AI-Powered School OS
          </motion.div>

          <motion.h1
            id="studynexs-hero-heading"
            className="mkt-h1 mkt-h1--hero"
            initial={reduce ? false : { opacity: 0, y: 32, filter: "blur(10px)" }}
            animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
            transition={{ duration: 0.85, delay: 0.25, ease: [0.22, 1, 0.36, 1] }}
          >
            The world&apos;s most advanced
            <br />
            <span className="mkt-gradient-text">school operating system</span>
          </motion.h1>

          <motion.p
            className="mkt-lead mkt-lead--hero"
            initial={reduce ? false : { opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.45 }}
          >
            Immersive intelligence for principals, teachers, students, and parents — one glass
            platform where AI assists, humans approve, and every school stays in control.
          </motion.p>

          <motion.div
            className="mkt-hero-actions mkt-hero-actions--left"
            initial={reduce ? false : { opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.65, delay: 0.6 }}
          >
            <MagneticButton href="/login?portal=staff" className="mkt-btn mkt-btn--primary mkt-btn--lg">
              Start free pilot
            </MagneticButton>
            <MagneticButton href="/platform" className="mkt-btn mkt-btn--glass mkt-btn--lg">
              Explore platform
            </MagneticButton>
          </motion.div>
        </div>

        <motion.div
          className="mkt-hero-visual"
          initial={reduce ? false : { opacity: 0, y: 48, rotateX: 8 }}
          animate={{ opacity: 1, y: 0, rotateX: 4 }}
          transition={{ duration: 1, delay: 0.75, ease: [0.22, 1, 0.36, 1] }}
        >
          <HeroDashboardScene />
        </motion.div>
      </div>
    </section>
  );
}
