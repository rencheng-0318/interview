import "server-only";

import { apiRequest } from "@/lib/api/client";

import {
  ClinicalSearchRequestSchema,
  ClinicalSearchResponseSchema,
  type ClinicalSearchRequest,
} from "./schemas";

export function searchClinicalRecords(request: ClinicalSearchRequest) {
  return apiRequest("/api/clinical-search", ClinicalSearchResponseSchema, {
    method: "POST",
    body: ClinicalSearchRequestSchema.parse(request),
  });
}
