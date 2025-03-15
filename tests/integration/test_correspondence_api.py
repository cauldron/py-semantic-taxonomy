import pytest

from py_semantic_taxonomy.adapters.routers.router import Paths


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
