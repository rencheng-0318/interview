from fastapi import APIRouter

from app.context import CurrentContext, PoolDep
from app.schemas import CamelModel

router = APIRouter(prefix="/api/session", tags=["session"])

IDENTITIES_SQL = """
SELECT u.id, u.display_name, u.role, p.id AS practice_id, p.name AS practice_name
FROM users u
JOIN practices p ON p.id = u.practice_id
ORDER BY p.name, u.role, u.id
"""


class SessionResponse(CamelModel):
    user_id: str
    display_name: str
    role: str
    practice_id: str
    practice_name: str


class DemoIdentity(CamelModel):
    user_id: str
    display_name: str
    role: str
    practice_id: str
    practice_name: str
    token: str


@router.get("", response_model=SessionResponse)
async def current_session(context: CurrentContext) -> SessionResponse:
    return SessionResponse(
        user_id=context.user_id,
        display_name=context.display_name,
        role=context.role,
        practice_id=context.practice_id,
        practice_name=context.practice_name,
    )


@router.get("/identities", response_model=list[DemoIdentity])
async def demo_identities(pool: PoolDep) -> list[DemoIdentity]:
    records = await pool.fetch(IDENTITIES_SQL)
    return [
        DemoIdentity(
            user_id=record["id"],
            display_name=record["display_name"],
            role=record["role"],
            practice_id=record["practice_id"],
            practice_name=record["practice_name"],
            token=f"demo_{record['id']}",
        )
        for record in records
    ]
