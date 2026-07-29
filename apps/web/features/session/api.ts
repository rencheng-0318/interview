import "server-only";

import { z } from "zod";

import { apiRequest } from "@/lib/api/client";

import { DemoIdentitySchema, SessionSchema } from "./schemas";

export function fetchSession() {
  return apiRequest("/api/session", SessionSchema);
}

export function fetchDemoIdentities() {
  return apiRequest("/api/session/identities", z.array(DemoIdentitySchema));
}
