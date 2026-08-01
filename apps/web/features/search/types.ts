import type { ClinicalSearchResponse } from "./schemas";

export interface SearchState {
  status: "idle" | "success" | "no_results" | "validation_error" | "service_error";
  data?: ClinicalSearchResponse;
  error?: string;
  query?: string;
}

export const INITIAL_STATE: SearchState = { status: "idle" };
