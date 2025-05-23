from unittest.mock import AsyncMock

import orjson

from py_semantic_taxonomy.application.graph_service import GraphService
from py_semantic_taxonomy.domain.constants import XKOS
from py_semantic_taxonomy.domain.entities import (
    Correspondence,
    CorrespondenceNotFoundError,
    DuplicateIRI,
    MadeOf,
)
from py_semantic_taxonomy.domain.url_utils import get_full_api_path


async def test_correspondence_get(cn, anonymous_client, monkeypatch):
    monkeypatch.setattr(
        GraphService,
        "correspondence_get",
        AsyncMock(return_value=Correspondence.from_json_ld(cn.correspondence)),
    )

    response = await anonymous_client.get(
        get_full_api_path("correspondence", iri=cn.correspondence["@id"])
    )
    assert response.status_code == 200
    correspondence = response.json()
    for key, value in correspondence.items():
        if value:
            assert cn.correspondence[key] == value

    GraphService.correspondence_get.assert_called_once()
    assert isinstance(GraphService.correspondence_get.call_args[1]["iri"], str)


async def test_correspondence_get_not_found(cn, anonymous_client, monkeypatch):
    monkeypatch.setattr(
        GraphService, "correspondence_get", AsyncMock(side_effect=CorrespondenceNotFoundError())
    )

    response = await anonymous_client.get(get_full_api_path("correspondence", iri="foo"))
    correspondence = response.json()
    assert response.status_code == 404
    assert correspondence == {
        "detail": "Correspondence with IRI `foo` not found",
    }


async def test_correspondence_get_all(cn, anonymous_client, monkeypatch):
    monkeypatch.setattr(
        GraphService,
        "correspondence_get_all",
        AsyncMock(return_value=[Correspondence.from_json_ld(cn.correspondence)]),
    )

    response = await anonymous_client.get(get_full_api_path("correspondence_all"))
    assert response.status_code == 200
    correspondences = response.json()
    assert len(correspondences) == 1

    GraphService.correspondence_get_all.assert_called_once()


async def test_correspondence_create(cn, client, monkeypatch):
    monkeypatch.setattr(
        GraphService,
        "correspondence_create",
        AsyncMock(return_value=Correspondence.from_json_ld(cn.correspondence)),
    )

    response = await client.post(
        get_full_api_path("correspondence", iri=cn.correspondence["@id"]), json=cn.correspondence
    )
    assert response.status_code == 200

    GraphService.correspondence_create.assert_called_once()
    assert isinstance(GraphService.correspondence_create.call_args[0][0], Correspondence)


async def test_correspondence_create_unauthorized(anonymous_client, cn):
    response = await anonymous_client.post(
        get_full_api_path("correspondence", iri=cn.correspondence["@id"]), json=cn.correspondence
    )
    assert response.status_code == 400


async def test_correspondence_create_error_validation_errors(cn, client, monkeypatch):
    monkeypatch.setattr(GraphService, "correspondence_create", AsyncMock())

    obj = cn.correspondence
    obj[f"{XKOS}madeOf"] = []

    response = await client.post(get_full_api_path("correspondence", iri=obj["@id"]), json=obj)
    assert response.json()["detail"][0]["type"] == "value_error"
    assert (
        response.json()["detail"][0]["msg"]
        == "Value error, Found `http://rdf-vocabulary.ddialliance.org/xkos#madeOf` in new correspondence; use dedicated API calls for this data."
    )
    assert response.status_code == 422


async def test_correspondence_create_error_already_exists(cn, client, monkeypatch):
    monkeypatch.setattr(GraphService, "correspondence_create", AsyncMock(side_effect=DuplicateIRI))

    response = await client.post(
        get_full_api_path("correspondence", iri=cn.correspondence["@id"]), json=cn.correspondence
    )
    assert response.json() == {
        "detail": f"Correspondence with IRI `{cn.correspondence['@id']}` already exists",
    }
    assert response.status_code == 409


async def test_correspondence_update(cn, client, monkeypatch):
    monkeypatch.setattr(
        GraphService,
        "correspondence_update",
        AsyncMock(return_value=Correspondence.from_json_ld(cn.correspondence)),
    )

    updated = cn.correspondence
    response = await client.put(
        get_full_api_path("correspondence", iri=updated["@id"]), json=updated
    )
    assert response.status_code == 200

    GraphService.correspondence_update.assert_called_once()
    assert isinstance(GraphService.correspondence_update.call_args[0][0], Correspondence)


async def test_correspondence_update_unauthorized(anonymous_client, cn):
    response = await anonymous_client.put(
        get_full_api_path("correspondence", iri=cn.correspondence["@id"]), json=cn.correspondence
    )
    assert response.status_code == 400


async def test_correspondence_update_error_validation_errors(cn, client, monkeypatch):
    monkeypatch.setattr(GraphService, "correspondence_update", AsyncMock())

    obj = cn.correspondence
    obj[f"{XKOS}madeOf"] = ["a"]

    response = await client.put(get_full_api_path("correspondence", iri=obj["@id"]), json=obj)
    assert response.json()["detail"][0]["type"] == "value_error"
    assert (
        response.json()["detail"][0]["msg"]
        == "Value error, Found `http://rdf-vocabulary.ddialliance.org/xkos#madeOf` in new correspondence; use dedicated API calls for this data."
    )
    assert response.status_code == 422


async def test_correspondence_update_error_missing(cn, client, monkeypatch):
    monkeypatch.setattr(
        GraphService, "correspondence_update", AsyncMock(side_effect=CorrespondenceNotFoundError)
    )

    obj = cn.correspondence
    obj["@id"] = "http://pyst-tests.ninja/correspondence/missing"

    response = await client.put(get_full_api_path("correspondence", iri=obj["@id"]), json=obj)
    assert response.json() == {"detail": f"Correspondence with IRI `{obj['@id']}` not found"}
    assert response.status_code == 404


async def test_correspondence_delete(cn, client, monkeypatch):
    monkeypatch.setattr(GraphService, "correspondence_delete", AsyncMock(return_value=1))

    response = await client.delete(
        get_full_api_path("correspondence", iri=cn.correspondence["@id"])
    )
    assert response.status_code == 204

    GraphService.correspondence_delete.assert_called_once()
    assert isinstance(GraphService.correspondence_delete.call_args[1]["iri"], str)


async def test_correspondence_delete_unauthorized(anonymous_client, cn):
    response = await anonymous_client.delete(
        get_full_api_path("correspondence", iri=cn.correspondence["@id"])
    )
    assert response.status_code == 400


async def test_correspondence_delete_not_found(cn, client, monkeypatch):
    monkeypatch.setattr(
        GraphService,
        "correspondence_delete",
        AsyncMock(side_effect=CorrespondenceNotFoundError("Test")),
    )

    response = await client.delete(
        get_full_api_path("correspondence", iri=cn.correspondence["@id"])
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Test"}


async def test_made_of_add(cn, made_of, client, monkeypatch):
    monkeypatch.setattr(
        GraphService,
        "made_of_add",
        AsyncMock(return_value=Correspondence.from_json_ld(cn.correspondence)),
    )

    response = await client.post(get_full_api_path("made_of"), json=made_of.to_json_ld())
    assert response.status_code == 200
    given = response.json()
    for key, value in cn.correspondence.items():
        assert given[key] == value

    GraphService.made_of_add.assert_called_once()
    assert isinstance(GraphService.made_of_add.call_args[0][0], MadeOf)


async def test_made_of_add_unauthorized(anonymous_client):
    response = await anonymous_client.post(get_full_api_path("made_of"), json={})
    assert response.status_code == 400


async def test_made_of_add_missing(cn, made_of, client, monkeypatch):
    monkeypatch.setattr(
        GraphService, "made_of_add", AsyncMock(side_effect=CorrespondenceNotFoundError)
    )

    response = await client.post(get_full_api_path("made_of"), json=made_of.to_json_ld())
    assert response.json() == {"detail": f"Correspondence with IRI `{made_of.id_}` not found"}
    assert response.status_code == 404


async def test_made_of_remove(cn, made_of, client, monkeypatch):
    monkeypatch.setattr(
        GraphService,
        "made_of_remove",
        AsyncMock(return_value=Correspondence.from_json_ld(cn.correspondence)),
    )

    # https://www.python-httpx.org/compatibility/#request-body-on-http-methods
    response = await client.request(
        method="DELETE",
        url=get_full_api_path("made_of"),
        content=orjson.dumps(made_of.to_json_ld()),
    )
    assert response.status_code == 200
    given = response.json()
    for key, value in cn.correspondence.items():
        assert given[key] == value

    GraphService.made_of_remove.assert_called_once()
    assert isinstance(GraphService.made_of_remove.call_args[0][0], MadeOf)


async def test_made_of_remove_unauthorized(anonymous_client):
    response = await anonymous_client.request(
        method="DELETE",
        url=get_full_api_path("made_of"),
        content=orjson.dumps([]),
    )
    assert response.status_code == 400


async def test_made_of_remove_missing(cn, made_of, client, monkeypatch):
    monkeypatch.setattr(
        GraphService, "made_of_remove", AsyncMock(side_effect=CorrespondenceNotFoundError)
    )

    response = await client.request(
        method="DELETE",
        url=get_full_api_path("made_of"),
        content=orjson.dumps(made_of.to_json_ld()),
    )
    assert response.json() == {"detail": f"Correspondence with IRI `{made_of.id_}` not found"}
    assert response.status_code == 404
