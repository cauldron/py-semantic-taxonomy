from unittest.mock import AsyncMock

from py_semantic_taxonomy.adapters.routers.router import GraphService, Paths
from py_semantic_taxonomy.domain.constants import XKOS
from py_semantic_taxonomy.domain.entities import (
    Correspondence,
    CorrespondenceNotFoundError,
    DuplicateIRI,
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


async def test_correspondence_create(cn, client, monkeypatch):
    monkeypatch.setattr(
        GraphService,
        "correspondence_create",
        AsyncMock(return_value=Correspondence.from_json_ld(cn.correspondence)),
    )

    response = await client.post(Paths.correspondence, json=cn.correspondence)
    assert response.status_code == 200

    GraphService.correspondence_create.assert_called_once()
    assert isinstance(GraphService.correspondence_create.call_args[0][0], Correspondence)


async def test_correspondence_create_error_validation_errors(cn, client, monkeypatch):
    monkeypatch.setattr(GraphService, "correspondence_create", AsyncMock())

    obj = cn.correspondence
    obj[f"{XKOS}madeOf"] = []

    response = await client.post(Paths.correspondence, json=obj)
    print(response.json())
    assert response.json()["detail"][0]["type"] == "value_error"
    assert (
        response.json()["detail"][0]["msg"]
        == "Value error, Found `http://rdf-vocabulary.ddialliance.org/xkos#madeOf` in new correspondence; use dedicated API calls for this data."
    )
    assert response.status_code == 422


async def test_correspondence_create_error_already_exists(cn, client, monkeypatch):
    monkeypatch.setattr(GraphService, "correspondence_create", AsyncMock(side_effect=DuplicateIRI))

    response = await client.post(Paths.correspondence, json=cn.correspondence)
    assert response.json() == {
        "message": "Resource with `@id` already exists",
        "detail": {"@id": "http://pyst-tests.ninja/correspondence/cn2023_cn2024"},
    }
    assert response.status_code == 409
