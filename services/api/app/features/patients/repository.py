from dataclasses import dataclass
from datetime import date

import asyncpg

PATIENT_SQL = """
SELECT id, practice_id, mrn, first_name, last_name, date_of_birth, sex
FROM patients
WHERE id = $1 AND practice_id = $2
"""

DOCUMENTS_SQL = r"""
SELECT id, document_type, title, document_date, author_name,
       left(btrim(body, E' \t\n\r'), $3) AS excerpt,
       length(btrim(body, E' \t\n\r')) AS body_length
FROM clinical_documents
WHERE patient_id = $1 AND practice_id = $2
ORDER BY document_date DESC, id
"""

EXCERPT_LENGTH = 400


@dataclass(frozen=True)
class PatientRecord:
    id: str
    practice_id: str
    mrn: str
    first_name: str
    last_name: str
    date_of_birth: date
    sex: str


@dataclass(frozen=True)
class DocumentSummary:
    id: str
    document_type: str
    title: str
    document_date: date
    author_name: str
    excerpt: str
    body_length: int


async def fetch_patient(
    pool: asyncpg.Pool, patient_id: str, practice_id: str
) -> PatientRecord | None:
    record = await pool.fetchrow(PATIENT_SQL, patient_id, practice_id)
    return PatientRecord(**dict(record)) if record else None


async def fetch_patient_documents(
    pool: asyncpg.Pool, patient_id: str, practice_id: str
) -> list[DocumentSummary]:
    records = await pool.fetch(DOCUMENTS_SQL, patient_id, practice_id, EXCERPT_LENGTH)
    return [DocumentSummary(**dict(record)) for record in records]
