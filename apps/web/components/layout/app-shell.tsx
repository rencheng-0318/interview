import Link from "next/link";
import type { ReactNode } from "react";

import type { DemoIdentity, Session } from "@/features/session/schemas";

import { PracticeSwitcher } from "./practice-switcher";

const NAV_LINKS = [
  { href: "/", label: "Overview" },
  { href: "/search", label: "Clinical search" },
];

interface AppShellProps {
  session: Session;
  identities: DemoIdentity[];
  children: ReactNode;
}

export function AppShell({ session, identities, children }: AppShellProps) {
  return (
    <div className="min-h-dvh">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded focus:bg-surface focus:px-4 focus:py-2"
      >
        Skip to content
      </a>

      <header className="border-b border-border bg-surface">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center gap-4 px-4 py-3">
          <p className="text-base font-semibold tracking-tight">Clinical Records</p>
          <nav aria-label="Main" className="flex gap-1">
            {NAV_LINKS.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="rounded px-3 py-1.5 text-sm font-medium text-content-secondary hover:bg-surface-raised hover:text-content"
              >
                {link.label}
              </Link>
            ))}
          </nav>
          <div className="ml-auto">
            <PracticeSwitcher session={session} identities={identities} />
          </div>
        </div>
      </header>

      <main id="main" className="mx-auto max-w-5xl px-4 py-8">
        {children}
      </main>

      <footer className="mx-auto max-w-5xl px-4 pb-10 pt-2">
        <p className="text-xs text-content-muted">
          All records in this application are synthetic. Search retrieves existing document
          passages; it does not produce a diagnosis.
        </p>
      </footer>
    </div>
  );
}
