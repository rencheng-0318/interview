from httpx import AsyncClient


async def test_default_identity_is_used_when_no_token_is_supplied(api: AsyncClient) -> None:
    response = await api.get("/api/session")

    assert response.status_code == 200
    assert response.json()["practiceId"] == "practice-northside"


async def test_token_selects_the_users_practice(
    api: AsyncClient, lakeshore_headers: dict[str, str]
) -> None:
    response = await api.get("/api/session", headers=lakeshore_headers)

    assert response.status_code == 200
    assert response.json()["practiceId"] == "practice-lakeshore"


async def test_unknown_user_is_rejected(api: AsyncClient) -> None:
    response = await api.get("/api/session", headers={"Authorization": "Bearer demo_user-nope"})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


async def test_malformed_authorization_header_is_rejected(api: AsyncClient) -> None:
    response = await api.get("/api/session", headers={"Authorization": "Basic abc123"})

    assert response.status_code == 401


async def test_identities_are_offered_for_the_demo_switcher(api: AsyncClient) -> None:
    response = await api.get("/api/session/identities")

    assert response.status_code == 200
    identities = response.json()
    assert {identity["practiceId"] for identity in identities} == {
        "practice-northside",
        "practice-lakeshore",
        "practice-summit",
    }
    assert all(identity["token"].startswith("demo_") for identity in identities)
