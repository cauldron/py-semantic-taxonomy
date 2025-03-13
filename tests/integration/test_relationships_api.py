import orjson
import pytest

from py_semantic_taxonomy.adapters.routers.router import Paths
from py_semantic_taxonomy.domain.constants import RelationshipVerbs
from py_semantic_taxonomy.domain.entities import Relationship


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


@pytest.mark.postgres
async def test_update_relationships(postgres, cn_db_engine, client, relationships):
    updated = Relationship(
        source=relationships[0].source,
        target=relationships[0].target,
        predicate=RelationshipVerbs.exact_match,
    )
    response = await client.put(Paths.relationship, json=[updated.to_json_ld()])
    assert response.status_code == 200
    assert response.json() == [updated.to_json_ld()]

    response = await client.get(Paths.relationship, params={"iri": updated.source})
    assert response.status_code == 200
    assert response.json() == [updated.to_json_ld()]


@pytest.mark.postgres
async def test_update_relationships_not_found(postgres, cn_db_engine, client, relationships):
    updated = Relationship(
        source="http://example.com/foo",
        target="http://example.com/bar",
        predicate=RelationshipVerbs.exact_match,
    )
    response = await client.put(Paths.relationship, json=[updated.to_json_ld()])
    assert response.status_code == 404
    assert response.json() == {
        "message": "Can't update non-existent relationship between source `http://example.com/foo` and target `http://example.com/bar`"
    }


@pytest.mark.postgres
async def test_relationship_delete(postgres, cn_db_engine, client, relationships):
    # https://www.python-httpx.org/compatibility/#request-body-on-http-methods
    response = await client.request(
        method="DELETE",
        url=Paths.relationship,
        content=orjson.dumps([relationships[0].to_json_ld()]),
    )
    assert response.status_code == 200
    assert response.json() == {
        "message": "Relationships (possibly) deleted",
        "count": 1,
    }

    response = await client.request(
        method="DELETE",
        url=Paths.relationship,
        content=orjson.dumps([relationships[0].to_json_ld()]),
    )
    assert response.status_code == 200
    assert response.json() == {
        "message": "Relationships (possibly) deleted",
        "count": 0,
    }
