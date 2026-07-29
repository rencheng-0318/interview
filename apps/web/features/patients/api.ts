import "server-only";

import { apiRequest } from "@/lib/api/client";

import { PatientDetailSchema } from "./schemas";

export function fetchPatient(patientId: string) {
  return apiRequest(`/api/patients/${encodeURIComponent(patientId)}`, PatientDetailSchema);
}
