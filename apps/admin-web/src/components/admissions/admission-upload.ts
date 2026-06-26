import { api } from "@/lib/api";

export const ADMISSION_MAX_UPLOAD_BYTES = 1024 * 1024;

export async function uploadAdmissionDocument(
  file: File,
  category: "document" | "report_card"
): Promise<{ id: string; name: string }> {
  if (file.size > ADMISSION_MAX_UPLOAD_BYTES) {
    throw new Error("File too large (max 1 MB)");
  }
  const fd = new FormData();
  fd.append("file", file);
  const res = await api<{ data: { id: string } }>(
    `/api/v1/files/upload?category=${category}`,
    { method: "POST", body: fd }
  );
  const id = res.data?.id;
  if (!id) throw new Error("Upload failed");
  return { id, name: file.name };
}

export type AdmissionDocumentType = "aadhaar" | "birth_certificate" | "apaar";

export async function extractAdmissionDocumentNumber(
  fileId: string,
  documentType: AdmissionDocumentType
): Promise<string | null> {
  const res = await api<{ data: { number: string | null } }>(
    "/api/v1/ops/admissions/extract-document-number",
    {
      method: "POST",
      body: JSON.stringify({ file_id: fileId, document_type: documentType }),
    }
  );
  return res.data?.number?.trim() || null;
}
