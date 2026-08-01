import { z } from "zod";

export const CaseEvaluationSchema = z.object({
  caseId: z.string(),
  query: z.string(),
  conditionKey: z.string(),
  expectedPatientId: z.string(),
  hit: z.boolean(),
  rank: z.number().int(),
  relevanceScore: z.number().nullable(),
  tookMs: z.number().int().nonnegative(),
  decoyLeaked: z.boolean(),
  topSnippet: z.string().nullable(),
});

export const EvaluationSummarySchema = z.object({
  totalCases: z.number().int().nonnegative(),
  hitCount: z.number().int().nonnegative(),
  hitRate: z.number(),
  mrr: z.number(),
  ndcg: z.number(),
  avgLatencyMs: z.number(),
  p50LatencyMs: z.number().int().nonnegative(),
  p95LatencyMs: z.number().int().nonnegative(),
  p99LatencyMs: z.number().int().nonnegative(),
  decoyLeakCount: z.number().int().nonnegative(),
});

export const EvaluationReportSchema = z.object({
  evaluatedAt: z.string(),
  summary: EvaluationSummarySchema,
  cases: z.array(CaseEvaluationSchema),
});

export type CaseEvaluation = z.infer<typeof CaseEvaluationSchema>;
export type EvaluationSummary = z.infer<typeof EvaluationSummarySchema>;
export type EvaluationReport = z.infer<typeof EvaluationReportSchema>;
