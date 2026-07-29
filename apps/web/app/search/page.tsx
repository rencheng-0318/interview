import { Alert } from "@/components/ui/alert";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { fetchSession } from "@/features/session/api";

export const metadata = { title: "Clinical search" };

export default async function ClinicalSearchPage() {
  const session = await fetchSession();

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Clinical search</h1>
        <p className="mt-1 text-content-secondary">
          Describe a presentation in plain language to find patients in{" "}
          {session.practiceName} whose existing documents are relevant.
        </p>
      </header>

      <Alert tone="warning" title="Not implemented yet">
        This is the starter shell. The search form, result list, and the states for
        loading, empty, invalid input, and backend failure are yours to build.
      </Alert>

      <Card>
        <CardHeader>
          <h2 className="font-semibold">What to build here</h2>
        </CardHeader>
        <CardBody className="space-y-4 text-sm text-content-secondary">
          <ol className="list-decimal space-y-2 pl-5">
            <li>
              A query field with an optional document-type filter, submitting to the search
              endpoint through a Server Action or a route handler — never by calling the API
              directly from the browser.
            </li>
            <li>
              A ranked patient list where each entry shows the patient, the source document
              title and type, its date, the matching excerpt, and an indication when further
              documents also matched.
            </li>
            <li>
              Distinct states for idle, loading, results, no results, invalid query, and
              backend or embedding-service failure.
            </li>
            <li>
              A link from each result to <code>/patients/[patientId]</code>, which already
              works.
            </li>
          </ol>
          <p>
            Feel free to use any visual design or layout that works for you. We are not
            evaluating visual polish, but the experience should be clear and intuitive.
          </p>
          <p>
            Primitives are ready in <code>components/ui/</code>: <code>Alert</code>,{" "}
            <code>Badge</code>, <code>Button</code>, <code>Card</code>,{" "}
            <code>EmptyState</code>, <code>TextField</code>, <code>SelectField</code>,{" "}
            <code>Spinner</code>, <code>Skeleton</code>. Search schemas and the server-side
            call are in <code>features/search/</code>.
          </p>
          <p className="text-content-muted">
            Present the relevance score as a retrieval aid or leave it out. It must not be
            labelled as confidence, probability, or clinical certainty.
          </p>
        </CardBody>
      </Card>
    </div>
  );
}
