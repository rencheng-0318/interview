import type { InputHTMLAttributes, SelectHTMLAttributes } from "react";

import { cn } from "@/lib/cn";

const FIELD_CLASSES =
  "w-full rounded-md border border-border-strong bg-surface px-3 text-content " +
  "placeholder:text-content-muted disabled:cursor-not-allowed disabled:opacity-60";

interface TextFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  hint?: string;
  errorMessage?: string;
}

export function TextField({
  label,
  hint,
  errorMessage,
  id,
  className,
  ...props
}: TextFieldProps) {
  const fieldId = id ?? props.name ?? "field";
  const hintId = `${fieldId}-hint`;
  const errorId = `${fieldId}-error`;
  const describedBy = [hint ? hintId : null, errorMessage ? errorId : null]
    .filter(Boolean)
    .join(" ");

  return (
    <div className="w-full">
      <label htmlFor={fieldId} className="mb-1.5 block text-sm font-medium text-content">
        {label}
      </label>
      <input
        id={fieldId}
        aria-invalid={errorMessage ? true : undefined}
        aria-describedby={describedBy || undefined}
        className={cn(FIELD_CLASSES, "h-11", errorMessage && "border-danger", className)}
        {...props}
      />
      {hint ? (
        <p id={hintId} className="mt-1.5 text-sm text-content-muted">
          {hint}
        </p>
      ) : null}
      {errorMessage ? (
        <p id={errorId} className="mt-1.5 text-sm font-medium text-danger">
          {errorMessage}
        </p>
      ) : null}
    </div>
  );
}

interface SelectFieldProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label: string;
}

export function SelectField({ label, id, className, children, ...props }: SelectFieldProps) {
  const fieldId = id ?? props.name ?? "select";
  return (
    <div>
      <label htmlFor={fieldId} className="mb-1.5 block text-sm font-medium text-content">
        {label}
      </label>
      <select id={fieldId} className={cn(FIELD_CLASSES, "h-11", className)} {...props}>
        {children}
      </select>
    </div>
  );
}
