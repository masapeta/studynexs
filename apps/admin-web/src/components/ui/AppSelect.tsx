"use client";

import { useEffect, useId, useRef, useState } from "react";
import { Check, ChevronDown } from "lucide-react";

export type AppSelectOption = {
  value: string;
  label: string;
  disabled?: boolean;
};

type Props = {
  value: string;
  onChange: (value: string) => void;
  options: AppSelectOption[];
  id?: string;
  name?: string;
  "aria-label"?: string;
  className?: string;
  variant?: "pill" | "field";
  disabled?: boolean;
  placeholder?: string;
  style?: React.CSSProperties;
};

export function AppSelect({
  value,
  onChange,
  options,
  id,
  name,
  "aria-label": ariaLabel,
  className = "",
  variant = "field",
  disabled = false,
  placeholder = "Select…",
  style,
}: Props) {
  const autoId = useId();
  const listId = `${id || autoId}-list`;
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const selected = options.find((o) => o.value === value);

  useEffect(() => {
    if (!open) return;
    const onPointerDown = (e: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  function pick(next: string) {
    onChange(next);
    setOpen(false);
  }

  return (
    <div
      ref={rootRef}
      className={`app-select app-select--${variant}${open ? " app-select--open" : ""}${className ? ` ${className}` : ""}`}
      style={style}
    >
      {name && <input type="hidden" name={name} value={value} readOnly />}
      <button
        id={id || autoId}
        type="button"
        className="app-select-trigger"
        aria-label={ariaLabel}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={listId}
        disabled={disabled}
        onClick={() => setOpen((v) => !v)}
      >
        <span className="app-select-value">{selected?.label || placeholder}</span>
        <ChevronDown size={14} className="app-select-chevron" aria-hidden />
      </button>
      {open && (
        <ul id={listId} className="app-select-menu" role="listbox" aria-label={ariaLabel}>
          {options.map((opt) => {
            const isSelected = opt.value === value;
            const isDisabled = Boolean(opt.disabled);
            return (
              <li
                key={opt.value || "__empty__"}
                role="option"
                aria-selected={isSelected}
                aria-disabled={isDisabled || undefined}
                className={`app-select-option${isSelected ? " selected" : ""}${isDisabled ? " disabled" : ""}`}
                onClick={() => {
                  if (!isDisabled) pick(opt.value);
                }}
                onKeyDown={(e) => {
                  if (isDisabled) return;
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    pick(opt.value);
                  }
                }}
                tabIndex={isDisabled ? -1 : 0}
              >
                <span>{opt.label}</span>
                {isSelected && <Check size={14} aria-hidden />}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
