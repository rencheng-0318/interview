import { describe, expect, it } from "vitest";

import { ClinicalSearchRequestSchema, ClinicalSearchResponseSchema } from "./schemas";

describe("clinical search schemas", () => {
  it("accepts the search request contract", () => {
    const request = {
      query: "recurrent headaches with visual aura",
      documentTypes: ["specialist_note"],
      limit: 10,
    };

    expect(ClinicalSearchRequestSchema.parse(request)).toEqual(request);
  });

  it("rejects a malformed response", () => {
    const response = {
      query: "headache",
      results: [],
      meta: { resultCount: "0", tookMs: 4 },
    };

    expect(ClinicalSearchResponseSchema.safeParse(response).success).toBe(false);
  });
});
