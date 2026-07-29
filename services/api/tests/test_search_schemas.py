from app.domain import DocumentType
from app.features.search.schemas import ClinicalSearchRequest


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
