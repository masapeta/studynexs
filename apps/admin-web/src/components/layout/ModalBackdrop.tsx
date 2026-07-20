"use client";

import { useEffect, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { PLATFORM_MOTION_MS } from "@/lib/platform-motion";

let lockCount = 0;
let savedBodyOverflow = "";
let savedHtmlOverflow = "";

function lockBodyScroll() {
  if (lockCount === 0) {
    savedBodyOverflow = document.body.style.overflow;
    savedHtmlOverflow = document.documentElement.style.overflow;
    document.body.style.overflow = "hidden";
    document.documentElement.style.overflow = "hidden";
  }
  lockCount += 1;
}

function unlockBodyScroll() {
  lockCount = Math.max(0, lockCount - 1);
  if (lockCount === 0) {
    document.body.style.overflow = savedBodyOverflow;
    document.documentElement.style.overflow = savedHtmlOverflow;
  }
}

export function useBodyScrollLock(locked: boolean) {
  useEffect(() => {
    if (!locked) return;
    lockBodyScroll();
    return () => unlockBodyScroll();
  }, [locked]);
}

function handleBackdropWheel(e: React.WheelEvent<HTMLDivElement>) {
  const scrollable = (e.target as HTMLElement).closest(".gw-modal-body");
  if (scrollable instanceof HTMLElement) {
    const { scrollTop, scrollHeight, clientHeight } = scrollable;
    const delta = e.deltaY;
    if (delta < 0 && scrollTop > 0) return;
    if (delta > 0 && scrollTop + clientHeight < scrollHeight - 1) return;
  }
  e.preventDefault();
}

type Props = {
  open: boolean;
  onClose: () => void;
  disableClose?: boolean;
  labelledBy?: string;
  children: ReactNode;
};

export function ModalBackdrop({ open, onClose, disableClose, labelledBy, children }: Props) {
  const [mounted, setMounted] = useState(false);
  const [visible, setVisible] = useState(open);
  const [motionClass, setMotionClass] = useState<"enter" | "exit" | "">("");
  useBodyScrollLock(visible);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !disableClose) onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose, disableClose]);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (open) {
      setVisible(true);
      setMotionClass("");
      const frame = requestAnimationFrame(() => {
        requestAnimationFrame(() => setMotionClass("enter"));
      });
      return () => cancelAnimationFrame(frame);
    }

    if (!visible) return;

    setMotionClass("exit");
    const timer = window.setTimeout(() => {
      setVisible(false);
      setMotionClass("");
    }, PLATFORM_MOTION_MS.fast);

    return () => window.clearTimeout(timer);
  }, [open, visible]);

  if (!visible || !mounted) return null;

  const motionModifier =
    motionClass === "enter"
      ? "gw-modal-backdrop--enter"
      : motionClass === "exit"
        ? "gw-modal-backdrop--exit"
        : "";

  return createPortal(
    <div
      className={`gw-modal-backdrop ${motionModifier}`.trim()}
      role="dialog"
      aria-modal="true"
      aria-labelledby={labelledBy}
      onClick={() => !disableClose && onClose()}
      onWheel={handleBackdropWheel}
    >
      {children}
    </div>,
    document.body
  );
}
