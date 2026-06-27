"use client";

import { motion, useReducedMotion } from "framer-motion";
import { Brain, TrendingUp, Zap } from "lucide-react";
import { AIAssistantDemo } from "./AIAssistantDemo";

const FLOAT_CARDS = [
  { icon: TrendingUp, label: "Attendance", value: "96.2%", pos: "mkt-float-card--tl" },
  { icon: Zap, label: "AI papers today", value: "14", pos: "mkt-float-card--tr" },
  { icon: Brain, label: "Mastery flags", value: "7", pos: "mkt-float-card--bl" },
];

function FloatingCard({
  icon: Icon,
  label,
  value,
  pos,
  delay,
}: (typeof FLOAT_CARDS)[0] & { delay: number }) {
  const reduce = useReducedMotion();
  return (
    <motion.div
      className={`mkt-float-card mkt-glass ${pos}`}
      initial={reduce ? false : { opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.7, delay, ease: [0.22, 1, 0.36, 1] }}
      aria-hidden
    >
      <Icon size={14} strokeWidth={2} />
      <div>
        <div className="mkt-float-card-value">{value}</div>
        <div className="mkt-float-card-label">{label}</div>
      </div>
    </motion.div>
  );
}

/** Shared landing-style hero: floating stats, dashboard preview, AI assistant. */
export function HeroDashboardScene() {
  const reduce = useReducedMotion();

  return (
    <div className="mkt-hero-scene">
      {FLOAT_CARDS.map((c, i) => (
        <FloatingCard key={c.label} {...c} delay={0.6 + i * 0.15} />
      ))}
      <motion.div
        className="mkt-dashboard-preview"
        animate={reduce ? undefined : { y: [0, -8, 0] }}
        transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
      >
        <div className="mkt-dashboard-inner">
          <div className="mkt-dash-bar">
            <span className="mkt-dash-dot" />
            <span className="mkt-dash-dot" />
            <span className="mkt-dash-dot" />
            <span className="mkt-dash-live">
              <span className="mkt-dash-live-pulse" />
              AI Command Center
            </span>
          </div>
          <div className="mkt-dash-body">
            <div className="mkt-dash-panel">
              <div className="mkt-dash-label">Mastery alerts</div>
              <div className="mkt-dash-stat">12</div>
              <div className="mkt-neural-line" />
              <div className="mkt-dash-hint">3 topics need review</div>
            </div>
            <div className="mkt-dash-panel mkt-dash-panel--hero">
              <div className="mkt-dash-label">AI papers generated</div>
              <div className="mkt-dash-stat">847</div>
              <div className="mkt-neural-line" />
              <div className="mkt-dash-tags">
                {["Algebra", "Physics", "English"].map((t) => (
                  <span key={t} className="mkt-dash-tag">
                    {t}
                  </span>
                ))}
              </div>
            </div>
            <div className="mkt-dash-panel">
              <div className="mkt-dash-label">Parent engagement</div>
              <div className="mkt-dash-stat">94%</div>
              <div className="mkt-neural-line" />
              <div className="mkt-dash-hint">Notices read this week</div>
            </div>
          </div>
        </div>
      </motion.div>
      <AIAssistantDemo />
    </div>
  );
}
