import type { ReactNode } from "react";

interface EmptyStateProps {
  title: string;
  description: string;
  children?: ReactNode;
}

export function EmptyState({ title, description, children }: EmptyStateProps) {
  return (
    <div className="rounded-lg border border-dashed border-border-strong bg-surface px-6 py-12 text-center">
      <p className="text-base font-semibold text-content">{title}</p>
      <p className="mx-auto mt-2 max-w-prose text-sm text-content-muted">{description}</p>
      {children ? <div className="mt-4 flex justify-center">{children}</div> : null}
    </div>
  );
}
