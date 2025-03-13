from unittest.mock import AsyncMock

import orjson

from py_semantic_taxonomy.adapters.routers.router import GraphService, Paths
from py_semantic_taxonomy.domain.constants import RelationshipVerbs
from py_semantic_taxonomy.domain.entities import Relationship


async def test_relationships_get(cn, client, monkeypatch, relationships):
    monkeypatch.setattr(
        GraphService, "relationships_get", AsyncMock(return_value=[relationships[0]])
    )

    response = await client.get(Paths.relationship, params={"iri": relationships[0].source})
    assert response.status_code == 200
    rels = orjson.loads(response.content)
    assert rels == [
        {
            "@id": relationships[0].source,
            relationships[0].predicate.value: [{"@id": relationships[0].target}],
        }
    ], "API return value incorrect"


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
