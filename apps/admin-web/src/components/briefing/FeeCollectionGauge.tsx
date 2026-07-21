"use client";

import { useEffect, useId, useRef, useState } from "react";
import { inr } from "@/lib/format";

type Props = {
  /** Collection rate 0–100 (collected ÷ target). */
  rate: number;
  collected: number;
  pending: number;
  size?: number;
};

/** Visible arc: gap at bottom, sweeps clockwise (~270°). */
const ARC_START_DEG = 135;
const ARC_SWEEP_DEG = 270;

function degToRad(deg: number) {
  return (deg * Math.PI) / 180;
}

function pointOnCircle(cx: number, cy: number, r: number, deg: number) {
  const rad = degToRad(deg);
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
}

function arcPath(cx: number, cy: number, r: number, startDeg: number, endDeg: number) {
  if (endDeg <= startDeg + 0.01) return "";
  const start = pointOnCircle(cx, cy, r, startDeg);
  const end = pointOnCircle(cx, cy, r, endDeg);
  const sweep = endDeg - startDeg;
  const largeArc = sweep > 180 ? 1 : 0;
  return `M ${start.x.toFixed(2)} ${start.y.toFixed(2)} A ${r} ${r} 0 ${largeArc} 1 ${end.x.toFixed(2)} ${end.y.toFixed(2)}`;
}

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

function useAnimatedRate(target: number, reducedMotion: boolean) {
  const [value, setValue] = useState(reducedMotion ? target : 0);
  const frameRef = useRef<number | null>(null);

  useEffect(() => {
    if (reducedMotion) {
      setValue(target);
      return;
    }

    const from = 0;
    const duration = 720;
    const start = performance.now();

    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - (1 - t) ** 3;
      setValue(from + (target - from) * eased);
      if (t < 1) frameRef.current = requestAnimationFrame(tick);
    };

    frameRef.current = requestAnimationFrame(tick);
    return () => {
      if (frameRef.current != null) cancelAnimationFrame(frameRef.current);
    };
  }, [target, reducedMotion]);

  return value;
}

export function FeeCollectionGauge({ rate, collected, pending, size = 168 }: Props) {
  const labelId = useId();
  const reducedMotion = usePrefersReducedMotion();
  const clampedTarget = Math.max(0, Math.min(100, rate));
  const animatedRate = useAnimatedRate(clampedTarget, reducedMotion);

  const stroke = 11;
  const cx = size / 2;
  const cy = size / 2;
  const r = (size - stroke * 2) / 2;

  const progressEnd = ARC_START_DEG + ARC_SWEEP_DEG * (animatedRate / 100);
  const trackEnd = ARC_START_DEG + ARC_SWEEP_DEG;
  const trackPath = arcPath(cx, cy, r, ARC_START_DEG, trackEnd);
  const progressPath = arcPath(cx, cy, r, ARC_START_DEG, progressEnd);
  const knob =
    animatedRate > 0.5
      ? pointOnCircle(cx, cy, r, progressEnd)
      : null;

  const total = collected + pending;
  const subtitle =
    total > 0 ? `${inr(collected)} collected` : "No fee records yet";

  return (
    <div className="fee-collection-gauge" style={{ width: size, height: size }}>
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        role="img"
        aria-labelledby={labelId}
        className="fee-collection-gauge__svg"
      >
        <title id={labelId}>
          Fee collection {Math.round(clampedTarget)} percent — {inr(collected)} collected,{" "}
          {inr(pending)} outstanding
        </title>

        <path
          d={trackPath}
          className="fee-collection-gauge__track"
          fill="none"
          strokeWidth={stroke}
          strokeLinecap="round"
        />

        {progressPath ? (
          <path
            d={progressPath}
            className="fee-collection-gauge__progress"
            fill="none"
            strokeWidth={stroke}
            strokeLinecap="round"
          />
        ) : null}

        {knob ? (
          <circle
            cx={knob.x}
            cy={knob.y}
            r={stroke * 0.42}
            className="fee-collection-gauge__knob"
          />
        ) : null}
      </svg>

      <div className="fee-collection-gauge__center" aria-hidden>
        <span className="fee-collection-gauge__value">{Math.round(clampedTarget)}%</span>
        <span className="fee-collection-gauge__subtitle">{subtitle}</span>
      </div>
    </div>
  );
}
