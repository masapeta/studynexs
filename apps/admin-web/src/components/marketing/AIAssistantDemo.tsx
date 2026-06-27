"use client";

import { useEffect, useState } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { Bot, Sparkles } from "lucide-react";

const MESSAGES = [
  { role: "user" as const, text: "Draft a Class 10 Maths paper — 100 marks, SSC pattern." },
  { role: "ai" as const, text: "Done. 4 sections, 33 questions, difficulty mix applied. Ready for your review." },
  { role: "user" as const, text: "Flag students weak in quadratic equations." },
  { role: "ai" as const, text: "7 students below class average. Parent narratives drafted — awaiting approval." },
];

export function AIAssistantDemo() {
  const reduce = useReducedMotion();
  const [step, setStep] = useState(0);

  useEffect(() => {
    if (reduce) return;
    const id = window.setInterval(() => {
      setStep((s) => (s + 1) % (MESSAGES.length + 1));
    }, 3200);
    return () => window.clearInterval(id);
  }, [reduce]);

  const visible = reduce ? MESSAGES : MESSAGES.slice(0, Math.min(step, MESSAGES.length));

  return (
    <motion.div
      className="mkt-ai-assistant mkt-glass-strong"
      initial={reduce ? false : { opacity: 0, y: 24, scale: 0.96 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.9, delay: 1.1, ease: [0.22, 1, 0.36, 1] }}
      aria-label="AI assistant preview"
    >
      <div className="mkt-ai-assistant-head">
        <span className="mkt-ai-assistant-avatar">
          <Bot size={16} aria-hidden />
        </span>
        <div>
          <div className="mkt-ai-assistant-title">StudyNexs AI</div>
          <div className="mkt-ai-assistant-status">
            <Sparkles size={10} aria-hidden /> School intelligence · Human-approved
          </div>
        </div>
      </div>
      <div className="mkt-ai-assistant-thread">
        {visible.map((m, i) => (
          <div
            key={`${m.role}-${i}`}
            className={`mkt-ai-bubble mkt-ai-bubble--${m.role}`}
          >
            {m.text}
          </div>
        ))}
        {!reduce && step < MESSAGES.length && (
          <div className="mkt-ai-typing" aria-hidden>
            <span />
            <span />
            <span />
          </div>
        )}
      </div>
    </motion.div>
  );
}
