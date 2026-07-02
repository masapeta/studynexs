"use client";

import { motion, useReducedMotion } from "framer-motion";
import { BookOpen, ClipboardCheck, FileText, ScanLine } from "lucide-react";

const TABS = ["Exams", "Mastery", "Lesson Plans", "Reports"];

const FLOAT_STATS = [
  { icon: FileText, label: "Papers approved", value: "6", pos: "mkt-product-float--tl" },
  { icon: ScanLine, label: "Sheets to review", value: "28", pos: "mkt-product-float--tr" },
  { icon: BookOpen, label: "Classes today", value: "12", pos: "mkt-product-float--bl" },
];

/** StudyNexs-specific product visual — teaching hub + exam loop (distinct from homepage hero). */
export function StudyNexsProductVisual() {
  const reduce = useReducedMotion();

  return (
    <div className="mkt-product-scene" aria-hidden>
      {FLOAT_STATS.map((card, i) => (
        <motion.div
          key={card.label}
          className={`mkt-product-float mkt-glass ${card.pos}`}
          initial={reduce ? false : { opacity: 0, scale: 0.92 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.65, delay: i * 0.1 }}
        >
          <card.icon size={14} strokeWidth={2} />
          <div>
            <div className="mkt-float-card-value">{card.value}</div>
            <div className="mkt-float-card-label">{card.label}</div>
          </div>
        </motion.div>
      ))}

      <motion.div
        className="mkt-product-window mkt-glass-strong"
        animate={reduce ? undefined : { y: [0, -6, 0] }}
        transition={{ duration: 7, repeat: Infinity, ease: "easeInOut" }}
      >
        <div className="mkt-product-window-bar">
          <span className="mkt-dash-dot" />
          <span className="mkt-dash-dot" />
          <span className="mkt-dash-dot" />
          <span className="mkt-product-window-title">Teaching Hub · Class 10</span>
        </div>

        <div className="mkt-product-tabs">
          {TABS.map((tab, i) => (
            <span key={tab} className={`mkt-product-tab${i === 0 ? " mkt-product-tab--active" : ""}`}>
              {tab}
            </span>
          ))}
        </div>

        <div className="mkt-product-window-body">
          <div className="mkt-product-panel">
            <div className="mkt-dash-label">Unit test · Maths</div>
            <div className="mkt-product-panel-row">
              <span>33 questions</span>
              <span className="mkt-product-pill mkt-product-pill--ok">Approved</span>
            </div>
            <div className="mkt-neural-line mkt-neural-line--compact" />
            <div className="mkt-product-panel-row">
              <span>Answer sheets</span>
              <span className="mkt-product-pill">28 pending</span>
            </div>
          </div>

          <div className="mkt-product-panel mkt-product-panel--accent">
            <div className="mkt-dash-label">Topic mastery heatmap</div>
            <div className="mkt-product-heatmap">
              {["Algebra", "Geometry", "Trig", "Stats"].map((topic, i) => (
                <div key={topic} className="mkt-product-heat-row">
                  <span>{topic}</span>
                  <span
                    className="mkt-product-heat-bar"
                    style={{ width: `${[72, 58, 41, 67][i]}%` }}
                  />
                </div>
              ))}
            </div>
          </div>
        </div>
      </motion.div>

      <motion.div
        className="mkt-product-approve mkt-glass"
        initial={reduce ? false : { opacity: 0, x: 16 }}
        whileInView={{ opacity: 1, x: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.7, delay: 0.25 }}
      >
        <div className="mkt-product-approve-head">
          <ClipboardCheck size={16} aria-hidden />
          <span>Human-in-the-loop</span>
        </div>
        <p>AI suggested 26/28 objective marks. Teacher reviews subjective responses before publish.</p>
        <div className="mkt-product-approve-actions">
          <span className="mkt-product-pill mkt-product-pill--ok">Approve batch</span>
          <span className="mkt-product-pill">Edit marks</span>
        </div>
      </motion.div>
    </div>
  );
}
