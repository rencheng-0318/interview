import { Badge } from "@/components/ui/badge";
import { DOCUMENT_TYPE_LABELS } from "@/features/clinical-documents/document-types";
import type { PatientDocument } from "@/features/patients/schemas";
import { formatDocumentDate } from "@/lib/format";

export function DocumentList({ documents }: { documents: PatientDocument[] }) {
  if (documents.length === 0) {
    return <p className="text-content-muted">This patient has no documents on file.</p>;
  }

  return (
    <ul className="space-y-4">
      {documents.map((document) => (
        <li key={document.id} className="rounded-lg border border-border bg-surface p-4">
          <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
            <h3 className="font-semibold text-content">{document.title}</h3>
            <Badge>{DOCUMENT_TYPE_LABELS[document.documentType]}</Badge>
            <span className="text-sm text-content-muted">
              {formatDocumentDate(document.documentDate)} · {document.authorName}
            </span>
          </div>
          <p className="mt-2 whitespace-pre-line text-sm text-content-secondary">
            {document.excerpt}
            {document.isTruncated ? "…" : ""}
          </p>
          {document.isTruncated ? (
            <p className="mt-2 text-xs text-content-muted">
              Excerpt only. The full document is not returned to the browser.
            </p>
          ) : null}
        </li>
      ))}
    </ul>
  );
}
