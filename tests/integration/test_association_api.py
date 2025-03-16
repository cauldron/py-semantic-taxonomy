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
