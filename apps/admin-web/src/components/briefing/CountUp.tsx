"use client";

import { useEffect, useRef, useState } from "react";

function usePrefersReducedMotion() {
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    const sync = () => setReduced(mq.matches);
    sync();
    mq.addEventListener("change", sync);
    return () => mq.removeEventListener("change", sync);
  }, []);
  return reduced;
}

type Props = {
  /** Final value to count to. */
  value: number;
  /** Formats the in-flight value (e.g. inr, percentage). Defaults to rounded int. */
  format?: (n: number) => string;
  /** Animation length in ms. */
  duration?: number;
};

/**
 * Animated number that counts up from 0 on mount.
 * Renders the final value immediately when reduced motion is preferred.
 */
export function CountUp({ value, format, duration = 700 }: Props) {
  const reduced = usePrefersReducedMotion();
  const [animated, setAnimated] = useState(0);
  const frameRef = useRef<number | null>(null);

  useEffect(() => {
    if (reduced || !Number.isFinite(value)) return;
    const start = performance.now();
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - (1 - t) ** 3;
      // setState only inside the RAF callback (async) — never in the effect body.
      setAnimated(value * eased);
      if (t < 1) frameRef.current = requestAnimationFrame(tick);
    };
    frameRef.current = requestAnimationFrame(tick);
    return () => {
      if (frameRef.current != null) cancelAnimationFrame(frameRef.current);
    };
  }, [value, duration, reduced]);

  // Reduced motion (or non-numeric input) renders the final value directly.
  const shown = reduced || !Number.isFinite(value) ? value : animated;
  return <>{format ? format(shown) : Math.round(shown).toLocaleString("en-IN")}</>;
}
