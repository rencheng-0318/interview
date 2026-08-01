"use client";

import { useEffect, useState, useTransition } from "react";
import { useActionState } from "react";
import { useFormStatus } from "react-dom";

import { Alert } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Spinner } from "@/components/ui/spinner";

import { runEvaluationAction } from "../actions";
import { clearReports, loadReports, saveReport, type StoredReport } from "../lib/indexeddb";
import type { EvaluationReport } from "../schemas";
import { EVALUATION_INITIAL_STATE, type EvaluationActionState } from "../types";

function RunButton() {
  const { pending } = useFormStatus();
  return (
    <Button type="submit" disabled={pending}>
      {pending ? <Spinner label="Running evaluation" /> : "Run evaluation"}
    </Button>
  );
}

function pct(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

function MetricCard({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <Card>
      <CardBody className="space-y-1">
        <p className="text-sm text-content-secondary">{label}</p>
        <p className="text-2xl font-semibold tracking-tight">{value}</p>
        {hint ? <p className="text-xs text-content-muted">{hint}</p> : null}
      </CardBody>
    </Card>
  );
}

function ReportView({ report }: { report: EvaluationReport }) {
  const { summary, cases } = report;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <MetricCard
          label="Hit rate"
          value={pct(summary.hitRate)}
          hint={`${summary.hitCount}/${summary.totalCases} cases found`}
        />
        <MetricCard label="MRR" value={summary.mrr.toFixed(3)} hint="Mean reciprocal rank" />
        <MetricCard
          label="Avg latency"
          value={`${summary.avgLatencyMs.toFixed(0)} ms`}
          hint="Per query"
        />
        <MetricCard
          label="Decoy leaks"
          value={String(summary.decoyLeakCount)}
          hint="Cross-practice isolation"
        />
      </div>

      <Card>
        <CardHeader>
          <h2 className="font-semibold">Case breakdown</h2>
        </CardHeader>
        <CardBody className="divide-y divide-border p-0">
          {cases.map((c) => (
            <div key={c.caseId} className="flex items-start gap-4 px-5 py-4">
              <div
                className={`mt-1 flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-bold ${
                  c.hit ? "bg-accent-surface text-accent" : "bg-danger-surface text-danger"
                }`}
              >
                {c.hit ? c.rank : "✕"}
              </div>
              <div className="min-w-0 flex-1 space-y-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-medium">{c.caseId}</span>
                  <Badge tone="neutral">{c.conditionKey}</Badge>
                  {c.decoyLeaked ? <Badge tone="accent">decoy leaked</Badge> : null}
                </div>
                <p className="truncate text-sm text-content-secondary italic">
                  &ldquo;{c.query}&rdquo;
                </p>
                <p className="text-xs text-content-muted">
                  expected {c.expectedPatientId}
                  {c.relevanceScore !== null ? ` · score ${c.relevanceScore}` : ""} · {c.tookMs} ms
                </p>
              </div>
            </div>
          ))}
        </CardBody>
      </Card>
    </div>
  );
}

export function EvaluationDashboard() {
  const [history, setHistory] = useState<StoredReport[]>([]);
  const [selected, setSelected] = useState<EvaluationReport | null>(null);
  const [isClearing, startClear] = useTransition();

  const [state, formAction] = useActionState(async (prev: EvaluationActionState) => {
    const result = await runEvaluationAction(prev);
    if (result.status === "success" && result.report) {
      await saveReport(result.report);
      setHistory(await loadReports());
      setSelected(null);
    }
    return result;
  }, EVALUATION_INITIAL_STATE);

  // Load persisted history on mount
  useEffect(() => {
    let cancelled = false;
    loadReports()
      .then((rows) => {
        if (!cancelled) setHistory(rows);
      })
      .catch(() => {
        // IndexedDB unavailable; ignore
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const handleClear = () => {
    startClear(async () => {
      await clearReports();
      setHistory([]);
    });
  };

  const current = selected ?? (state.status === "success" ? state.report : null);

  return (
    <div className="space-y-6">
      <form action={formAction} className="flex items-center gap-3">
        <RunButton />
        <p className="text-sm text-content-muted">
          Runs all curated cases against the live search pipeline.
        </p>
      </form>

      {state.status === "error" ? (
        <Alert tone="danger" title="Evaluation failed">
          {state.error}
        </Alert>
      ) : null}

      {current ? (
        <ReportView report={current} />
      ) : state.status === "idle" ? (
        <EmptyState
          title="No evaluation yet"
          description="Run an evaluation to measure retrieval quality across the curated cases."
        />
      ) : null}

      {history.length > 0 ? (
        <Card>
          <CardHeader className="flex items-center justify-between">
            <h2 className="font-semibold">History</h2>
            <Button variant="secondary" onClick={handleClear} disabled={isClearing}>
              Clear history
            </Button>
          </CardHeader>
          <CardBody className="divide-y divide-border p-0">
            {history.map((entry) => (
              <button
                key={entry.id}
                type="button"
                onClick={() => setSelected(entry.report)}
                className="flex w-full items-center justify-between px-5 py-3 text-left hover:bg-surface-raised"
              >
                <span className="text-sm text-content-secondary">
                  {new Date(entry.savedAt).toLocaleString()}
                </span>
                <span className="text-sm font-medium">
                  hit {pct(entry.report.summary.hitRate)} · MRR{" "}
                  {entry.report.summary.mrr.toFixed(3)}
                </span>
              </button>
            ))}
          </CardBody>
        </Card>
      ) : null}
    </div>
  );
}
