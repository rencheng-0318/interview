import { z } from "zod";

import { DocumentTypeSchema } from "@/features/clinical-documents/document-types";

export const ClinicalSearchRequestSchema = z.object({
  query: z.string(),
  documentTypes: z.array(DocumentTypeSchema).optional(),
  limit: z.number().int().positive().optional(),
});

export const PatientSummarySchema = z.object({
  id: z.string(),
  displayName: z.string(),
});

export const BestMatchSchema = z.object({
  documentId: z.string(),
  documentType: DocumentTypeSchema,
  documentTitle: z.string(),
  documentDate: z.string(),
  snippet: z.string(),
  relevanceScore: z.number(),
});

export const SearchResultSchema = z.object({
  patient: PatientSummarySchema,
  bestMatch: BestMatchSchema,
  additionalMatchingDocuments: z.number().int().nonnegative(),
});

export const ClinicalSearchResponseSchema = z.object({
  query: z.string(),
  results: z.array(SearchResultSchema),
  meta: z.object({
    resultCount: z.number().int().nonnegative(),
    tookMs: z.number().int().nonnegative(),
  }),
});

export type ClinicalSearchRequest = z.infer<typeof ClinicalSearchRequestSchema>;
export type ClinicalSearchResponse = z.infer<typeof ClinicalSearchResponseSchema>;
