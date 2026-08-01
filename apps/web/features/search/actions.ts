"use server";

import { ApiError } from "@/lib/api/client";

import { searchClinicalRecords } from "./api";
import type { SearchState } from "./types";

export async function searchAction(
  _prev: SearchState,
  formData: FormData,
): Promise<SearchState> {
  const query = (formData.get("query") as string | null)?.trim() ?? "";
  const documentType = (formData.get("documentType") as string | null) ?? "";

  if (!query) {
    return { status: "validation_error", error: "Please enter a search query.", query };
  }

  if (query.length > 500) {
    return {
      status: "validation_error",
      error: "Query must be at most 500 characters.",
      query,
    };
  }

  try {
    const result = await searchClinicalRecords({
      query,
      documentTypes: documentType ? [documentType as never] : undefined,
    });

    if (result.results.length === 0) {
      return { status: "no_results", data: result, query };
    }

    return { status: "success", data: result, query };
  } catch (error) {
    if (error instanceof ApiError) {
      if (error.status === 422) {
        return { status: "validation_error", error: error.message, query };
      }
      if (error.status === 503) {
        return {
          status: "service_error",
          error: "The search service is temporarily unavailable. Please try again shortly.",
          query,
        };
      }
      return { status: "service_error", error: error.message, query };
    }
    return {
      status: "service_error",
      error: "An unexpected error occurred. Please try again.",
      query,
    };
  }
}
