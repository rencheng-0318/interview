import { beforeEach, describe, expect, it, vi } from "vitest";

// Mock server-only modules before importing the action
vi.mock("./api", () => ({
  searchClinicalRecords: vi.fn(),
}));

vi.mock("@/lib/api/client", () => ({
  ApiError: class ApiError extends Error {
    constructor(
      readonly status: number,
      readonly code: string,
      message: string,
      readonly requestId?: string,
    ) {
      super(message);
      this.name = "ApiError";
    }
  },
}));

import { ApiError } from "@/lib/api/client";

import { searchAction } from "./actions";
import { searchClinicalRecords } from "./api";
import type { SearchState } from "./types";

const mockSearch = vi.mocked(searchClinicalRecords);

function makeFormData(query: string, documentType = ""): FormData {
  const fd = new FormData();
  fd.set("query", query);
  fd.set("documentType", documentType);
  return fd;
}

const prevState: SearchState = { status: "idle" };

describe("searchAction", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns validation_error for empty query", async () => {
    const result = await searchAction(prevState, makeFormData(""));
    expect(result.status).toBe("validation_error");
    expect(result.error).toBe("Please enter a search query.");
  });

  it("returns validation_error for whitespace-only query", async () => {
    const result = await searchAction(prevState, makeFormData("   "));
    expect(result.status).toBe("validation_error");
    expect(result.error).toBe("Please enter a search query.");
  });

  it("returns validation_error for query exceeding 500 characters", async () => {
    const longQuery = "a".repeat(501);
    const result = await searchAction(prevState, makeFormData(longQuery));
    expect(result.status).toBe("validation_error");
    expect(result.error).toBe("Query must be at most 500 characters.");
  });

  it("returns success with results", async () => {
    const mockResponse = {
      query: "headache",
      results: [
        {
          patient: { id: "p1", displayName: "John Doe" },
          bestMatch: {
            documentId: "d1",
            documentType: "diagnostic_note" as const,
            documentTitle: "Diagnosis",
            documentDate: "2024-01-01",
            snippet: "Patient reports headaches",
            relevanceScore: 0.9,
          },
          additionalMatchingDocuments: 2,
        },
      ],
      meta: { resultCount: 1, tookMs: 15 },
    };
    mockSearch.mockResolvedValue(mockResponse);

    const result = await searchAction(prevState, makeFormData("headache"));
    expect(result.status).toBe("success");
    expect(result.data).toEqual(mockResponse);
    expect(result.query).toBe("headache");
  });

  it("returns no_results when API returns empty results", async () => {
    const mockResponse = {
      query: "unknown symptom",
      results: [],
      meta: { resultCount: 0, tookMs: 5 },
    };
    mockSearch.mockResolvedValue(mockResponse);

    const result = await searchAction(prevState, makeFormData("unknown symptom"));
    expect(result.status).toBe("no_results");
    expect(result.data).toEqual(mockResponse);
  });

  it("passes documentType filter to the API", async () => {
    const mockResponse = {
      query: "headache",
      results: [],
      meta: { resultCount: 0, tookMs: 5 },
    };
    mockSearch.mockResolvedValue(mockResponse);

    await searchAction(prevState, makeFormData("headache", "lab_report"));
    expect(mockSearch).toHaveBeenCalledWith({
      query: "headache",
      documentTypes: ["lab_report"],
    });
  });

  it("returns validation_error on 422 ApiError", async () => {
    mockSearch.mockRejectedValue(new ApiError(422, "invalid_query", "Query too short"));

    const result = await searchAction(prevState, makeFormData("x"));
    expect(result.status).toBe("validation_error");
    expect(result.error).toBe("Query too short");
  });

  it("returns service_error on 503 ApiError", async () => {
    mockSearch.mockRejectedValue(new ApiError(503, "unavailable", "Service down"));

    const result = await searchAction(prevState, makeFormData("headache"));
    expect(result.status).toBe("service_error");
    expect(result.error).toBe(
      "The search service is temporarily unavailable. Please try again shortly.",
    );
  });

  it("returns service_error on other ApiError", async () => {
    mockSearch.mockRejectedValue(new ApiError(500, "internal", "Something broke"));

    const result = await searchAction(prevState, makeFormData("headache"));
    expect(result.status).toBe("service_error");
    expect(result.error).toBe("Something broke");
  });

  it("returns service_error on unexpected non-ApiError", async () => {
    mockSearch.mockRejectedValue(new TypeError("network failure"));

    const result = await searchAction(prevState, makeFormData("headache"));
    expect(result.status).toBe("service_error");
    expect(result.error).toBe("An unexpected error occurred. Please try again.");
  });
});
