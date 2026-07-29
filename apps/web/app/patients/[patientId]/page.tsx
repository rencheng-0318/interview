import Link from "next/link";
import { notFound } from "next/navigation";

import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { fetchPatient } from "@/features/patients/api";
import { DocumentList } from "@/features/patients/components/document-list";
import { ApiError } from "@/lib/api/client";
import { calculateAge, formatDocumentDate } from "@/lib/format";

interface PageProps {
  params: Promise<{ patientId: string }>;
}

export default async function PatientDetailPage({ params }: PageProps) {
  const { patientId } = await params;

  const patient = await fetchPatient(patientId).catch((error: unknown) => {
    if (error instanceof ApiError && error.status === 404) notFound();
    throw error;
  });

  const age = calculateAge(patient.dateOfBirth);

  return (
    <div className="space-y-6">
      <div>
        <Link href="/search" className="text-sm font-medium text-primary hover:underline">
          ← Back to search
        </Link>
      </div>

      <header>
        <h1 className="text-2xl font-semibold tracking-tight">{patient.displayName}</h1>
        <p className="mt-1 text-content-secondary">
          {patient.mrn} · {age === null ? "age unknown" : `${age} years`} · {patient.sex}
          {" · born "}
          {formatDocumentDate(patient.dateOfBirth)}
        </p>
      </header>

      <Card>
        <CardHeader>
          <h2 className="font-semibold">
            Clinical documents{" "}
            <span className="font-normal text-content-muted">({patient.documentCount})</span>
          </h2>
        </CardHeader>
        <CardBody>
          <DocumentList documents={patient.documents} />
        </CardBody>
      </Card>
    </div>
  );
}
