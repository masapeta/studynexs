"use client";

import { ReactNode } from "react";
import { motion, useReducedMotion } from "framer-motion";

type Props = {
  id: string;
  eyebrow: ReactNode;
  title: ReactNode;
  lead: string;
  actions?: ReactNode;
  visual?: ReactNode;
  compact?: boolean;
};

export function MarketingPageHero({ id, eyebrow, title, lead, actions, visual, compact }: Props) {
  const reduce = useReducedMotion();

  return (
    <section
      className={`mkt-hero${compact ? " mkt-hero--compact" : ""}`}
      aria-labelledby={id}
    >
      <div className="mkt-hero-grid">
        <div className="mkt-hero-copy">
          <motion.div
            className="mkt-eyebrow mkt-glass"
            initial={reduce ? false : { opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.1 }}
          >
            {eyebrow}
          </motion.div>

          <motion.h1
            id={id}
            className="mkt-h1 mkt-h1--hero"
            initial={reduce ? false : { opacity: 0, y: 28, filter: "blur(8px)" }}
            animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
            transition={{ duration: 0.8, delay: 0.2, ease: [0.22, 1, 0.36, 1] }}
          >
            {title}
          </motion.h1>

          <motion.p
            className="mkt-lead mkt-lead--hero"
            initial={reduce ? false : { opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.65, delay: 0.35 }}
          >
            {lead}
          </motion.p>

          {actions && (
            <motion.div
              className="mkt-hero-actions mkt-hero-actions--left"
              initial={reduce ? false : { opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.5 }}
            >
              {actions}
            </motion.div>
          )}
        </div>

        {visual && (
          <motion.div
            className="mkt-hero-visual"
            initial={reduce ? false : { opacity: 0, y: 48, rotateX: 8 }}
            animate={{ opacity: 1, y: 0, rotateX: 4 }}
            transition={{ duration: 1, delay: 0.55, ease: [0.22, 1, 0.36, 1] }}
          >
            {visual}
          </motion.div>
        )}
      </div>
    </section>
  );
}
