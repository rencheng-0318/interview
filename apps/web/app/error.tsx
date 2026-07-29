"use client";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";

export default function RouteError({ reset }: { error: Error; reset: () => void }) {
  return (
    <div className="space-y-4">
      <Alert tone="danger" title="Something went wrong">
        This page could not be loaded. The problem has been logged.
      </Alert>
      <Button onClick={reset} variant="secondary">
        Try again
      </Button>
    </div>
  );
}
