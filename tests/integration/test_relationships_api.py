import pytest

from py_semantic_taxonomy.adapters.routers.router import Paths
from py_semantic_taxonomy.domain.constants import RelationshipVerbs


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


@pytest.mark.postgres
async def test_create_relationships(postgres, cn_db_engine, client):
    given = [
        {
            "@id": "http://example.com/foo",
            RelationshipVerbs.broader.value: [{"@id": "http://example.com/bar"}],
        }
    ]

    response = await client.post(Paths.relationship, json=given)
    assert response.status_code == 200
    assert response.json() == given, "API return value incorrect"

    response = await client.get(Paths.relationship, params={"iri": "http://example.com/foo"})
    assert response.status_code == 200
    assert response.json() == given


@pytest.mark.postgres
async def test_create_relationships_duplicate(postgres, cn_db_engine, client, relationships):
    response = await client.post(Paths.relationship, json=[relationships[0].to_json_ld()])
    assert response.status_code == 409
    assert response.json() == {
        "message": "Relationship between source `http://data.europa.eu/xsp/cn2024/010021000090` and target `http://data.europa.eu/xsp/cn2024/010011000090` already exists"
    }, "API return value incorrect"
