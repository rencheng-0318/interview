from datetime import date

from fastapi import APIRouter

from app.context import CurrentContext, PoolDep
from app.errors import NotFoundError
from app.features.patients.repository import fetch_patient, fetch_patient_documents
from app.schemas import CamelModel

router = APIRouter(prefix="/api/patients", tags=["patients"])


class PatientDocument(CamelModel):
    id: str
    document_type: str
    title: str
    document_date: date
    author_name: str
    excerpt: str
    is_truncated: bool


class PatientDetail(CamelModel):
    id: str
    display_name: str
    mrn: str
    date_of_birth: date
    sex: str
    document_count: int
    documents: list[PatientDocument]


@router.get("/{patient_id}", response_model=PatientDetail)
async def get_patient(patient_id: str, pool: PoolDep, context: CurrentContext) -> PatientDetail:
    patient = await fetch_patient(pool, patient_id, context.practice_id)
    if patient is None:
        raise NotFoundError("No patient with that identifier exists in the current practice.")

    documents = await fetch_patient_documents(pool, patient_id, context.practice_id)
    return PatientDetail(
        id=patient.id,
        display_name=f"{patient.first_name} {patient.last_name}",
        mrn=patient.mrn,
        date_of_birth=patient.date_of_birth,
        sex=patient.sex,
        document_count=len(documents),
        documents=[
            PatientDocument(
                id=document.id,
                document_type=document.document_type,
                title=document.title,
                document_date=document.document_date,
                author_name=document.author_name,
                excerpt=document.excerpt,
                is_truncated=document.body_length > len(document.excerpt),
            )
            for document in documents
        ],
    )
