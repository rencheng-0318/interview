import { EvaluationDashboard } from "@/features/evaluation/components/evaluation-dashboard";
import { fetchSession } from "@/features/session/api";

export const metadata = { title: "Search quality evaluation" };

export default async function EvaluationPage() {
  const session = await fetchSession();

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Search quality evaluation</h1>
        <p className="mt-1 text-content-secondary">
          Measures retrieval quality for {session.practiceName} against the curated ground-truth
          cases. Reports are stored locally in your browser.
        </p>
      </header>

      <EvaluationDashboard />
    </div>
  );
}
