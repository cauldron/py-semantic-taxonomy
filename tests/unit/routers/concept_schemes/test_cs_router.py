from unittest.mock import AsyncMock

from py_semantic_taxonomy.application.graph_service import GraphService
from py_semantic_taxonomy.domain.constants import SKOS
from py_semantic_taxonomy.domain.entities import (
    ConceptScheme,
    ConceptSchemeNotFoundError,
    DuplicateIRI,
)
from py_semantic_taxonomy.domain.url_utils import get_full_api_path


async def test_concept_scheme_get(cn, anonymous_client, monkeypatch):
    monkeypatch.setattr(
        GraphService,
        "concept_scheme_get",
        AsyncMock(return_value=ConceptScheme.from_json_ld(cn.scheme)),
    )

    response = await anonymous_client.get(get_full_api_path("concept_scheme", iri=cn.scheme["@id"]))
    assert response.status_code == 200
    for key, value in response.json().items():
        if value:
            assert cn.scheme[key] == value

    GraphService.concept_scheme_get.assert_called_once()
    assert isinstance(GraphService.concept_scheme_get.call_args[1]["iri"], str)


async def test_concept_scheme_get_not_found(cn, anonymous_client, monkeypatch):
    monkeypatch.setattr(
        GraphService, "concept_scheme_get", AsyncMock(side_effect=ConceptSchemeNotFoundError())
    )

    response = await anonymous_client.get(get_full_api_path("concept_scheme", iri="foo"))
    assert response.status_code == 404
    assert response.json() == {
        "detail": "Concept Scheme with IRI `foo` not found",
    }


async def test_concept_scheme_get_all(cn, anonymous_client, monkeypatch):
    monkeypatch.setattr(
        GraphService,
        "concept_scheme_get_all",
        AsyncMock(return_value=[ConceptScheme.from_json_ld(cn.scheme)]),
    )

    response = await anonymous_client.get(get_full_api_path("concept_scheme_all"))
    assert response.status_code == 200
    assert len(response.json()) == 1

    GraphService.concept_scheme_get_all.assert_called_once()


async def test_concept_scheme_create(cn, client, monkeypatch):
    monkeypatch.setattr(
        GraphService,
        "concept_scheme_create",
        AsyncMock(return_value=ConceptScheme.from_json_ld(cn.scheme)),
    )

    response = await client.post(
        get_full_api_path("concept_scheme", iri=cn.scheme["@id"]), json=cn.scheme
    )
    assert response.status_code == 200

    GraphService.concept_scheme_create.assert_called_once()
    assert isinstance(GraphService.concept_scheme_create.call_args[0][0], ConceptScheme)


async def test_concept_scheme_create_unauthorized(anonymous_client, cn):
    response = await anonymous_client.post(
        get_full_api_path("concept_scheme", iri=cn.scheme["@id"]), json=cn.scheme
    )
    assert response.status_code == 400


async def test_concept_scheme_create_error_validation_errors(cn, client, monkeypatch):
    monkeypatch.setattr(GraphService, "concept_scheme_create", AsyncMock())

    obj = cn.scheme
    original_id = obj["@id"]
    del obj["@id"]

    response = await client.post(get_full_api_path("concept_scheme", iri=original_id), json=obj)
    assert response.json()["detail"][0]["type"] == "missing"
    assert response.json()["detail"][0]["loc"] == ["body", "@id"]
    assert response.status_code == 422


async def test_concept_scheme_create_error_already_exists(cn, client, monkeypatch):
    monkeypatch.setattr(GraphService, "concept_scheme_create", AsyncMock(side_effect=DuplicateIRI))

    response = await client.post(
        get_full_api_path("concept_scheme", iri=cn.scheme["@id"]), json=cn.scheme
    )
    assert response.json() == {
        "detail": f"Concept Scheme with IRI `{cn.scheme['@id']}` already exists"
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
    response = await client.put(
        get_full_api_path("concept_scheme", iri=updated["@id"]), json=updated
    )
    assert response.status_code == 200

    GraphService.concept_scheme_update.assert_called_once()
    assert isinstance(GraphService.concept_scheme_update.call_args[0][0], ConceptScheme)


async def test_concept_scheme_update_unauthorized(anonymous_client, cn):
    response = await anonymous_client.put(
        get_full_api_path("concept_scheme", iri=cn.scheme["@id"]), json=cn.scheme
    )
    assert response.status_code == 400


async def test_concept_scheme_update_error_validation_errors(cn, client, monkeypatch):
    monkeypatch.setattr(GraphService, "concept_scheme_update", AsyncMock())

    obj = cn.scheme
    del obj[f"{SKOS}prefLabel"]

    response = await client.put(get_full_api_path("concept_scheme", iri=obj["@id"]), json=obj)
    assert response.json()["detail"][0]["type"] == "missing"
    assert response.json()["detail"][0]["loc"] == ["body", f"{SKOS}prefLabel"]
    assert response.status_code == 422


async def test_concept_scheme_update_error_missing(cn, client, monkeypatch):
    monkeypatch.setattr(
        GraphService, "concept_scheme_update", AsyncMock(side_effect=ConceptSchemeNotFoundError)
    )

    obj = cn.scheme
    obj["@id"] = "http://data.europa.eu/xsp/cn2024/cn2025"

    response = await client.put(get_full_api_path("concept_scheme", iri=obj["@id"]), json=obj)
    assert response.json() == {
        "detail": f"Concept Scheme with IRI `{obj['@id']}` not found",
    }
    assert response.status_code == 404


async def test_concept_scheme_delete(cn, client, monkeypatch):
    monkeypatch.setattr(GraphService, "concept_scheme_delete", AsyncMock(return_value=1))

    response = await client.delete(get_full_api_path("concept_scheme", iri=cn.scheme["@id"]))
    assert response.status_code == 204

    GraphService.concept_scheme_delete.assert_called_once()
    assert isinstance(GraphService.concept_scheme_delete.call_args[1]["iri"], str)


async def test_concept_scheme_delete_unauthorized(anonymous_client, cn):
    response = await anonymous_client.delete(
        get_full_api_path("concept_scheme", iri=cn.scheme["@id"])
    )
    assert response.status_code == 400


async def test_concept_scheme_delete_not_found(cn, client, monkeypatch):
    monkeypatch.setattr(
        GraphService,
        "concept_scheme_delete",
        AsyncMock(side_effect=ConceptSchemeNotFoundError("Test")),
    )

    response = await client.delete(get_full_api_path("concept_scheme", iri=cn.scheme["@id"]))
    assert response.status_code == 404
    assert response.json() == {"detail": "Test"}
