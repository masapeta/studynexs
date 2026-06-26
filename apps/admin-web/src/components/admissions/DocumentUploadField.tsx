"use client";

import { FileText, X } from "lucide-react";
import { AppFileInput } from "@/components/ui/AppFileInput";

type Props = {
  label: string;
  required?: boolean;
  accept?: string;
  fileId: string;
  fileName: string;
  uploading: boolean;
  disabled?: boolean;
  onSelect: (file: File) => void;
  onClear: () => void;
};

export function DocumentUploadField({
  label,
  required,
  accept = ".pdf,.jpg,.jpeg,.png,.webp",
  fileId,
  fileName,
  uploading,
  disabled,
  onSelect,
  onClear,
}: Props) {
  return (
    <div className="gw-doc-upload">
      <span className="gw-form-label">
        {label}
        {required && <span className="gw-form-required">*</span>}
      </span>
      {fileId ? (
        <div className="gw-doc-upload-file">
          <FileText size={16} className="gw-doc-upload-icon" aria-hidden />
          <span className="gw-doc-upload-name" title={fileName}>
            {fileName}
          </span>
          <button
            type="button"
            className="btn btn-ghost gw-btn-sm"
            disabled={disabled || uploading}
            onClick={onClear}
            aria-label={`Remove ${label}`}
          >
            <X size={14} />
          </button>
        </div>
      ) : (
        <AppFileInput
          variant="field"
          accept={accept}
          file={null}
          disabled={disabled}
          uploading={uploading}
          placeholder="Choose PDF or image"
          aria-label={label}
          onChange={(file) => {
            if (file) onSelect(file);
          }}
        />
      )}
    </div>
  );
}
