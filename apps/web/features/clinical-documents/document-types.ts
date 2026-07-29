import { z } from "zod";

export const DOCUMENT_TYPES = [
  "diagnostic_note",
  "specialist_note",
  "radiology_report",
  "lab_report",
] as const;

export const DocumentTypeSchema = z.enum(DOCUMENT_TYPES);

export type DocumentType = z.infer<typeof DocumentTypeSchema>;

export const DOCUMENT_TYPE_LABELS: Record<DocumentType, string> = {
  diagnostic_note: "Diagnostic note",
  specialist_note: "Specialist note",
  radiology_report: "Radiology report",
  lab_report: "Laboratory report",
};
