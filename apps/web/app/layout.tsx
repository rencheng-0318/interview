import type { Metadata } from "next";

import { AppShell } from "@/components/layout/app-shell";
import { Alert } from "@/components/ui/alert";
import { fetchDemoIdentities, fetchSession } from "@/features/session/api";

import "./globals.css";

export const metadata: Metadata = {
  title: "Clinical Records",
  description: "Search synthetic clinical records by natural-language description.",
};

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  let content = children;
  let shell: Awaited<ReturnType<typeof loadShellData>> | null = null;

  try {
    shell = await loadShellData();
  } catch {
    content = (
      <Alert tone="danger" title="The API is not reachable">
        Start the backend with <code>make dev</code>, then reload. If it is already running,
        check <code>docker compose logs api</code>.
      </Alert>
    );
  }

  return (
    <html lang="en">
      <body>
        {shell ? (
          <AppShell session={shell.session} identities={shell.identities}>
            {children}
          </AppShell>
        ) : (
          <main className="mx-auto max-w-5xl px-4 py-10">{content}</main>
        )}
      </body>
    </html>
  );
}

async function loadShellData() {
  const [session, identities] = await Promise.all([fetchSession(), fetchDemoIdentities()]);
  return { session, identities };
}
