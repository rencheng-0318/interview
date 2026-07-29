from httpx import AsyncClient

from tests.stubs import StubEmbeddingClient


async def test_health_reports_ok_when_dependencies_are_up(api: AsyncClient) -> None:
    response = await api.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["dependencies"] == {"database": "ok", "embedding": "ok"}


async def test_health_reports_degraded_when_embedding_is_down(
    api: AsyncClient, embedding_client: StubEmbeddingClient
) -> None:
    embedding_client.healthy = False

    response = await api.get("/health")

    assert response.status_code == 503
    assert response.json()["dependencies"]["embedding"] == "unavailable"


async def test_every_response_carries_a_request_id(api: AsyncClient) -> None:
    response = await api.get("/health")

    assert response.headers["X-Request-Id"]
