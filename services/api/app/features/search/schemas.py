from datetime import date

from app.domain import DocumentType
from app.schemas import CamelModel


class ClinicalSearchRequest(CamelModel):
    query: str
    document_types: list[DocumentType] | None = None
    limit: int | None = None


class PatientSummary(CamelModel):
    id: str
    display_name: str


class BestMatch(CamelModel):
    document_id: str
    document_type: DocumentType
    document_title: str
    document_date: date
    snippet: str
    relevance_score: float


class SearchResult(CamelModel):
    patient: PatientSummary
    best_match: BestMatch
    additional_matching_documents: int


class SearchMeta(CamelModel):
    result_count: int
    took_ms: int


class ClinicalSearchResponse(CamelModel):
    query: str
    results: list[SearchResult]
    meta: SearchMeta
