"use client";

import { motion, useReducedMotion } from "framer-motion";
import { Bot, Database, Network, Share2, Users } from "lucide-react";

const NODES = [
  { id: "agents", icon: Bot, label: "AI Agents", x: "12%", y: "18%" },
  { id: "teams", icon: Users, label: "Teams", x: "78%", y: "22%" },
  { id: "apps", icon: Database, label: "Applications", x: "18%", y: "72%" },
  { id: "workflows", icon: Share2, label: "Workflows", x: "72%", y: "68%" },
];

/** Conceptual visualization: agents connected through a shared memory layer. */
export function MemoryFabricVisual() {
  const reduce = useReducedMotion();

  return (
    <div className="mkt-memory-visual" aria-hidden>
      <motion.div
        className="mkt-memory-core mkt-glass-strong"
        animate={reduce ? undefined : { y: [0, -6, 0] }}
        transition={{ duration: 7, repeat: Infinity, ease: "easeInOut" }}
      >
        <Network size={22} strokeWidth={1.75} />
        <div>
          <div className="mkt-memory-core-title">Memory Fabric</div>
          <div className="mkt-memory-core-sub">Shared intelligence layer</div>
        </div>
      </motion.div>

      <svg className="mkt-memory-lines" viewBox="0 0 400 280" preserveAspectRatio="none">
        <defs>
          <linearGradient id="mkt-mem-grad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="rgba(59, 130, 246, 0.35)" />
            <stop offset="100%" stopColor="rgba(99, 102, 241, 0.15)" />
          </linearGradient>
        </defs>
        {NODES.map((node) => (
          <motion.line
            key={node.id}
            x1="200"
            y1="140"
            x2={node.x === "12%" ? 48 : node.x === "78%" ? 352 : node.x === "18%" ? 72 : 328}
            y2={node.y === "18%" ? 50 : node.y === "22%" ? 62 : node.y === "72%" ? 202 : 190}
            stroke="url(#mkt-mem-grad)"
            strokeWidth="1.5"
            strokeDasharray="4 6"
            initial={reduce ? undefined : { pathLength: 0, opacity: 0.3 }}
            animate={reduce ? undefined : { pathLength: 1, opacity: 0.7 }}
            transition={{ duration: 1.2, delay: 0.3 }}
          />
        ))}
      </svg>

      {NODES.map((node, i) => (
        <motion.div
          key={node.id}
          className="mkt-memory-node mkt-glass"
          style={{ left: node.x, top: node.y }}
          initial={reduce ? false : { opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6, delay: 0.4 + i * 0.1 }}
        >
          <node.icon size={14} aria-hidden />
          <span>{node.label}</span>
        </motion.div>
      ))}

      <div className="mkt-memory-orbit mkt-memory-orbit--1" />
      <div className="mkt-memory-orbit mkt-memory-orbit--2" />
    </div>
  );
}
