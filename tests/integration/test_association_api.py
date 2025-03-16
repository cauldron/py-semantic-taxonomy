import pytest

from py_semantic_taxonomy.adapters.routers.router import Paths
from py_semantic_taxonomy.domain.constants import SKOS


@pytest.mark.postgres
async def test_get_association(postgres, cn_db_engine, cn, client):
    response = await client.get(Paths.association, params={"iri": cn.association_top["@id"]})
    assert response.status_code == 200
    given = response.json()

    for key, value in cn.association_top.items():
        assert given[key] == value


@pytest.mark.postgres
async def test_get_association_404(postgres, cn_db_engine, client):
    response = await client.get(
        Paths.association, params={"iri": "http://pyst-tests.ninja/association/missing"}
    )
    assert response.status_code == 404


@pytest.mark.postgres
async def test_create_association(postgres, cn_db_engine, cn, client):
    new = cn.association_top
    new["@id"] = "http://pyst-tests.ninja/association/new"

    response = await client.post(Paths.association, json=new)
    assert response.status_code == 200
    given = response.json()
    for key, value in new.items():
        assert given[key] == value

    given = (await client.get(Paths.association, params={"iri": new["@id"]})).json()
    for key, value in new.items():
        assert given[key] == value


@pytest.mark.postgres
async def test_create_association_duplicate(postgres, cn_db_engine, cn, client):
    response = await client.post(Paths.association, json=cn.association_top)
    assert response.status_code == 409


@pytest.mark.postgres
async def test_delete_association(postgres, cn_db_engine, cn, client):
    response = await client.get(Paths.association, params={"iri": cn.association_top["@id"]})
    assert response.status_code == 200
    assert response.json()

    response = await client.delete(Paths.association, params={"iri": cn.association_top["@id"]})
    assert response.status_code == 204

    response = await client.delete(Paths.association, params={"iri": cn.association_top["@id"]})
    assert response.status_code == 404

    response = await client.get(Paths.association, params={"iri": cn.association_top["@id"]})
    assert response.status_code == 404
