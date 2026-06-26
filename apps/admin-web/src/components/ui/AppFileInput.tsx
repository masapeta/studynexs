"use client";

import { useId, useRef } from "react";
import { Upload, X } from "lucide-react";

type Props = {
  accept?: string;
  disabled?: boolean;
  uploading?: boolean;
  placeholder?: string;
  file?: File | null;
  onChange: (file: File | null) => void;
  variant?: "compact" | "field";
  className?: string;
  style?: React.CSSProperties;
  "aria-label"?: string;
  id?: string;
};

export function AppFileInput({
  accept,
  disabled = false,
  uploading = false,
  placeholder = "Choose file…",
  file = null,
  onChange,
  variant = "compact",
  className = "",
  style,
  "aria-label": ariaLabel,
  id,
}: Props) {
  const autoId = useId();
  const inputRef = useRef<HTMLInputElement>(null);
  const inputId = id || autoId;
  const busy = disabled || uploading;

  function pick(next: File | null) {
    onChange(next);
    if (inputRef.current) inputRef.current.value = "";
  }

  return (
    <div
      className={`app-file-input app-file-input--${variant}${busy ? " app-file-input--disabled" : ""}${className ? ` ${className}` : ""}`}
      style={style}
    >
      <label
        htmlFor={inputId}
        className="app-file-input-trigger"
        aria-label={ariaLabel}
      >
        <Upload size={variant === "compact" ? 15 : 16} className="app-file-input-icon" aria-hidden />
        <span className="app-file-input-text">
          {uploading ? "Uploading…" : file?.name || placeholder}
        </span>
        {file && !busy && (
          <button
            type="button"
            className="app-file-input-clear"
            aria-label="Remove file"
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              pick(null);
            }}
          >
            <X size={14} aria-hidden />
          </button>
        )}
      </label>
      <input
        ref={inputRef}
        id={inputId}
        type="file"
        accept={accept}
        disabled={busy}
        className="app-file-input-native"
        onChange={(e) => {
          const next = e.target.files?.[0] || null;
          if (next) onChange(next);
          e.target.value = "";
        }}
      />
    </div>
  );
}
