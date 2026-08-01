"use client";

import Link from "next/link";
import { useCallback, useState } from "react";
import { useActionState } from "react";
import { useFormStatus } from "react-dom";

import { Alert } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardBody } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { SelectField } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import {
  DOCUMENT_TYPES,
  DOCUMENT_TYPE_LABELS,
} from "@/features/clinical-documents/document-types";

import { searchAction } from "../actions";
import { INITIAL_STATE, type SearchState } from "../types";
import { SearchSuggestions } from "./search-suggestions";

function SubmitButton() {
  const { pending } = useFormStatus();
  return (
    <Button type="submit" disabled={pending}>
      {pending ? <Spinner label="Searching" /> : "Search"}
    </Button>
  );
}

function SearchResults({ state }: { state: SearchState }) {
  if (state.status === "idle") {
    return (
      <EmptyState
        title="Search clinical records"
        description="Describe a clinical presentation in plain language to find patients whose existing documents are relevant."
      />
    );
  }

  if (state.status === "validation_error") {
    return <Alert tone="danger" title="Invalid query">{state.error}</Alert>;
  }

  if (state.status === "service_error") {
    return <Alert tone="danger" title="Service unavailable">{state.error}</Alert>;
  }

  if (state.status === "no_results") {
    return (
      <EmptyState
        title="No matching patients"
        description={`No records matched "${state.query}". Try rephrasing or broadening your search.`}
      />
    );
  }

  const { data } = state;
  if (!data) return null;

  return (
    <div className="space-y-4">
      <p className="text-sm text-content-secondary">
        {data.meta.resultCount} result{data.meta.resultCount !== 1 ? "s" : ""} in{" "}
        {data.meta.tookMs} ms
      </p>

      <div className="space-y-3">
        {data.results.map((result) => (
          <Card key={result.patient.id}>
            <CardBody className="space-y-2">
              <div className="flex items-start justify-between gap-2">
                <Link
                  href={`/patients/${result.patient.id}`}
                  className="font-semibold text-primary hover:underline"
                >
                  {result.patient.displayName}
                </Link>
                <Badge tone="info">
                  {DOCUMENT_TYPE_LABELS[result.bestMatch.documentType] ??
                    result.bestMatch.documentType}
                </Badge>
              </div>

              <p className="text-sm text-content-secondary">
                {result.bestMatch.documentTitle} &middot;{" "}
                {result.bestMatch.documentDate}
              </p>

              <p className="rounded bg-surface-raised p-3 text-sm text-content-secondary italic">
                &ldquo;{result.bestMatch.snippet}&rdquo;
              </p>

              {result.additionalMatchingDocuments > 0 && (
                <p className="text-xs text-content-muted">
                  +{result.additionalMatchingDocuments} more matching document
                  {result.additionalMatchingDocuments !== 1 ? "s" : ""}
                </p>
              )}
            </CardBody>
          </Card>
        ))}
      </div>
    </div>
  );
}

export function SearchPanel() {
  const [state, formAction] = useActionState(searchAction, INITIAL_STATE);
  const [query, setQuery] = useState(state.query ?? "");

  const handleSelectSuggestion = useCallback((value: string) => {
    setQuery(value);
  }, []);

  return (
    <div className="space-y-6">
      <form action={formAction} className="space-y-4">
        <div className="w-full">
          <label htmlFor="query" className="mb-1.5 block text-sm font-medium text-content">
            Clinical query
          </label>
          <SearchSuggestions
            query={query}
            onQueryChange={setQuery}
            onSelect={handleSelectSuggestion}
            inputId="query"
          />
          <input type="hidden" name="query" value={query} />
        </div>

        <div className="flex items-end gap-3">
          <div className="w-56">
            <SelectField label="Document type" name="documentType" defaultValue="">
              <option value="">All types</option>
              {DOCUMENT_TYPES.map((dt) => (
                <option key={dt} value={dt}>
                  {DOCUMENT_TYPE_LABELS[dt]}
                </option>
              ))}
            </SelectField>
          </div>
          <SubmitButton />
        </div>
      </form>

      <SearchResults state={state} />
    </div>
  );
}
