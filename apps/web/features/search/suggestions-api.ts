"use client";

import { z } from "zod";

const SearchSuggestionsResponseSchema = z.object({
  suggestions: z.array(z.string()),
  query: z.string(),
});

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";

export async function fetchSearchSuggestions(query: string): Promise<string[]> {
  if (!query || query.length < 2) {
    return [];
  }

  try {
    const response = await fetch(
      `${API_BASE_URL}/api/search/suggestions?q=${encodeURIComponent(query)}`,
      {
        method: "GET",
        headers: {
          Accept: "application/json",
        },
      }
    );

    if (!response.ok) {
      return [];
    }

    const data: unknown = await response.json();
    const parsed = SearchSuggestionsResponseSchema.safeParse(data);

    if (!parsed.success) {
      return [];
    }

    return parsed.data.suggestions;
  } catch {
    return [];
  }
}
