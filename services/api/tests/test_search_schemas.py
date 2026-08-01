from app.domain import DocumentType
from app.features.search.schemas import ClinicalSearchRequest, SearchMeta


def test_search_request_maps_camel_case_contract_to_python_names() -> None:
    request = ClinicalSearchRequest.model_validate(
        {
            "query": "recurrent headaches with visual aura",
            "documentTypes": ["specialist_note"],
            "limit": 10,
        }
    )

    assert request.document_types == [DocumentType.SPECIALIST_NOTE]
    assert request.model_dump(by_alias=True)["documentTypes"] == [DocumentType.SPECIALIST_NOTE]


def test_search_meta_defaults_degraded_to_false() -> None:
    meta = SearchMeta(result_count=5, took_ms=120)
    assert meta.degraded is False
    dumped = meta.model_dump(by_alias=True)
    assert dumped["degraded"] is False


def test_search_meta_degraded_true_serialises_correctly() -> None:
    meta = SearchMeta(result_count=3, took_ms=80, degraded=True)
    assert meta.degraded is True
    dumped = meta.model_dump(by_alias=True)
    assert dumped["degraded"] is True
