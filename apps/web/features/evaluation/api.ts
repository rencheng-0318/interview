import "server-only";

import { apiRequest } from "@/lib/api/client";

import { EvaluationReportSchema } from "./schemas";

export function runEvaluation() {
  return apiRequest("/api/evaluation/run", EvaluationReportSchema, {
    method: "POST",
    timeoutMs: 120_000,
  });
}
