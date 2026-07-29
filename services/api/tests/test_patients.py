import asyncpg
from httpx import AsyncClient


async def first_patient_in(connection: asyncpg.Connection, practice_id: str) -> str:
    return await connection.fetchval(
        "SELECT id FROM patients WHERE practice_id = $1 ORDER BY id LIMIT 1", practice_id
    )


async def test_patient_detail_includes_documents(
    api: AsyncClient, connection: asyncpg.Connection, northside_headers: dict[str, str]
) -> None:
    patient_id = await first_patient_in(connection, "practice-northside")

    response = await api.get(f"/api/patients/{patient_id}", headers=northside_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == patient_id
    assert body["displayName"]
    assert body["documentCount"] == len(body["documents"])
    assert body["documents"], "seeded patients are expected to have documents"


async def test_patient_from_another_practice_is_not_visible(
    api: AsyncClient, connection: asyncpg.Connection, northside_headers: dict[str, str]
) -> None:
    other_practice_patient = await first_patient_in(connection, "practice-lakeshore")

    response = await api.get(f"/api/patients/{other_practice_patient}", headers=northside_headers)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


async def test_same_patient_is_visible_to_their_own_practice(
    api: AsyncClient, connection: asyncpg.Connection, lakeshore_headers: dict[str, str]
) -> None:
    patient_id = await first_patient_in(connection, "practice-lakeshore")

    response = await api.get(f"/api/patients/{patient_id}", headers=lakeshore_headers)

    assert response.status_code == 200


async def test_document_excerpts_are_truncated_rather_than_returned_whole(
    api: AsyncClient, connection: asyncpg.Connection, northside_headers: dict[str, str]
) -> None:
    patient_id = await connection.fetchval(
        """
        SELECT patient_id FROM clinical_documents
        WHERE practice_id = 'practice-northside' AND length(body) > 2000
        ORDER BY id LIMIT 1
        """
    )

    response = await api.get(f"/api/patients/{patient_id}", headers=northside_headers)

    assert response.status_code == 200
    truncated = [d for d in response.json()["documents"] if d["isTruncated"]]
    assert truncated, "a long document should be reported as truncated"
    assert all(len(d["excerpt"]) <= 400 for d in truncated)


async def test_unknown_patient_returns_not_found(
    api: AsyncClient, northside_headers: dict[str, str]
) -> None:
    response = await api.get("/api/patients/patient-does-not-exist", headers=northside_headers)

    assert response.status_code == 404
