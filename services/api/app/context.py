import logging
from dataclasses import dataclass
from typing import Annotated

import asyncpg
from fastapi import Depends, Request

from app.config import Settings, get_settings
from app.errors import UnauthorizedError

logger = logging.getLogger("api.context")

TOKEN_PREFIX = "demo_"

USER_LOOKUP_SQL = """
SELECT u.id, u.practice_id, u.display_name, u.role, p.name AS practice_name
FROM users u
JOIN practices p ON p.id = u.practice_id
WHERE u.id = $1
"""


@dataclass(frozen=True)
class RequestContext:
    user_id: str
    practice_id: str
    display_name: str
    role: str
    practice_name: str


def parse_user_id(authorization: str | None, default_user_id: str) -> str:
    if not authorization:
        return default_user_id
    scheme, _, credentials = authorization.partition(" ")
    if scheme.lower() != "bearer" or not credentials.startswith(TOKEN_PREFIX):
        raise UnauthorizedError("Authorization header must be 'Bearer demo_<user-id>'.")
    user_id = credentials.removeprefix(TOKEN_PREFIX).strip()
    if not user_id:
        raise UnauthorizedError("Bearer token did not contain a user identifier.")
    return user_id


def get_pool(request: Request) -> asyncpg.Pool:
    return request.app.state.pool


async def get_request_context(
    request: Request,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> RequestContext:
    user_id = parse_user_id(request.headers.get("authorization"), settings.default_demo_user_id)
    record = await pool.fetchrow(USER_LOOKUP_SQL, user_id)
    if record is None:
        logger.warning("rejected unknown session user_id=%s", user_id)
        raise UnauthorizedError("The session identity is not recognised.")
    return RequestContext(
        user_id=record["id"],
        practice_id=record["practice_id"],
        display_name=record["display_name"],
        role=record["role"],
        practice_name=record["practice_name"],
    )


CurrentContext = Annotated[RequestContext, Depends(get_request_context)]
PoolDep = Annotated[asyncpg.Pool, Depends(get_pool)]
