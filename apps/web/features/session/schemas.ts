import { z } from "zod";

export const SessionSchema = z.object({
  userId: z.string(),
  displayName: z.string(),
  role: z.string(),
  practiceId: z.string(),
  practiceName: z.string(),
});

export const DemoIdentitySchema = SessionSchema.extend({
  token: z.string(),
});

export type Session = z.infer<typeof SessionSchema>;
export type DemoIdentity = z.infer<typeof DemoIdentitySchema>;
