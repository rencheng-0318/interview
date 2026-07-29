import "server-only";

import { z, type ZodType } from "zod";

import { getSessionToken } from "@/lib/session";

const API_BASE_URL = process.env.API_BASE_URL ?? "http://api:8000";
const DEFAULT_TIMEOUT_MS = 30_000;

const ApiErrorBodySchema = z.object({
  error: z.object({
    code: z.string(),
    message: z.string(),
    requestId: z.string(),
  }),
});

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    message: string,
    readonly requestId?: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function toApiError(response: Response): Promise<ApiError> {
  const fallback = `Request failed with status ${response.status}`;
  try {
    const body: unknown = await response.json();
    const parsed = ApiErrorBodySchema.safeParse(body);
    if (parsed.success) {
      return new ApiError(
        response.status,
        parsed.data.error.code,
        parsed.data.error.message,
        parsed.data.error.requestId,
      );
    }
    return new ApiError(response.status, "unexpected_response", fallback);
  } catch {
    return new ApiError(response.status, "unexpected_response", fallback);
  }
}

interface RequestOptions {
  method?: "GET" | "POST";
  body?: unknown;
  cache?: RequestCache;
  timeoutMs?: number;
}

export async function apiRequest<T>(
  path: string,
  schema: ZodType<T>,
  options: RequestOptions = {},
): Promise<T> {
  const { method = "GET", body, cache = "no-store", timeoutMs = DEFAULT_TIMEOUT_MS } = options;
  const token = await getSessionToken();

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      cache,
      signal: controller.signal,
      headers: {
        Accept: "application/json",
        Authorization: `Bearer ${token}`,
        ...(body === undefined ? {} : { "Content-Type": "application/json" }),
      },
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    });

    if (!response.ok) {
      throw await toApiError(response);
    }
    const payload: unknown = await response.json();
    const parsed = schema.safeParse(payload);
    if (!parsed.success) {
      throw new ApiError(502, "unexpected_response", "The API returned an invalid response.");
    }
    return parsed.data;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new ApiError(504, "upstream_timeout", "The request to the API timed out.");
    }
    throw new ApiError(502, "upstream_unreachable", "The API could not be reached.");
  } finally {
    clearTimeout(timeout);
  }
}
