import orjson

from unittest.mock import AsyncMock

from py_semantic_taxonomy.adapters.routers.router import GraphService
from py_semantic_taxonomy.domain.entities import Concept, DuplicateIRI


async def test_concept_create(cn, client, monkeypatch):
    monkeypatch.setattr(
        GraphService, "concept_create", AsyncMock(return_value=Concept.from_json_ld(cn.concept_low))
    )

    response = client.post("/concept/", json=cn.concept_low)
    assert response.status_code == 200


async def test_concept_create_error_missing_(cn, client, monkeypatch):
    monkeypatch.setattr(GraphService, "concept_create", AsyncMock())

    obj = cn.concept_low
    del obj["@id"]

    response = client.post("/concept/", json=obj)
    assert response.json()["detail"][0]["type"] == "missing"
    assert response.json()["detail"][0]["loc"] == ["body", "@id"]
    assert response.status_code == 422


async def test_concept_create_error_already_exists(cn, client, monkeypatch):
    monkeypatch.setattr(GraphService, "concept_create", AsyncMock(side_effect=DuplicateIRI))

    response = client.post("/concept/", json=cn.concept_low)
    assert orjson.loads(response.content) == {
        "message": "Resource with `@id` already exists",
        "detail": {"@id": "http://data.europa.eu/xsp/cn2024/010100000080"},
    }
    assert response.status_code == 409
