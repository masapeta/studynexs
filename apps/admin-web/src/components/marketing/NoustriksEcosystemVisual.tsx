"use client";

import { motion, useReducedMotion } from "framer-motion";
import { GraduationCap, Layers, Network } from "lucide-react";
import { MEMORY_FABRIC, STUDYNEXS } from "@/lib/noustriks-content";

/** Homepage visual — flagship products as floating glass surfaces (not a single-product dashboard). */
export function NoustriksEcosystemVisual() {
  const reduce = useReducedMotion();

  return (
    <div className="mkt-ecosystem-visual" aria-hidden>
      <motion.div
        className="mkt-ecosystem-core mkt-glass-strong"
        animate={reduce ? undefined : { y: [0, -8, 0] }}
        transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
      >
        <Network size={22} strokeWidth={1.75} />
        <div>
          <div className="mkt-ecosystem-core-title">Noustriks</div>
          <div className="mkt-ecosystem-core-sub">Intelligent platforms</div>
        </div>
      </motion.div>

      <motion.div
        className="mkt-ecosystem-card mkt-ecosystem-card--edu mkt-glass"
        animate={reduce ? undefined : { y: [0, -5, 0] }}
        transition={{ duration: 6, repeat: Infinity, ease: "easeInOut", delay: 0.5 }}
      >
        <GraduationCap size={16} aria-hidden />
        <div>
          <strong>{STUDYNEXS.name}</strong>
          <span>AI School OS</span>
        </div>
      </motion.div>

      <motion.div
        className="mkt-ecosystem-card mkt-ecosystem-card--ent mkt-glass"
        animate={reduce ? undefined : { y: [0, -6, 0] }}
        transition={{ duration: 7, repeat: Infinity, ease: "easeInOut", delay: 1.2 }}
      >
        <Layers size={16} aria-hidden />
        <div>
          <strong>{MEMORY_FABRIC.name}</strong>
          <span>Enterprise memory</span>
        </div>
      </motion.div>

      <div className="mkt-ecosystem-orbit mkt-ecosystem-orbit--1" />
      <div className="mkt-ecosystem-orbit mkt-ecosystem-orbit--2" />

      <div className="mkt-ecosystem-chips">
        <span className="mkt-ecosystem-chip mkt-glass">Agentic AI</span>
        <span className="mkt-ecosystem-chip mkt-glass">Persistent memory</span>
        <span className="mkt-ecosystem-chip mkt-glass">Human-approved</span>
      </div>
    </div>
  );
}
