"""Evaluation endpoint: run curated cases against the search pipeline."""

import json
import logging
import math
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.clients.embedding import SupportsEmbedding
from app.context import PoolDep
from app.features.evaluation.schemas import (
    CaseEvaluation,
    EvaluationReport,
    EvaluationSummary,
)
from app.features.search.service import search_patients

logger = logging.getLogger("api.evaluation")

router = APIRouter(prefix="/api", tags=["evaluation"])

CURATED_CASES_PATH = Path("/srv/database/seed/data/curated_cases.json")
EVAL_LIMIT = 10
NDCG_K = 10  # NDCG cutoff


def _compute_ndcg(cases: list[CaseEvaluation], k: int = NDCG_K) -> float:
    """Compute NDCG@K: measures ranking quality considering position."""
    dcg = sum(
        1.0 / math.log2(c.rank + 1) for c in cases if c.hit and 0 < c.rank <= k
    )
    # Ideal: all cases hit at rank 1, each contributes 1/log2(2) = 1.0
    idcg = float(len(cases))
    return dcg / idcg if idcg > 0 else 0.0


def _compute_percentiles(values: list[int]) -> tuple[int, int, int]:
    """Compute P50, P95, P99 from a list of values."""
    if not values:
        return 0, 0, 0
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    p50 = sorted_vals[int(n * 0.50)]
    p95 = sorted_vals[min(int(n * 0.95), n - 1)]
    p99 = sorted_vals[min(int(n * 0.99), n - 1)]
    return p50, p95, p99


def get_embedding_client(request: Request) -> SupportsEmbedding:
    return request.app.state.embedding_client


EmbeddingDep = Annotated[SupportsEmbedding, Depends(get_embedding_client)]


def _load_cases() -> dict:
    with open(CURATED_CASES_PATH) as f:
        return json.load(f)


@router.post("/evaluation/run", response_model=EvaluationReport)
async def run_evaluation(pool: PoolDep, embedding_client: EmbeddingDep) -> EvaluationReport:
    """Execute all curated cases and produce a retrieval-quality report."""
    data = _load_cases()
    practice_id = data["primaryPracticeId"]
    cases = data["cases"]

    evaluations: list[CaseEvaluation] = []

    async with pool.acquire() as conn:
        for case in cases:
            started = time.perf_counter()
            results, _degraded = await search_patients(
                conn,
                embedding_client,
                case["query"],
                practice_id,
                None,
                EVAL_LIMIT,
            )
            took_ms = int((time.perf_counter() - started) * 1000)

            patient_ids = [r["patient_id"] for r in results]
            expected = case["expectedPatientId"]
            hit = expected in patient_ids
            rank = patient_ids.index(expected) + 1 if hit else -1

            relevance = None
            snippet = None
            if results:
                top = results[0]
                snippet = top["snippet"]
                if hit:
                    relevance = results[rank - 1]["relevance_score"]

            decoy = case.get("crossPracticeDecoyPatientId")
            decoy_leaked = decoy in patient_ids if decoy else False

            evaluations.append(
                CaseEvaluation(
                    case_id=case["id"],
                    query=case["query"],
                    condition_key=case.get("conditionKey", ""),
                    expected_patient_id=expected,
                    hit=hit,
                    rank=rank,
                    relevance_score=relevance,
                    took_ms=took_ms,
                    decoy_leaked=decoy_leaked,
                    top_snippet=snippet,
                )
            )

    total = len(evaluations)
    hit_count = sum(1 for e in evaluations if e.hit)
    mrr = (
        sum(1.0 / e.rank for e in evaluations if e.hit) / total if total else 0.0
    )
    ndcg = _compute_ndcg(evaluations)
    avg_latency = sum(e.took_ms for e in evaluations) / total if total else 0.0
    latencies = [e.took_ms for e in evaluations]
    p50, p95, p99 = _compute_percentiles(latencies)
    decoy_leaks = sum(1 for e in evaluations if e.decoy_leaked)

    report = EvaluationReport(
        evaluated_at=datetime.now(UTC).isoformat(),
        summary=EvaluationSummary(
            total_cases=total,
            hit_count=hit_count,
            hit_rate=round(hit_count / total, 4) if total else 0.0,
            mrr=round(mrr, 4),
            ndcg=round(ndcg, 4),
            avg_latency_ms=round(avg_latency, 1),
            p50_latency_ms=p50,
            p95_latency_ms=p95,
            p99_latency_ms=p99,
            decoy_leak_count=decoy_leaks,
        ),
        cases=evaluations,
    )

    logger.info(
        "evaluation complete hit_rate=%.2f mrr=%.2f ndcg=%.2f",
        report.summary.hit_rate,
        report.summary.mrr,
        report.summary.ndcg,
    )
    return report
