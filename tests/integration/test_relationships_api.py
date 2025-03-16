import orjson
import pytest

from py_semantic_taxonomy.adapters.routers.router import Paths
from py_semantic_taxonomy.domain.constants import SKOS, RelationshipVerbs
from py_semantic_taxonomy.domain.entities import Relationship


@pytest.mark.postgres
async def test_get_relationships(postgres, cn_db_engine, relationships, client):
    response = await client.get(Paths.relationship, params={"iri": relationships[1].source})
    assert response.status_code == 200
    assert response.json() == [
        {
            "@id": relationships[1].source,
            relationships[1].predicate.value: [{"@id": relationships[1].target}],
        }
    ], "API return value incorrect"


@pytest.mark.postgres
async def test_get_relationships_args(postgres, cn_db_engine, relationships, client):
    response = await client.get(
        Paths.relationship, params={"iri": relationships[1].source, "source": 0, "target": 1}
    )
    assert response.status_code == 200
    assert response.json() == [
        {
            "@id": relationships[2].source,
            relationships[2].predicate.value: [{"@id": relationships[2].target}],
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
    response = await client.post(Paths.relationship, json=[relationships[1].to_json_ld()])
    assert response.status_code == 409
    assert response.json() == {
        "message": "Relationship between source `http://data.europa.eu/xsp/cn2024/010021000090` and target `http://data.europa.eu/xsp/cn2024/010011000090` already exists"
    }, "API return value incorrect"


@pytest.mark.postgres
async def test_create_relationships_across_scheme(
    postgres, cn_db_engine, cn, client, relationships
):
    new_scheme = cn.scheme
    new_scheme["@id"] = "http://example.com/foo"
    await client.post(Paths.concept_scheme, json=new_scheme)

    new_concept = cn.concept_low
    new_concept[f"{SKOS}inScheme"] = [{"@id": "http://example.com/foo"}]
    if f"{SKOS}broader" in new_concept:
        del new_concept[f"{SKOS}broader"]
    new_concept["@id"] = "http://example.com/bar"
    await client.post(Paths.concept, json=new_concept)

    cross_cs = Relationship(
        source=relationships[1].source,
        target=new_concept["@id"],
        predicate=RelationshipVerbs.broader,
    )
    response = await client.post(Paths.relationship, json=[cross_cs.to_json_ld()])

    assert response.status_code == 422
    assert response.json() == {
        "message": f"Hierarchical relationship between `{cross_cs.source}` and `{cross_cs.target}` crosses Concept Schemes. Use an associative relationship like `skos:broadMatch` instead."
    }, "API return value incorrect"


@pytest.mark.postgres
async def test_create_relationships_reference_concept_scheme(
    postgres, cn_db_engine, cn, client, relationships
):
    rel = Relationship(
        source=cn.concept_low["@id"],
        target=cn.scheme["@id"],
        predicate=RelationshipVerbs.broader,
    )
    response = await client.post(Paths.relationship, json=[rel.to_json_ld()])

    assert response.status_code == 422
    assert response.json() == {
        "message": "Relationship `Relationship(source='http://data.europa.eu/xsp/cn2024/010100000080', target='http://data.europa.eu/xsp/cn2024/cn2024', predicate=<RelationshipVerbs.broader: 'http://www.w3.org/2004/02/skos/core#broader'>)` target refers to concept scheme `http://data.europa.eu/xsp/cn2024/cn2024`"
    }, "API return value incorrect"


@pytest.mark.postgres
async def test_update_relationships(postgres, cn_db_engine, client, relationships):
    updated = Relationship(
        source=relationships[1].source,
        target=relationships[1].target,
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
async def test_update_relationships_cross_cs_change_to_hierarchical(
    postgres, cn_db_engine, cn, client, relationships
):
    new_scheme = cn.scheme
    new_scheme["@id"] = "http://example.com/foo"
    await client.post(Paths.concept_scheme, json=new_scheme)

    new_concept = cn.concept_low
    new_concept[f"{SKOS}inScheme"] = [{"@id": "http://example.com/foo"}]
    if f"{SKOS}broader" in new_concept:
        del new_concept[f"{SKOS}broader"]
    new_concept["@id"] = "http://example.com/bar"
    await client.post(Paths.concept, json=new_concept)

    cross_cs = Relationship(
        source=relationships[1].source,
        target=new_concept["@id"],
        predicate=RelationshipVerbs.broad_match,
    )
    response = await client.post(Paths.relationship, json=[cross_cs.to_json_ld()])

    updated = Relationship(
        source=relationships[1].source,
        target=new_concept["@id"],
        predicate=RelationshipVerbs.broader,
    )
    response = await client.put(Paths.relationship, json=[updated.to_json_ld()])
    assert response.status_code == 422
    assert response.json() == {
        "message": "Hierarchical relationship between `http://data.europa.eu/xsp/cn2024/010021000090` and `http://example.com/bar` crosses Concept Schemes. Use an associative relationship like `skos:broadMatch` instead."
    }


@pytest.mark.postgres
async def test_relationship_delete(postgres, cn_db_engine, client, relationships):
    # https://www.python-httpx.org/compatibility/#request-body-on-http-methods
    response = await client.request(
        method="DELETE",
        url=Paths.relationship,
        content=orjson.dumps([relationships[1].to_json_ld()]),
    )
    assert response.status_code == 200
    assert response.json() == {
        "message": "Relationships (possibly) deleted",
        "count": 1,
    }

    response = await client.request(
        method="DELETE",
        url=Paths.relationship,
        content=orjson.dumps([relationships[1].to_json_ld()]),
    )
    assert response.status_code == 200
    assert response.json() == {
        "message": "Relationships (possibly) deleted",
        "count": 0,
    }
