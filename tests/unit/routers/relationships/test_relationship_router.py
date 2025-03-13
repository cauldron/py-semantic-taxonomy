from unittest.mock import AsyncMock

import orjson

from py_semantic_taxonomy.adapters.routers.router import GraphService, Paths
from py_semantic_taxonomy.domain.constants import RelationshipVerbs
from py_semantic_taxonomy.domain.entities import (
    DuplicateRelationship,
    Relationship,
    RelationshipNotFoundError,
)


async def test_relationships_get(cn, client, monkeypatch, relationships):
    monkeypatch.setattr(
        GraphService, "relationships_get", AsyncMock(return_value=[relationships[0]])
    )

    response = await client.get(Paths.relationship, params={"iri": relationships[0].source})
    assert response.status_code == 200
    assert response.json() == [
        {
            "@id": relationships[0].source,
            relationships[0].predicate.value: [{"@id": relationships[0].target}],
        }
    ], "API return value incorrect"

    GraphService.relationships_get.assert_called_once()
    assert isinstance(GraphService.relationships_get.call_args[1]["iri"], str)
    assert isinstance(GraphService.relationships_get.call_args[1]["source"], bool)
    assert isinstance(GraphService.relationships_get.call_args[1]["target"], bool)


async def test_relationships_get_args(cn, client, monkeypatch, relationships):
    monkeypatch.setattr(
        GraphService, "relationships_get", AsyncMock(return_value=[relationships[0]])
    )

    response = await client.get(Paths.relationship, params={"iri": relationships[0].source})
    assert response.status_code == 200
    GraphService.relationships_get.assert_called_with(
        iri=relationships[0].source, source=True, target=False
    )

    response = await client.get(
        Paths.relationship, params={"iri": relationships[0].source, "target": 1}
    )
    assert response.status_code == 200
    GraphService.relationships_get.assert_called_with(
        iri=relationships[0].source, source=True, target=True
    )

    response = await client.get(
        Paths.relationship, params={"iri": relationships[0].source, "source": 0, "target": 1}
    )
    assert response.status_code == 200
    GraphService.relationships_get.assert_called_with(
        iri=relationships[0].source, source=False, target=True
    )


async def test_relationship_create(relationships, client, monkeypatch):
    monkeypatch.setattr(GraphService, "relationships_create", AsyncMock(return_value=relationships))

    response = await client.post(
        Paths.relationship, json=[obj.to_json_ld() for obj in relationships]
    )
    assert response.status_code == 200
    assert Relationship.from_json_ld_list(response.json()) == relationships

    GraphService.relationships_create.assert_called_once()
    assert isinstance(GraphService.relationships_create.call_args[0][0], list)
    assert isinstance(GraphService.relationships_create.call_args[0][0][0], Relationship)


async def test_relationship_create_already_exists(relationships, client, monkeypatch):
    monkeypatch.setattr(
        GraphService,
        "relationships_create",
        AsyncMock(side_effect=DuplicateRelationship("Already exists")),
    )

    response = await client.post(
        Paths.relationship, json=[obj.to_json_ld() for obj in relationships]
    )
    assert response.status_code == 409
    assert response.json() == {"message": "Already exists"}


async def test_relationships_create_error_validation_errors_zero_relatioships(
    relationships, client, monkeypatch
):
    monkeypatch.setattr(GraphService, "relationships_create", AsyncMock())

    given = [
        {
            "@id": relationships[0].source,
        }
    ]

    response = await client.post(Paths.relationship, json=given)
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "value_error"
    assert response.json()["detail"][0]["msg"] == "Value error, Found zero relationships"


async def test_relationships_create_error_validation_errors_multiple_same_kind(
    relationships, client, monkeypatch
):
    monkeypatch.setattr(GraphService, "relationships_create", AsyncMock())

    given = [
        {
            "@id": relationships[0].source,
            RelationshipVerbs.broader.value: [
                {"@id": relationships[1].source},
                {"@id": relationships[0].target},
            ],
        }
    ]

    response = await client.post(Paths.relationship, json=given)
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "value_error"
    assert (
        response.json()["detail"][0]["msg"]
        == "Value error, Found multiple relationships of type `broader`"
    )


async def test_relationships_create_error_validation_errors_multiple_different_kinds(
    relationships, client, monkeypatch
):
    monkeypatch.setattr(GraphService, "relationships_create", AsyncMock())

    given = [
        {
            "@id": relationships[0].source,
            RelationshipVerbs.broader.value: [{"@id": relationships[0].target}],
            RelationshipVerbs.exact_match.value: [{"@id": relationships[1].source}],
        }
    ]

    response = await client.post(Paths.relationship, json=given)
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "value_error"
    assert (
        response.json()["detail"][0]["msg"]
        == "Value error, Found multiple relationships ['broader', 'exact_match'] where only one is allowed"
    )


async def test_relationships_create_error_validation_errors_self_reference(
    relationships, client, monkeypatch
):
    monkeypatch.setattr(GraphService, "relationships_create", AsyncMock())

    given = [
        {
            "@id": relationships[0].source,
            RelationshipVerbs.broader.value: [
                {"@id": relationships[0].source},
            ],
        }
    ]

    response = await client.post(Paths.relationship, json=given)
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "value_error"
    assert (
        response.json()["detail"][0]["msg"]
        == "Value error, Relationship has same source and target"
    )


async def test_relationships_update(relationships, client, monkeypatch):
    monkeypatch.setattr(GraphService, "relationships_update", AsyncMock(return_value=relationships))

    updated = Relationship(
        source=relationships[0].source,
        target=relationships[0].target,
        predicate=RelationshipVerbs.exact_match,
    )
    response = await client.put(Paths.relationship, json=[updated.to_json_ld()])
    assert response.status_code == 200
    assert response.json()

    GraphService.relationships_update.assert_called_once()
    assert isinstance(GraphService.relationships_update.call_args[0][0], list)
    assert isinstance(GraphService.relationships_update.call_args[0][0][0], Relationship)


async def test_relationship_update_error_missing(relationships, client, monkeypatch):
    monkeypatch.setattr(
        GraphService,
        "relationships_update",
        AsyncMock(side_effect=RelationshipNotFoundError("Test message")),
    )

    response = await client.put(Paths.relationship, json=[relationships[0].to_json_ld()])
    assert response.status_code == 404
    assert response.json() == {
        "message": "Test message",
    }


async def test_relationship_delete(relationships, client, monkeypatch):
    monkeypatch.setattr(GraphService, "relationships_delete", AsyncMock(return_value=1))

    # https://www.python-httpx.org/compatibility/#request-body-on-http-methods
    response = await client.request(
        method="DELETE",
        url=Paths.relationship,
        content=orjson.dumps([relationships[0].to_json_ld()]),
    )
    assert response.status_code == 200
    assert response.json() == {
        "message": "Relationships (possibly) deleted",
        "count": 1,
    }
    GraphService.relationships_delete.assert_called_once()
    assert isinstance(GraphService.relationships_delete.call_args[0][0], list)
    assert isinstance(GraphService.relationships_delete.call_args[0][0][0], Relationship)
