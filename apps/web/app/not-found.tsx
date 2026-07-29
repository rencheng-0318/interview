import Link from "next/link";

import { EmptyState } from "@/components/ui/empty-state";

export default function NotFound() {
  return (
    <EmptyState
      title="Not found"
      description="This record does not exist, or it belongs to another practice."
    >
      <Link href="/search" className="font-medium text-primary hover:underline">
        Back to clinical search
      </Link>
    </EmptyState>
  );
}
