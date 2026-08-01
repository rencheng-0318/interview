from app.schemas import CamelModel


class CaseEvaluation(CamelModel):
    case_id: str
    query: str
    condition_key: str
    expected_patient_id: str
    hit: bool
    rank: int  # 1-based; -1 if not found
    relevance_score: float | None = None
    took_ms: int
    decoy_leaked: bool
    top_snippet: str | None = None


class EvaluationSummary(CamelModel):
    total_cases: int
    hit_count: int
    hit_rate: float
    mrr: float  # Mean Reciprocal Rank
    avg_latency_ms: float
    decoy_leak_count: int


class EvaluationReport(CamelModel):
    evaluated_at: str
    summary: EvaluationSummary
    cases: list[CaseEvaluation]
