from unittest.mock import AsyncMock

import orjson

from py_semantic_taxonomy.adapters.routers.router import GraphService
from py_semantic_taxonomy.domain.constants import SKOS
from py_semantic_taxonomy.domain.entities import Concept, ConceptNotFoundError, DuplicateIRI


async def test_concept_get(cn, client, monkeypatch):
    monkeypatch.setattr(
        GraphService, "concept_get", AsyncMock(return_value=Concept.from_json_ld(cn.concept_top))
    )

    response = await client.get("/concept/", params={"iri": cn.concept_top["@id"]})
    assert response.status_code == 200
    concept = orjson.loads(response.content)
    for key, value in concept.items():
        if value:
            assert cn.concept_top[key] == value


async def test_concept_get_not_found(cn, client, monkeypatch):
    monkeypatch.setattr(GraphService, "concept_get", AsyncMock(side_effect=ConceptNotFoundError()))

    response = await client.get("/concept/", params={"iri": "foo"})
    concept = orjson.loads(response.content)
    assert response.status_code == 404
    assert concept == {
        "message": "Concept with IRI 'foo' not found",
        "detail": {"iri": "foo"},
    }


async def test_concept_create(cn, client, monkeypatch):
    monkeypatch.setattr(
        GraphService, "concept_create", AsyncMock(return_value=Concept.from_json_ld(cn.concept_low))
    )

    response = await client.post("/concept/", json=cn.concept_low)
    assert response.status_code == 200


async def test_concept_create_error_validation_errors(cn, client, monkeypatch):
    monkeypatch.setattr(GraphService, "concept_create", AsyncMock())

    obj = cn.concept_low
    del obj["@id"]

    response = await client.post("/concept/", json=obj)
    assert response.json()["detail"][0]["type"] == "missing"
    assert response.json()["detail"][0]["loc"] == ["body", "@id"]
    assert response.status_code == 422


async def test_concept_create_error_already_exists(cn, client, monkeypatch):
    monkeypatch.setattr(GraphService, "concept_create", AsyncMock(side_effect=DuplicateIRI))

    response = await client.post("/concept/", json=cn.concept_low)
    assert orjson.loads(response.content) == {
        "message": "Resource with `@id` already exists",
        "detail": {"@id": "http://data.europa.eu/xsp/cn2024/010100000080"},
    }
    assert response.status_code == 409


async def test_concept_update(cn, client, monkeypatch):
    monkeypatch.setattr(
        GraphService, "concept_update", AsyncMock(return_value=Concept.from_json_ld(cn.concept_top))
    )

    updated = cn.concept_top
    updated[f"{SKOS}altLabel"] = [{"@value": "Dream a little dream", "@language": "en"}]
    del updated[f"{SKOS}narrower"]
    del updated[f"{SKOS}topConceptOf"]
    response = await client.put("/concept/", json=updated)
    assert response.status_code == 200


async def test_concept_update_error_validation_errors(cn, client, monkeypatch):
    monkeypatch.setattr(GraphService, "concept_update", AsyncMock())

    obj = cn.concept_low
    del obj[f"{SKOS}broader"]
    del obj[f"{SKOS}prefLabel"]

    response = await client.put("/concept/", json=obj)
    assert response.json()["detail"][0]["type"] == "missing"
    assert response.json()["detail"][0]["loc"] == ["body", f"{SKOS}prefLabel"]
    assert response.status_code == 422


async def test_concept_update_error_missing(cn, client, monkeypatch):
    monkeypatch.setattr(GraphService, "concept_update", AsyncMock(side_effect=ConceptNotFoundError))

    obj = cn.concept_low
    del obj[f"{SKOS}broader"]
    id_ = obj["@id"]

    response = await client.put("/concept/", json=obj)
    assert orjson.loads(response.content) == {
        "message": f"Concept with `@id` {id_} not present",
        "detail": {"@id": id_},
    }
    assert response.status_code == 404
