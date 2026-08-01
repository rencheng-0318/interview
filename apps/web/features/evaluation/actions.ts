"use server";

import { runEvaluation } from "./api";
import type { EvaluationActionState } from "./types";

export async function runEvaluationAction(
  _prev: EvaluationActionState,
): Promise<EvaluationActionState> {
  try {
    const report = await runEvaluation();
    return { status: "success", report };
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Evaluation failed unexpectedly.";
    return { status: "error", error: message };
  }
}
