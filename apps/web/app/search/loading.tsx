import { Skeleton } from "@/components/ui/skeleton";

export default function SearchLoading() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-8 w-56" />
      <Skeleton className="h-5 w-80" />
      <Skeleton className="h-40 w-full" />
    </div>
  );
}
