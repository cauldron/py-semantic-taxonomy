from unittest.mock import AsyncMock

import orjson

from py_semantic_taxonomy.adapters.routers.router import GraphService, Paths
from py_semantic_taxonomy.domain.constants import SKOS
from py_semantic_taxonomy.domain.entities import (
    ConceptScheme,
    ConceptSchemeNotFoundError,
    DuplicateIRI,
)


async def test_concept_scheme_get(cn, client, monkeypatch):
    monkeypatch.setattr(
        GraphService,
        "concept_scheme_get",
        AsyncMock(return_value=ConceptScheme.from_json_ld(cn.scheme)),
    )

    response = await client.get(Paths.concept_scheme, params={"iri": cn.scheme["@id"]})
    assert response.status_code == 200
    for key, value in response.json().items():
        if value:
            assert cn.scheme[key] == value

    GraphService.concept_scheme_get.assert_called_once()
    assert isinstance(GraphService.concept_scheme_get.call_args[1]["iri"], str)


async def test_concept_get_not_found(cn, client, monkeypatch):
    monkeypatch.setattr(
        GraphService, "concept_scheme_get", AsyncMock(side_effect=ConceptSchemeNotFoundError())
    )

    response = await client.get(Paths.concept_scheme, params={"iri": "foo"})
    assert response.status_code == 404
    assert response.json() == {
        "message": "Concept Scheme with IRI 'foo' not found",
        "detail": {"iri": "foo"},
    }


async def test_concept_scheme_create(cn, client, monkeypatch):
    monkeypatch.setattr(
        GraphService,
        "concept_scheme_create",
        AsyncMock(return_value=ConceptScheme.from_json_ld(cn.scheme)),
    )

    response = await client.post(Paths.concept_scheme, json=cn.scheme)
    assert response.status_code == 200

    GraphService.concept_scheme_create.assert_called_once()
    assert isinstance(GraphService.concept_scheme_create.call_args[0][0], ConceptScheme)


async def test_concept_scheme_create_error_validation_errors(cn, client, monkeypatch):
    monkeypatch.setattr(GraphService, "concept_scheme_create", AsyncMock())

    obj = cn.scheme
    del obj["@id"]

    response = await client.post(Paths.concept_scheme, json=obj)
    assert response.json()["detail"][0]["type"] == "missing"
    assert response.json()["detail"][0]["loc"] == ["body", "@id"]
    assert response.status_code == 422


async def test_concept_scheme_create_error_already_exists(cn, client, monkeypatch):
    monkeypatch.setattr(GraphService, "concept_scheme_create", AsyncMock(side_effect=DuplicateIRI))

    response = await client.post(Paths.concept_scheme, json=cn.scheme)
    assert orjson.loads(response.content) == {
        "message": "Resource with `@id` already exists",
        "detail": {"@id": "http://data.europa.eu/xsp/cn2024/cn2024"},
    }
    assert response.status_code == 409


async def test_concept_scheme_update(cn, client, monkeypatch):
    monkeypatch.setattr(
        GraphService,
        "concept_scheme_update",
        AsyncMock(return_value=ConceptScheme.from_json_ld(cn.scheme)),
    )

    updated = cn.scheme
    updated[f"{SKOS}prefLabel"] = [{"@value": "Combine all them nommies", "@language": "en"}]
    response = await client.put(Paths.concept_scheme, json=updated)
    assert response.status_code == 200

    GraphService.concept_scheme_update.assert_called_once()
    assert isinstance(GraphService.concept_scheme_update.call_args[0][0], ConceptScheme)


async def test_concept_scheme_update_error_validation_errors(cn, client, monkeypatch):
    monkeypatch.setattr(GraphService, "concept_scheme_update", AsyncMock())

    obj = cn.scheme
    del obj[f"{SKOS}prefLabel"]

    response = await client.put(Paths.concept_scheme, json=obj)
    assert response.json()["detail"][0]["type"] == "missing"
    assert response.json()["detail"][0]["loc"] == ["body", f"{SKOS}prefLabel"]
    assert response.status_code == 422


async def test_concept_scheme_update_error_missing(cn, client, monkeypatch):
    monkeypatch.setattr(
        GraphService, "concept_scheme_update", AsyncMock(side_effect=ConceptSchemeNotFoundError)
    )

    obj = cn.scheme
    obj["@id"] = "http://data.europa.eu/xsp/cn2024/cn2025"
    id_ = obj["@id"]

    response = await client.put(Paths.concept_scheme, json=obj)
    assert orjson.loads(response.content) == {
        "message": f"Concept Scheme with `@id` {id_} not present",
        "detail": {"@id": id_},
    }
    assert response.status_code == 404


async def test_concept_scheme_delete(cn, client, monkeypatch):
    monkeypatch.setattr(GraphService, "concept_scheme_delete", AsyncMock(return_value=1))

    response = await client.delete(Paths.concept_scheme, params={"iri": cn.scheme["@id"]})
    assert response.status_code == 200
    assert orjson.loads(response.content) == {
        "message": "Concept Scheme (possibly) deleted",
        "count": 1,
    }

    GraphService.concept_scheme_delete.assert_called_once()
    assert isinstance(GraphService.concept_scheme_delete.call_args[1]["iri"], str)
