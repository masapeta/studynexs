"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { animate, useInView, useReducedMotion } from "framer-motion";

type Props = {
  value: string;
  label: string;
};

function parseStat(value: string): { num: number; prefix: string; suffix: string } | null {
  const match = value.match(/^([^0-9.-]*)([0-9.]+)(.*)$/);
  if (!match) return null;
  return { prefix: match[1], num: parseFloat(match[2]), suffix: match[3] };
}

function formatStat(num: number, prefix: string, suffix: string, target: number): string {
  const useDecimal = target % 1 !== 0;
  const formatted = useDecimal ? num.toFixed(1) : String(Math.round(num));
  return `${prefix}${formatted}${suffix}`;
}

export function AnimatedStat({ value, label }: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true, margin: "-40px" });
  const reduce = useReducedMotion();
  const animated = useRef(false);

  const parsed = useMemo(() => parseStat(value), [value]);
  const num = parsed?.num ?? null;
  const prefix = parsed?.prefix ?? "";
  const suffix = parsed?.suffix ?? "";

  const [display, setDisplay] = useState(value);

  useEffect(() => {
    if (reduce || num === null) {
      setDisplay(value);
      return;
    }

    if (!inView || animated.current) return;

    animated.current = true;
    const controls = animate(0, num, {
      duration: 1.4,
      ease: [0.22, 1, 0.36, 1],
      onUpdate: (latest) => {
        setDisplay(formatStat(latest, prefix, suffix, num));
      },
      onComplete: () => {
        setDisplay(value);
      },
    });

    return () => controls.stop();
  }, [inView, reduce, num, prefix, suffix, value]);

  return (
    <div ref={ref} className="mkt-stat mkt-glass mkt-stat--animated">
      <div className="mkt-stat-value">{display}</div>
      <div className="mkt-stat-label">{label}</div>
      <div className="mkt-stat-glow" aria-hidden />
    </div>
  );
}
