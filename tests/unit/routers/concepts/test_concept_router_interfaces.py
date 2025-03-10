from unittest.mock import AsyncMock

from py_semantic_taxonomy.adapters.routers.router import GraphService
from py_semantic_taxonomy.domain.entities import Concept


async def test_concept_create(cn, client, monkeypatch):
    monkeypatch.setattr(
        GraphService, "concept_create", AsyncMock(return_value=Concept.from_json_ld(cn.concept_low))
    )

    response = client.post("/concept/", json=cn.concept_low)
    assert response.status_code == 200


async def test_concept_create_error(cn, client, monkeypatch):
    monkeypatch.setattr(GraphService, "concept_create", AsyncMock())

    obj = cn.concept_low
    del obj["@id"]

    response = client.post("/concept/", json=obj)
    assert response.json()["detail"][0]["type"] == "missing"
    assert response.json()["detail"][0]["loc"] == ["body", "@id"]
    assert response.status_code == 422
