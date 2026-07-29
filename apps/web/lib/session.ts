import "server-only";

import { cookies } from "next/headers";

export const SESSION_COOKIE = "demo_user_id";
export const DEFAULT_DEMO_USER_ID = "user-northside-01";

export async function getDemoUserId(): Promise<string> {
  const store = await cookies();
  return store.get(SESSION_COOKIE)?.value ?? DEFAULT_DEMO_USER_ID;
}

export async function getSessionToken(): Promise<string> {
  return `demo_${await getDemoUserId()}`;
}
