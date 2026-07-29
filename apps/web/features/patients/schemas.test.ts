import { describe, expect, it } from "vitest";

import { PatientDetailSchema } from "./schemas";

const patient = {
  id: "patient-0001",
  displayName: "Jordan Lee",
  mrn: "MRN-0001",
  dateOfBirth: "1980-01-01",
  sex: "female",
  documentCount: 1,
  documents: [
    {
      id: "document-000001",
      documentType: "diagnostic_note",
      title: "Consultation Note",
      documentDate: "2026-01-01",
      authorName: "Dr M. Aldridge",
      excerpt: "Synthetic clinical text.",
      isTruncated: false,
    },
  ],
};

describe("patient schemas", () => {
  it("accepts the patient detail contract", () => {
    expect(PatientDetailSchema.parse(patient)).toEqual(patient);
  });

  it("rejects an unknown document type", () => {
    const invalid = {
      ...patient,
      documents: [{ ...patient.documents[0], documentType: "unknown" }],
    };

    expect(PatientDetailSchema.safeParse(invalid).success).toBe(false);
  });
});
