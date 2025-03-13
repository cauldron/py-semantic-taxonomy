import pytest

from py_semantic_taxonomy.adapters.routers.router import Paths


@pytest.mark.postgres
async def test_get_relationships(postgres, cn_db_engine, relationships, client):
    response = await client.get(Paths.relationship, params={"iri": relationships[0].source})
    assert response.status_code == 200
    assert response.json() == [
        {
            "@id": relationships[0].source,
            relationships[0].predicate.value: [{"@id": relationships[0].target}],
        }
    ], "API return value incorrect"


@pytest.mark.postgres
async def test_get_relationships_args(postgres, cn_db_engine, relationships, client):
    response = await client.get(
        Paths.relationship, params={"iri": relationships[0].source, "source": 0, "target": 1}
    )
    assert response.status_code == 200
    assert response.json() == [
        {
            "@id": relationships[1].source,
            relationships[1].predicate.value: [{"@id": relationships[1].target}],
        }
    ], "API return value incorrect"


@pytest.mark.postgres
async def test_get_relationships_empty(postgres, cn_db_engine, client):
    response = await client.get(
        Paths.relationship, params={"iri": "http://data.europa.eu/xsp/cn2024/woof"}
    )
    assert response.status_code == 200
    assert response.json() == []
