import { z } from "zod";

import { DocumentTypeSchema } from "@/features/clinical-documents/document-types";

export const PatientDocumentSchema = z.object({
  id: z.string(),
  documentType: DocumentTypeSchema,
  title: z.string(),
  documentDate: z.string(),
  authorName: z.string(),
  excerpt: z.string(),
  isTruncated: z.boolean(),
});

export const PatientDetailSchema = z.object({
  id: z.string(),
  displayName: z.string(),
  mrn: z.string(),
  dateOfBirth: z.string(),
  sex: z.string(),
  documentCount: z.number().int().nonnegative(),
  documents: z.array(PatientDocumentSchema),
});

export type PatientDocument = z.infer<typeof PatientDocumentSchema>;
export type PatientDetail = z.infer<typeof PatientDetailSchema>;
