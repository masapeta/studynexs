"use client";

import { useEffect, useState } from "react";
import { FlaskConical } from "lucide-react";
import { isDemoMode } from "@/lib/demo-mode";

const STORAGE_KEY = "sn-demo-banner-dismissed";
const AUTO_HIDE_MS = 6000;
const FADE_MS = 320;

type Props = {
  variant?: "app" | "marketing";
};

function shouldShowBanner(): boolean {
  if (!isDemoMode()) return false;
  if (typeof window === "undefined") return false;
  try {
    return !sessionStorage.getItem(STORAGE_KEY);
  } catch {
    return true;
  }
}

export function DemoDataBanner({ variant = "app" }: Props) {
  const [visible, setVisible] = useState(shouldShowBanner);
  const [hiding, setHiding] = useState(false);

  useEffect(() => {
    if (!visible) return;

    const hideTimer = window.setTimeout(() => setHiding(true), AUTO_HIDE_MS);
    return () => window.clearTimeout(hideTimer);
  }, [visible]);

  useEffect(() => {
    if (!hiding) return;

    const removeTimer = window.setTimeout(() => {
      try {
        sessionStorage.setItem(STORAGE_KEY, "1");
      } catch {
        /* ignore quota / private mode */
      }
      setVisible(false);
    }, FADE_MS);

    return () => window.clearTimeout(removeTimer);
  }, [hiding]);

  if (!visible) return null;

  const className = [
    "sn-demo-banner",
    variant === "marketing" ? "sn-demo-banner--marketing" : "",
    hiding ? "sn-demo-banner--hiding" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={className} role="status" aria-live="polite">
      <FlaskConical size={14} aria-hidden className="sn-demo-banner__icon" />
      <span>
        <strong>Demo data</strong>
        {" — "}
        Sample school records for evaluation. Not live parent or student information.
      </span>
    </div>
  );
}
