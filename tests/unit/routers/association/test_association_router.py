from unittest.mock import AsyncMock

from py_semantic_taxonomy.adapters.routers.router import GraphService, Paths
from py_semantic_taxonomy.domain.constants import RDF_MAPPING, SKOS
from py_semantic_taxonomy.domain.entities import (
    Association,
    AssociationNotFoundError,
    DuplicateIRI,
)


async def test_association_get(cn, client, monkeypatch):
    monkeypatch.setattr(
        GraphService,
        "association_get",
        AsyncMock(return_value=Association.from_json_ld(cn.association_top)),
    )

    response = await client.get(Paths.association, params={"iri": cn.association_top["@id"]})
    assert response.status_code == 200
    for key, value in response.json().items():
        if value:
            assert cn.association_top[key] == value

    GraphService.association_get.assert_called_once()
    assert isinstance(GraphService.association_get.call_args[1]["iri"], str)


async def test_association_get_not_found(cn, client, monkeypatch):
    monkeypatch.setattr(
        GraphService, "association_get", AsyncMock(side_effect=AssociationNotFoundError())
    )

    response = await client.get(Paths.association, params={"iri": "foo"})
    assert response.status_code == 404
    assert response.json() == {
        "message": "Association with IRI 'foo' not found",
        "detail": {"iri": "foo"},
    }


async def test_association_create(cn, client, monkeypatch):
    monkeypatch.setattr(
        GraphService,
        "association_create",
        AsyncMock(return_value=Association.from_json_ld(cn.association_top)),
    )

    response = await client.post(Paths.association, json=cn.association_top)
    assert response.status_code == 200

    GraphService.association_create.assert_called_once()
    assert isinstance(GraphService.association_create.call_args[0][0], Association)


async def test_association_create_error_validation_errors(cn, client, monkeypatch):
    monkeypatch.setattr(GraphService, "association_create", AsyncMock())

    obj = cn.association_top
    del obj[RDF_MAPPING["source_concepts"]]

    response = await client.post(Paths.association, json=obj)
    assert response.json()["detail"][0]["type"] == "missing"
    assert response.json()["detail"][0]["loc"] == ["body", RDF_MAPPING["source_concepts"]]
    assert response.status_code == 422


async def test_association_create_error_already_exists(cn, client, monkeypatch):
    monkeypatch.setattr(
        GraphService, "association_create", AsyncMock(side_effect=DuplicateIRI("Test message"))
    )

    response = await client.post(Paths.association, json=cn.association_top)
    assert response.json() == {"detail": "Test message"}
    assert response.status_code == 409


async def test_association_delete(cn, client, monkeypatch):
    monkeypatch.setattr(GraphService, "association_delete", AsyncMock())

    response = await client.delete(Paths.association, params={"iri": cn.association_top["@id"]})
    assert response.status_code == 204

    GraphService.association_delete.assert_called_once()
    assert isinstance(GraphService.association_delete.call_args[1]["iri"], str)


async def test_association_delete_missing(cn, client, monkeypatch):
    monkeypatch.setattr(
        GraphService,
        "association_delete",
        AsyncMock(side_effect=AssociationNotFoundError("Problem")),
    )

    response = await client.delete(Paths.association, params={"iri": cn.association_top["@id"]})
    assert response.json() == {"detail": "Problem"}
    assert response.status_code == 404
