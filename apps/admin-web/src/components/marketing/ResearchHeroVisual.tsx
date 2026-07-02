"use client";

import { motion, useReducedMotion } from "framer-motion";
import { Atom, Brain, FlaskConical, GitBranch, Shield, Sparkles } from "lucide-react";

const PROGRAMS = [
  { icon: Brain, label: "Agentic AI", status: "Active" },
  { icon: Sparkles, label: "Persistent memory", status: "Active" },
  { icon: Shield, label: "Responsible AI", status: "Review" },
  { icon: Atom, label: "Quantum hybrid", status: "Exploring" },
];

const FLOAT_STATS = [
  { icon: FlaskConical, label: "Research tracks", value: "7" },
  { icon: GitBranch, label: "In production", value: "2" },
];

/** Research hero — lab console + program pipeline (distinct from product mockups). */
export function ResearchHeroVisual() {
  const reduce = useReducedMotion();

  return (
    <div className="mkt-research-scene" aria-hidden>
      {FLOAT_STATS.map((stat, i) => (
        <motion.div
          key={stat.label}
          className={`mkt-research-float mkt-glass mkt-research-float--${i === 0 ? "tl" : "tr"}`}
          initial={reduce ? false : { opacity: 0, scale: 0.92 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.65, delay: 0.5 + i * 0.12 }}
        >
          <stat.icon size={14} strokeWidth={2} />
          <div>
            <div className="mkt-float-card-value">{stat.value}</div>
            <div className="mkt-float-card-label">{stat.label}</div>
          </div>
        </motion.div>
      ))}

      <motion.div
        className="mkt-research-window mkt-glass-strong"
        animate={reduce ? undefined : { y: [0, -7, 0] }}
        transition={{ duration: 7, repeat: Infinity, ease: "easeInOut" }}
      >
        <div className="mkt-research-window-bar">
          <span className="mkt-dash-dot" />
          <span className="mkt-dash-dot" />
          <span className="mkt-dash-dot" />
          <span className="mkt-research-window-title">
            <FlaskConical size={12} aria-hidden />
            Noustriks Research
          </span>
          <span className="mkt-dash-live">
            <span className="mkt-dash-live-pulse" />
            Live programs
          </span>
        </div>

        <div className="mkt-research-window-body">
          <div className="mkt-research-programs">
            {PROGRAMS.map((program, i) => (
              <motion.div
                key={program.label}
                className="mkt-research-program mkt-glass"
                initial={reduce ? false : { opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.5, delay: 0.35 + i * 0.08 }}
              >
                <program.icon size={14} aria-hidden />
                <span className="mkt-research-program-name">{program.label}</span>
                <span
                  className={`mkt-research-program-status mkt-research-program-status--${program.status.toLowerCase()}`}
                >
                  {program.status}
                </span>
              </motion.div>
            ))}
          </div>

          <div className="mkt-research-pipeline mkt-glass">
            <div className="mkt-dash-label">Research to product</div>
            <div className="mkt-research-pipeline-steps">
              <span>Lab</span>
              <span className="mkt-research-pipeline-arrow" aria-hidden>
                →
              </span>
              <span>Prototype</span>
              <span className="mkt-research-pipeline-arrow" aria-hidden>
                →
              </span>
              <span className="mkt-research-pipeline-step--active">Shipped</span>
            </div>
            <div className="mkt-research-pipeline-products">
              <span className="mkt-product-pill">StudyNexs</span>
              <span className="mkt-product-pill">Memory Fabric</span>
            </div>
          </div>
        </div>
      </motion.div>

      <motion.div
        className="mkt-research-insight mkt-glass"
        initial={reduce ? false : { opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, delay: 0.85 }}
      >
        <div className="mkt-research-insight-head">
          <Sparkles size={14} aria-hidden />
          <span>Latest insight</span>
        </div>
        <p>Human-in-the-loop patterns from school pilots now inform enterprise memory governance.</p>
      </motion.div>

      <div className="mkt-research-orbit mkt-research-orbit--1" />
      <div className="mkt-research-orbit mkt-research-orbit--2" />
    </div>
  );
}
