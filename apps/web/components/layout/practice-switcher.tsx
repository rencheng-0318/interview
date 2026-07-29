"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";

import type { DemoIdentity, Session } from "@/features/session/schemas";

interface PracticeSwitcherProps {
  session: Session;
  identities: DemoIdentity[];
}

export function PracticeSwitcher({ session, identities }: PracticeSwitcherProps) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const [failed, setFailed] = useState(false);

  async function switchIdentity(userId: string) {
    setFailed(false);
    const response = await fetch("/api/demo-session", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ userId }),
    });
    if (!response.ok) {
      setFailed(true);
      return;
    }
    startTransition(() => router.refresh());
  }

  return (
    <div className="flex items-center gap-2">
      <label htmlFor="demo-identity" className="text-sm text-content-muted">
        Signed in as
      </label>
      <select
        id="demo-identity"
        value={session.userId}
        disabled={isPending}
        onChange={(event) => void switchIdentity(event.target.value)}
        className="h-9 rounded-md border border-border-strong bg-surface px-2 text-sm text-content disabled:opacity-60"
      >
        {identities.map((identity) => (
          <option key={identity.userId} value={identity.userId}>
            {identity.practiceName} — {identity.displayName}
          </option>
        ))}
      </select>
      {failed ? (
        <span role="alert" className="text-sm font-medium text-danger">
          Could not switch
        </span>
      ) : null}
    </div>
  );
}
