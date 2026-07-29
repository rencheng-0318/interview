import type { ReactNode } from "react";

import { cn } from "@/lib/cn";

type Tone = "info" | "warning" | "danger" | "success";

const TONES: Record<Tone, { container: string; icon: string; label: string }> = {
  info: { container: "bg-info-surface text-info", icon: "i", label: "Information" },
  warning: { container: "bg-warning-surface text-warning", icon: "!", label: "Warning" },
  danger: { container: "bg-danger-surface text-danger", icon: "×", label: "Error" },
  success: { container: "bg-success-surface text-success", icon: "✓", label: "Success" },
};

interface AlertProps {
  tone?: Tone;
  title: string;
  children?: ReactNode;
  className?: string;
}

export function Alert({ tone = "info", title, children, className }: AlertProps) {
  const { container, icon, label } = TONES[tone];
  return (
    <div
      role={tone === "danger" ? "alert" : "status"}
      className={cn("flex gap-3 rounded-lg border border-transparent p-4", container, className)}
    >
      <span
        aria-hidden="true"
        className="mt-0.5 flex size-5 shrink-0 items-center justify-center rounded-full border border-current text-xs font-bold"
      >
        {icon}
      </span>
      <div className="min-w-0">
        <p className="font-semibold">
          <span className="sr-only">{label}: </span>
          {title}
        </p>
        {children ? <div className="mt-1 text-sm opacity-90">{children}</div> : null}
      </div>
    </div>
  );
}
