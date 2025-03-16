import pytest

from py_semantic_taxonomy.adapters.routers.router import Paths
from py_semantic_taxonomy.domain.constants import SKOS


@pytest.mark.postgres
async def test_get_correspondence(postgres, cn_db_engine, cn, client):
    response = await client.get(Paths.correspondence, params={"iri": cn.correspondence["@id"]})
    assert response.status_code == 200
    given = response.json()

    for key, value in cn.correspondence.items():
        assert given[key] == value


@pytest.mark.postgres
async def test_get_correspondence_404(postgres, cn_db_engine, client):
    response = await client.get(
        Paths.correspondence, params={"iri": "http://pyst-tests.ninja/correspondence/missing"}
    )
    assert response.status_code == 404


@pytest.mark.postgres
async def test_create_correspondence(postgres, cn_db_engine, cn, client):
    new = cn.correspondence
    new["@id"] = "http://pyst-tests.ninja/correspondence/new"

    response = await client.post(Paths.correspondence, json=new)
    assert response.status_code == 200
    given = response.json()
    for key, value in new.items():
        assert given[key] == value

    given = (await client.get(Paths.correspondence, params={"iri": new["@id"]})).json()
    for key, value in new.items():
        assert given[key] == value


@pytest.mark.postgres
async def test_create_correspondence_duplicate(postgres, cn_db_engine, cn, client):
    response = await client.post(Paths.correspondence, json=cn.correspondence)
    assert response.status_code == 409


@pytest.mark.postgres
async def test_update_correspondence(postgres, cn_db_engine, cn, client):
    updated = cn.correspondence
    updated[f"{SKOS}prefLabel"] = [{"@value": "Don't read my correspondence", "@language": "en"}]

    response = await client.put(Paths.correspondence, json=updated)
    assert response.status_code == 200
    given = response.json()
    for key, value in updated.items():
        assert given[key] == value

    given = (await client.get(Paths.correspondence, params={"iri": updated["@id"]})).json()
    for key, value in updated.items():
        assert given[key] == value


@pytest.mark.postgres
async def test_update_correspondence_not_found(postgres, cn_db_engine, cn, client):
    obj = cn.correspondence
    obj["@id"] = "http://pyst-tests.ninja/correspondence/missing"

    response = await client.put(Paths.correspondence, json=obj)
    assert response.status_code == 404


@pytest.mark.postgres
async def test_delete_correspondence(postgres, cn_db_engine, cn, client):
    response = await client.get(Paths.correspondence, params={"iri": cn.correspondence["@id"]})
    assert response.status_code == 200
    assert response.json()

    response = await client.delete(Paths.correspondence, params={"iri": cn.correspondence["@id"]})
    assert response.status_code == 204

    response = await client.delete(Paths.correspondence, params={"iri": cn.correspondence["@id"]})
    assert response.status_code == 404

    response = await client.get(Paths.correspondence, params={"iri": cn.correspondence["@id"]})
    assert response.status_code == 404
