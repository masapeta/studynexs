"use client";

import { useEffect, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";

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
  useBodyScrollLock(open);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!open || !mounted) return null;

  return createPortal(
    <div
      className="gw-modal-backdrop"
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
