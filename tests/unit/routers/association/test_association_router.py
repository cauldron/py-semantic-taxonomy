from unittest.mock import AsyncMock

from py_semantic_taxonomy.adapters.routers.router import GraphService, Paths
from py_semantic_taxonomy.domain.constants import SKOS
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
