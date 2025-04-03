from unittest.mock import AsyncMock

from py_semantic_taxonomy.adapters.routers.router import Paths
from py_semantic_taxonomy.application.graph_service import GraphService
from py_semantic_taxonomy.application.search_service import SearchService
from py_semantic_taxonomy.domain.constants import SKOS, RelationshipVerbs
from py_semantic_taxonomy.domain.entities import (
    Concept,
    ConceptNotFoundError,
    ConceptSchemesNotInDatabase,
    DuplicateIRI,
    DuplicateRelationship,
    HierarchyConflict,
    Relationship,
    RelationshipsInCurrentConceptScheme,
    SearchNotConfigured,
    SearchResult,
    UnknownLanguage,
)


async def test_concept_get(cn, anonymous_client, monkeypatch):
    monkeypatch.setattr(
        GraphService, "concept_get", AsyncMock(return_value=Concept.from_json_ld(cn.concept_top))
    )

    response = await anonymous_client.get(Paths.concepts, params={"iri": cn.concept_top["@id"]})
    assert response.status_code == 200
    for key, value in response.json().items():
        if value:
            assert cn.concept_top[key] == value

    GraphService.concept_get.assert_called_once()
    assert isinstance(GraphService.concept_get.call_args[1]["iri"], str)


async def test_concept_get_not_found(cn, anonymous_client, monkeypatch):
    monkeypatch.setattr(GraphService, "concept_get", AsyncMock(side_effect=ConceptNotFoundError()))

    response = await anonymous_client.get(Paths.concepts, params={"iri": "foo"})
    concept = response.json()
    assert response.status_code == 404
    assert concept == {
        "detail": "Concept with IRI `foo` not found",
    }


async def test_concept_create_unauthorized(anonymous_client):
    response = await anonymous_client.post(Paths.concepts, json={})
    assert response.status_code == 400


async def test_concept_create(cn, client, monkeypatch):
    monkeypatch.setattr(
        GraphService, "concept_create", AsyncMock(return_value=Concept.from_json_ld(cn.concept_low))
    )

    response = await client.post(Paths.concepts, json=cn.concept_low)
    assert response.status_code == 200
    GraphService.concept_create.assert_called_with(
        concept=Concept.from_json_ld(cn.concept_low),
        relationships=[
            Relationship(
                source="http://data.europa.eu/xsp/cn2024/010100000080",
                target="http://data.europa.eu/xsp/cn2024/010021000090",
                predicate=RelationshipVerbs.broader,
            )
        ],
    )
    GraphService.concept_create.assert_called_once()


async def test_concept_create_error_validation_errors(cn, client, monkeypatch):
    monkeypatch.setattr(GraphService, "concept_create", AsyncMock())

    obj = cn.concept_low
    del obj["@id"]

    response = await client.post(Paths.concepts, json=obj)
    assert response.json()["detail"][0]["type"] == "missing"
    assert response.json()["detail"][0]["loc"] == ["body", "@id"]
    assert response.status_code == 422


async def test_concept_create_error_concept_schemes_not_in_database(cn, client, monkeypatch):
    monkeypatch.setattr(
        GraphService,
        "concept_create",
        AsyncMock(side_effect=ConceptSchemesNotInDatabase("Problem")),
    )

    response = await client.post(Paths.concepts, json=cn.concept_top)
    assert response.status_code == 422
    assert response.json() == {"detail": "Problem"}


async def test_concept_create_error_hierarchy_conflict(cn, client, monkeypatch):
    monkeypatch.setattr(
        GraphService,
        "concept_create",
        AsyncMock(side_effect=HierarchyConflict("Problem")),
    )

    response = await client.post(Paths.concepts, json=cn.concept_top)
    assert response.status_code == 422
    assert response.json() == {"detail": "Problem"}


async def test_concept_create_error_already_exists(cn, client, monkeypatch):
    monkeypatch.setattr(GraphService, "concept_create", AsyncMock(side_effect=DuplicateIRI))

    response = await client.post(Paths.concepts, json=cn.concept_low)
    assert response.json() == {
        "detail": f"Concept with IRI `{cn.concept_low['@id']}` already exists",
    }
    assert response.status_code == 409


async def test_concept_create_error_relationships(cn, client, monkeypatch):
    monkeypatch.setattr(
        GraphService, "concept_create", AsyncMock(side_effect=DuplicateRelationship("Test"))
    )

    response = await client.post(Paths.concepts, json=cn.concept_low)
    assert response.json() == {
        "detail": "Test",
    }
    assert response.status_code == 422


async def test_concept_update(cn, client, monkeypatch):
    monkeypatch.setattr(
        GraphService, "concept_update", AsyncMock(return_value=Concept.from_json_ld(cn.concept_top))
    )

    updated = cn.concept_top
    updated[f"{SKOS}altLabel"] = [{"@value": "Dream a little dream", "@language": "en"}]
    if f"{SKOS}narrower" in updated:
        del updated[f"{SKOS}narrower"]

    response = await client.put(Paths.concepts, json=updated)
    assert response.status_code == 200

    GraphService.concept_update.assert_called_once()
    assert isinstance(GraphService.concept_update.call_args[0][0], Concept)


async def test_concept_update_unauthorized(anonymous_client):
    response = await anonymous_client.put(Paths.concepts, json={})
    assert response.status_code == 400


async def test_concept_update_error_validation_errors(cn, client, monkeypatch):
    monkeypatch.setattr(GraphService, "concept_update", AsyncMock())

    obj = cn.concept_low
    del obj[f"{SKOS}broader"]
    del obj[f"{SKOS}prefLabel"]

    response = await client.put(Paths.concepts, json=obj)
    assert response.json()["detail"][0]["type"] == "missing"
    assert response.json()["detail"][0]["loc"] == ["body", f"{SKOS}prefLabel"]
    assert response.status_code == 422


async def test_concept_update_error_hierarchy_conflict(cn, client, monkeypatch):
    monkeypatch.setattr(
        GraphService,
        "concept_update",
        AsyncMock(side_effect=HierarchyConflict("Problem")),
    )

    response = await client.put(Paths.concepts, json=cn.concept_top)
    assert response.status_code == 422
    assert response.json() == {"detail": "Problem"}


async def test_concept_update_error_concept_schemes_not_in_database(cn, client, monkeypatch):
    monkeypatch.setattr(
        GraphService,
        "concept_update",
        AsyncMock(side_effect=ConceptSchemesNotInDatabase("Problem")),
    )

    response = await client.put(Paths.concepts, json=cn.concept_top)
    assert response.status_code == 422
    assert response.json() == {"detail": "Problem"}


async def test_concept_update_error_relationships_concept_schemes(cn, client, monkeypatch):
    monkeypatch.setattr(
        GraphService,
        "concept_update",
        AsyncMock(side_effect=RelationshipsInCurrentConceptScheme("Problem")),
    )

    response = await client.put(Paths.concepts, json=cn.concept_top)
    assert response.status_code == 422
    assert response.json() == {"detail": "Problem"}


async def test_concept_update_error_missing(cn, client, monkeypatch):
    monkeypatch.setattr(GraphService, "concept_update", AsyncMock(side_effect=ConceptNotFoundError))

    obj = cn.concept_low
    del obj[f"{SKOS}broader"]
    id_ = obj["@id"]

    response = await client.put(Paths.concepts, json=obj)
    assert response.json() == {
        "detail": f"Concept with IRI `{id_}` not found",
    }
    assert response.status_code == 404


async def test_concept_delete(cn, client, monkeypatch):
    monkeypatch.setattr(GraphService, "concept_delete", AsyncMock(return_value=1))

    response = await client.delete(Paths.concepts, params={"iri": cn.concept_top["@id"]})
    assert response.status_code == 204

    GraphService.concept_delete.assert_called_once()
    assert isinstance(GraphService.concept_delete.call_args[1]["iri"], str)


async def test_concept_delete_unauthorized(anonymous_client):
    response = await anonymous_client.delete(Paths.concepts, params={"iri": ""})
    assert response.status_code == 400


async def test_concept_delete_not_found(cn, client, monkeypatch):
    monkeypatch.setattr(
        GraphService,
        "concept_delete",
        AsyncMock(side_effect=ConceptNotFoundError("Test")),
    )

    response = await client.delete(Paths.concepts, params={"iri": cn.concept_top["@id"]})
    assert response.status_code == 404
    assert response.json() == {"detail": "Test"}


async def test_concept_search(anonymous_client, monkeypatch):
    monkeypatch.setattr(
        SearchService,
        "search",
        AsyncMock(
            return_value=[SearchResult(id_="http://example.com/foo", label="foo", highlight="bar")]
        ),
    )

    response = await anonymous_client.get(
        Paths.search, params={"query": "foo", "language": "en", "semantic": 1}
    )
    result = response.json()
    assert response.status_code == 200
    assert result == [{"id_": "http://example.com/foo", "label": "foo", "highlight": "bar"}]


async def test_concept_search_not_configured(anonymous_client, monkeypatch):
    monkeypatch.setattr(
        SearchService,
        "search",
        AsyncMock(side_effect=SearchNotConfigured()),
    )

    response = await anonymous_client.get(
        Paths.search, params={"query": "foo", "language": "en", "semantic": 1}
    )
    assert response.status_code == 503
    assert response.json() == {"detail": "Search engine not available"}


async def test_concept_search_unknown_language(anonymous_client, monkeypatch):
    monkeypatch.setattr(
        SearchService,
        "search",
        AsyncMock(side_effect=UnknownLanguage()),
    )

    response = await anonymous_client.get(
        Paths.search, params={"query": "foo", "language": "en", "semantic": 1}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Search engine not configured for given language"}


async def test_concept_suggest(anonymous_client, monkeypatch):
    monkeypatch.setattr(
        SearchService,
        "suggest",
        AsyncMock(
            return_value=[SearchResult(id_="http://example.com/foo", label="foo", highlight="bar")]
        ),
    )

    response = await anonymous_client.get(
        Paths.suggest, params={"query": "foo", "language": "en", "semantic": 1}
    )
    result = response.json()
    assert response.status_code == 200
    assert result == [{"id_": "http://example.com/foo", "label": "foo", "highlight": "bar"}]


async def test_concept_suggest_not_configured(anonymous_client, monkeypatch):
    monkeypatch.setattr(
        SearchService,
        "suggest",
        AsyncMock(side_effect=SearchNotConfigured()),
    )

    response = await anonymous_client.get(Paths.suggest, params={"query": "foo", "language": "en"})
    assert response.status_code == 503
    assert response.json() == {"detail": "Search engine not available"}


async def test_concept_suggest_unknown_language(anonymous_client, monkeypatch):
    monkeypatch.setattr(
        SearchService,
        "suggest",
        AsyncMock(side_effect=UnknownLanguage()),
    )

    response = await anonymous_client.get(Paths.suggest, params={"query": "foo", "language": "en"})
    assert response.status_code == 422
    assert response.json() == {"detail": "Search engine not configured for given language"}
