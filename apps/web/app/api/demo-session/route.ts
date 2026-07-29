import { NextResponse } from "next/server";
import { z } from "zod";

import { fetchDemoIdentities } from "@/features/session/api";
import { SESSION_COOKIE } from "@/lib/session";

const RequestSchema = z.object({ userId: z.string().min(1).max(128) });

const COOKIE_MAX_AGE_SECONDS = 60 * 60 * 24 * 7;

export async function POST(request: Request) {
  let payload: unknown;
  try {
    payload = await request.json();
  } catch {
    return NextResponse.json({ error: "Malformed request body." }, { status: 400 });
  }

  const parsed = RequestSchema.safeParse(payload);
  if (!parsed.success) {
    return NextResponse.json({ error: "A userId is required." }, { status: 400 });
  }

  const identities = await fetchDemoIdentities();
  if (!identities.some((identity) => identity.userId === parsed.data.userId)) {
    return NextResponse.json({ error: "Unknown demo identity." }, { status: 400 });
  }

  const response = NextResponse.json({ userId: parsed.data.userId });
  response.cookies.set({
    name: SESSION_COOKIE,
    value: parsed.data.userId,
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    maxAge: COOKIE_MAX_AGE_SECONDS,
  });
  return response;
}
