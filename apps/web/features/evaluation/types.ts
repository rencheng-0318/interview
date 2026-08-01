import type { EvaluationReport } from "./schemas";

export interface EvaluationActionState {
  status: "idle" | "success" | "error";
  report?: EvaluationReport;
  error?: string;
}

export const EVALUATION_INITIAL_STATE: EvaluationActionState = { status: "idle" };
