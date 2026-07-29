import Link from "next/link";

import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { fetchSession } from "@/features/session/api";

export default async function OverviewPage() {
  const session = await fetchSession();

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">
          {session.practiceName}
        </h1>
        <p className="mt-1 text-content-secondary">
          Signed in as {session.displayName} ({session.role}). Every record you can reach
          belongs to this practice.
        </p>
      </header>

      <Card>
        <CardHeader>
          <h2 className="font-semibold">Clinical search</h2>
        </CardHeader>
        <CardBody className="space-y-3">
          <p className="text-content-secondary">
            Describe a presentation in plain language and find patients in this practice
            whose existing notes and reports are relevant. Each result shows the passage
            that caused the match.
          </p>
          <p className="text-sm text-content-muted">
            Search retrieves existing document text. It does not generate a diagnosis or
            infer a condition that is not already recorded.
          </p>
          <Link
            href="/search"
            className="inline-flex h-11 items-center rounded-md bg-primary px-4 font-medium text-primary-contrast hover:bg-primary-hover"
          >
            Open clinical search
          </Link>
        </CardBody>
      </Card>
    </div>
  );
}
