from fastapi import APIRouter

from app.context import CurrentContext, PoolDep
from app.errors import ErrorResponse, NotImplementedYetError
from app.features.search.schemas import ClinicalSearchRequest, ClinicalSearchResponse

router = APIRouter(prefix="/api", tags=["search"])


@router.post(
    "/clinical-search",
    response_model=ClinicalSearchResponse,
    responses={
        422: {"model": ErrorResponse},
        501: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)
async def clinical_search(
    payload: ClinicalSearchRequest,
    pool: PoolDep,
    context: CurrentContext,
) -> ClinicalSearchResponse:
    raise NotImplementedYetError(
        "POST /api/clinical-search is not implemented yet. "
        "See services/api/app/features/search/README.md."
    )
