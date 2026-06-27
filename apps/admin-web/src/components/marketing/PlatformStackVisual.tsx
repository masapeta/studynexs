"use client";

import type { CSSProperties } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { Brain, GraduationCap, Shield } from "lucide-react";

const LAYERS = [
  {
    label: "AI Intelligence Layer",
    badge: "Human-approved",
    items: ["Papers", "Mastery", "Remarks"],
    icon: Brain,
    accent: "rgba(59, 130, 246, 0.14)",
    floatDelay: 0,
  },
  {
    label: "School Operations",
    badge: "Unified SMS",
    items: ["Academics", "Finance", "Family"],
    icon: GraduationCap,
    accent: "rgba(14, 165, 233, 0.1)",
    floatDelay: 0.8,
  },
  {
    label: "Secure Data Core",
    badge: "Tenant-isolated",
    items: ["RBAC", "Audit logs", "DPDP"],
    icon: Shield,
    accent: "rgba(99, 102, 241, 0.1)",
    floatDelay: 1.6,
  },
];

const EASE = [0.22, 1, 0.36, 1] as const;

export function PlatformStackVisual() {
  const reduce = useReducedMotion();

  return (
    <div className="mkt-hero-scene mkt-hero-scene--stack">
      <motion.div
        className="mkt-stack-visual"
        animate={reduce ? undefined : { y: [0, -6, 0] }}
        transition={{ duration: 7, repeat: Infinity, ease: "easeInOut" }}
      >
        {LAYERS.map((layer, i) => (
          <motion.div
            key={layer.label}
            className="mkt-stack-layer mkt-glass"
            style={{ "--mkt-layer-accent": layer.accent } as CSSProperties}
            initial={reduce ? false : { opacity: 0, y: 28, scale: 0.96 }}
            animate={
              reduce
                ? { opacity: 1, y: 0, scale: 1 }
                : { opacity: 1, y: [0, i % 2 === 0 ? -4 : -6, 0], scale: 1 }
            }
            transition={{
              opacity: { duration: 0.7, delay: 0.55 + i * 0.12, ease: EASE },
              y: {
                duration: 5 + i,
                repeat: Infinity,
                ease: "easeInOut",
                delay: layer.floatDelay,
              },
              scale: { duration: 0.7, delay: 0.55 + i * 0.12, ease: EASE },
            }}
          >
            <div className="mkt-stack-layer-head">
              <span className="mkt-stack-layer-icon">
                <layer.icon size={16} strokeWidth={2} />
              </span>
              <div>
                <div className="mkt-stack-layer-title">{layer.label}</div>
                <div className="mkt-stack-layer-badge">{layer.badge}</div>
              </div>
            </div>
            <div className="mkt-neural-line" />
            <div className="mkt-stack-layer-tags">
              {layer.items.map((item) => (
                <span key={item} className="mkt-stack-tag">
                  {item}
                </span>
              ))}
            </div>
          </motion.div>
        ))}
        <div className="mkt-stack-glow" />
      </motion.div>
    </div>
  );
}
