from unittest.mock import AsyncMock

from py_semantic_taxonomy.adapters.routers.router import GraphService, Paths
from py_semantic_taxonomy.domain.entities import (
    Correspondence,
    CorrespondenceNotFoundError,
)


async def test_correspondence(cn, client, monkeypatch):
    monkeypatch.setattr(
        GraphService,
        "correspondence_get",
        AsyncMock(return_value=Correspondence.from_json_ld(cn.correspondence)),
    )

    response = await client.get(Paths.correspondence, params={"iri": cn.correspondence["@id"]})
    assert response.status_code == 200
    correspondence = response.json()
    for key, value in correspondence.items():
        if value:
            assert cn.correspondence[key] == value

    GraphService.correspondence_get.assert_called_once()
    assert isinstance(GraphService.correspondence_get.call_args[1]["iri"], str)


async def test_correspondence_get_not_found(cn, client, monkeypatch):
    monkeypatch.setattr(
        GraphService, "correspondence_get", AsyncMock(side_effect=CorrespondenceNotFoundError())
    )

    response = await client.get(Paths.correspondence, params={"iri": "foo"})
    correspondence = response.json()
    assert response.status_code == 404
    assert correspondence == {
        "message": "Correspondence with IRI 'foo' not found",
        "detail": {"iri": "foo"},
    }
