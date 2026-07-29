import asyncpg

EXPECTED_DOCUMENT_COUNT = 2400
EXPECTED_PRACTICE_COUNT = 3


async def test_seed_loaded_the_expected_volume(connection: asyncpg.Connection) -> None:
    assert await connection.fetchval("SELECT count(*) FROM practices") == EXPECTED_PRACTICE_COUNT
    assert (
        await connection.fetchval("SELECT count(*) FROM clinical_documents")
        == EXPECTED_DOCUMENT_COUNT
    )


async def test_migrations_are_recorded_and_idempotent(
    connection: asyncpg.Connection, settings
) -> None:
    from app.db.migrations import discover_migrations

    recorded = await connection.fetchval("SELECT count(*) FROM schema_migrations")
    on_disk = len(discover_migrations(settings.migrations_dir))

    assert recorded == on_disk


async def test_document_practice_always_matches_its_patient(connection: asyncpg.Connection) -> None:
    mismatched = await connection.fetchval(
        """
        SELECT count(*) FROM clinical_documents d
        JOIN patients p ON p.id = d.patient_id
        WHERE d.practice_id <> p.practice_id
        """
    )

    assert mismatched == 0


async def test_curated_expected_patients_are_in_the_primary_practice(
    connection: asyncpg.Connection, curated_cases: dict, primary_practice_id: str
) -> None:
    for case in curated_cases["cases"]:
        practice_id = await connection.fetchval(
            "SELECT practice_id FROM patients WHERE id = $1", case["expectedPatientId"]
        )
        assert practice_id == primary_practice_id, case["id"]


async def test_curated_decoys_live_in_a_different_practice(
    connection: asyncpg.Connection, curated_cases: dict, primary_practice_id: str
) -> None:
    for case in curated_cases["cases"]:
        practice_id = await connection.fetchval(
            "SELECT practice_id FROM patients WHERE id = $1",
            case["crossPracticeDecoyPatientId"],
        )
        assert practice_id != primary_practice_id, case["id"]


async def test_curated_evidence_never_quotes_the_query_verbatim(
    connection: asyncpg.Connection, curated_cases: dict
) -> None:
    for case in curated_cases["cases"]:
        body = await connection.fetchval(
            "SELECT body FROM clinical_documents WHERE id = $1", case["expectedDocumentId"]
        )
        assert case["query"].lower() not in body.lower(), case["id"]


async def test_decoy_evidence_does_quote_the_query_verbatim(
    connection: asyncpg.Connection, curated_cases: dict
) -> None:
    for case in curated_cases["cases"]:
        body = await connection.fetchval(
            "SELECT body FROM clinical_documents WHERE id = $1",
            case["crossPracticeDecoyDocumentId"],
        )
        assert case["query"].lower() in body.lower(), case["id"]


async def test_unindexable_documents_are_present(connection: asyncpg.Connection) -> None:
    blank = await connection.fetchval(
        r"SELECT count(*) FROM clinical_documents WHERE btrim(body, E' \t\n\r') = ''"
    )
    oversized = await connection.fetchval(
        "SELECT count(*) FROM clinical_documents WHERE length(body) > 50000"
    )
    without_word_breaks = await connection.fetchval(
        "SELECT count(*) FROM clinical_documents "
        "WHERE length(body) > 5000 AND position(' ' in body) = 0"
    )
    punctuation_only = await connection.fetchval(
        r"""
        SELECT count(*) FROM clinical_documents
        WHERE btrim(body, E' \t\n\r') <> '' AND body !~ '[[:alnum:]]'
        """
    )

    assert blank == 2, "one empty body and one whitespace-only body are expected"
    assert oversized == 1
    assert without_word_breaks == 1
    assert punctuation_only == 1
