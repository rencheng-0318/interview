import { cn } from "@/lib/cn";

export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      aria-hidden="true"
      className={cn("animate-pulse rounded bg-surface-raised", className)}
    />
  );
}

export function SkeletonResultCard() {
  return (
    <div className="rounded-lg border border-border bg-surface p-5">
      <Skeleton className="h-5 w-40" />
      <Skeleton className="mt-3 h-4 w-full" />
      <Skeleton className="mt-2 h-4 w-11/12" />
      <Skeleton className="mt-4 h-3 w-28" />
    </div>
  );
}
