import { describe, expect, it } from "vitest";

import { DemoIdentitySchema, SessionSchema } from "./schemas";

const session = {
  userId: "user-northside-01",
  displayName: "Dr Alex Reyes",
  role: "clinician",
  practiceId: "practice-northside",
  practiceName: "Northside Family Medicine",
};

describe("session schemas", () => {
  it("accepts the session contract", () => {
    expect(SessionSchema.parse(session)).toEqual(session);
  });

  it("rejects an identity without a token", () => {
    expect(DemoIdentitySchema.safeParse(session).success).toBe(false);
  });
});
