import pytest

from py_semantic_taxonomy.domain.constants import RDF_MAPPING as RDF
from py_semantic_taxonomy.domain.constants import (
    SKOS,
    SKOS_RELATIONSHIP_PREDICATES,
)
from py_semantic_taxonomy.domain.url_utils import get_full_api_path


@pytest.mark.postgres
async def test_get_concept(postgres, cn_db_engine, cn, client):
    response = await client.get(get_full_api_path("concept", iri=cn.concept_top["@id"]))
    assert response.status_code == 200
    expected = {
        key: value
        for key, value in cn.concept_top.items()
        if key not in SKOS_RELATIONSHIP_PREDICATES
    }
    given = response.json()

    # https://fastapi.tiangolo.com/tutorial/response-model/#response-model-encoding-parameters
    # Child models don't call `model_dump`, which means that `exclude_unset` or `by_alias` is
    # ignored. See https://github.com/pydantic/pydantic/issues/8792
    for key, value in expected.items():
        assert given[key] == value


@pytest.mark.postgres
async def test_get_concept_404(postgres, cn_db_engine, client):
    response = await client.get(
        get_full_api_path("concept", iri="http://data.europa.eu/xsp/cn2024/woof")
    )
    assert response.status_code == 404


@pytest.mark.postgres
async def test_get_concept_all_with_concept_scheme(postgres, cn_db_engine, cn, client):
    response = await client.get(
        get_full_api_path("concept_all"), params={"concept_scheme_iri": cn.scheme["@id"]}
    )
    assert response.status_code == 200
    expected = {
        key: value
        for key, value in cn.concept_top.items()
        if key not in SKOS_RELATIONSHIP_PREDICATES
    }
    given = response.json()
    assert isinstance(given, list)
    assert len(given) == 2
    for key, value in expected.items():
        assert given[0][key] == value

    assert [obj["@id"] for obj in given] == sorted([cn.concept_top["@id"], cn.concept_mid["@id"]])


@pytest.mark.postgres
async def test_get_concept_all_with_concept_scheme_top_concepts(postgres, cn_db_engine, cn, client):
    response = await client.get(
        get_full_api_path("concept_all"),
        params={"concept_scheme_iri": cn.scheme["@id"], "top_concepts_only": 1},
    )
    assert response.status_code == 200
    given = response.json()
    assert isinstance(given, list)
    assert len(given) == 1
    assert given[0]["@id"] == cn.concept_top["@id"]


@pytest.mark.postgres
async def test_get_concept_all(postgres, cn_db_engine, cn, client):
    response = await client.get(get_full_api_path("concept_all"))
    assert response.status_code == 200
    given = response.json()
    assert isinstance(given, list)
    assert len(given) == 4
    assert [obj["@id"] for obj in given] == sorted(
        [
            cn.concept_top["@id"],
            cn.concept_mid["@id"],
            cn.concept_2023_top["@id"],
            cn.concept_2023_low["@id"],
        ]
    )


@pytest.mark.postgres
async def test_get_concept_all_top_concepts_without_concept_scheme(
    postgres, cn_db_engine, cn, client
):
    response = await client.get(get_full_api_path("concept_all"), params={"top_concepts_only": 1})
    assert response.status_code == 200
    given = response.json()
    assert isinstance(given, list)
    assert len(given) == 4
    assert [obj["@id"] for obj in given] == sorted(
        [
            cn.concept_top["@id"],
            cn.concept_mid["@id"],
            cn.concept_2023_top["@id"],
            cn.concept_2023_low["@id"],
        ]
    )


@pytest.mark.postgres
async def test_create_concept(postgres, cn_db_engine, cn, client):
    # Broader relationship already given in `cn_db_engine` fixture
    del cn.concept_low[f"{SKOS}broader"]
    response = await client.post(
        get_full_api_path("concept", iri=cn.concept_low["@id"]), json=cn.concept_low
    )
    assert response.status_code == 200
    expected = {
        key: value
        for key, value in cn.concept_low.items()
        if key not in SKOS_RELATIONSHIP_PREDICATES
    }
    given = response.json()

    # https://fastapi.tiangolo.com/tutorial/response-model/#response-model-encoding-parameters
    # Child models don't call `model_dump`, which means that `exclude_unset` or `by_alias` is
    # ignored. See https://github.com/pydantic/pydantic/issues/8792
    for key, value in expected.items():
        assert given[key] == value

    given = (await client.get(get_full_api_path("concept", iri=cn.concept_low["@id"]))).json()
    for key, value in expected.items():
        assert given[key] == value


@pytest.mark.postgres
async def test_create_concept_concept_scheme_not_in_database(postgres, cn_db_engine, cn, client):
    updated = cn.concept_top
    if f"{SKOS}narrower" in updated:
        del updated[f"{SKOS}narrower"]

    updated[f"{SKOS}inScheme"] = [{"@id": "http://example.com/foo"}]

    response = await client.post(get_full_api_path("concept", iri=updated["@id"]), json=updated)
    assert response.status_code == 422
    assert response.json() == {
        "detail": "At least one of the specified concept schemes must be in the database: {'http://example.com/foo'}"
    }


@pytest.mark.postgres
async def test_create_concept_hierarchy_conflict(postgres, cn_db_engine, cn, client):
    new = cn.concept_low
    new[RDF["top_concept_of"]] = [{"@id": cn.scheme["@id"]}]

    response = await client.post(get_full_api_path("concept", iri=new["@id"]), json=new)
    assert response.status_code == 422
    assert response.json() == {
        "detail": f"Concept is marked as `topConceptOf` but also has broader relationship to `{cn.concept_mid['@id']}`"
    }


@pytest.mark.postgres
async def test_create_concept_relationships(postgres, cn_db_engine, cn, client):
    # Broader relationship already given in `cn_db_engine` fixture
    cn.concept_low[f"{SKOS}broader"] = [{"@id": "http://example.com/foo"}]
    cn.concept_low[f"{SKOS}exactMatch"] = [{"@id": "http://example.com/bar"}]
    response = await client.post(
        get_full_api_path("concept", iri=cn.concept_low["@id"]), json=cn.concept_low
    )
    assert response.status_code == 200
    expected = {
        key: value
        for key, value in cn.concept_low.items()
        if key not in SKOS_RELATIONSHIP_PREDICATES
    }
    given = response.json()

    # https://fastapi.tiangolo.com/tutorial/response-model/#response-model-encoding-parameters
    # Child models don't call `model_dump`, which means that `exclude_unset` or `by_alias` is
    # ignored. See https://github.com/pydantic/pydantic/issues/8792
    for key, value in expected.items():
        assert given[key] == value

    given = (await client.get(get_full_api_path("concept", iri=cn.concept_low["@id"]))).json()
    for key, value in expected.items():
        assert given[key] == value

    given = (
        await client.get(get_full_api_path("relationship"), params={"iri": cn.concept_low["@id"]})
    ).json()
    assert {
        "@id": cn.concept_low["@id"],
        f"{SKOS}broader": [{"@id": "http://example.com/foo"}],
    } in given, "Missing relationship"
    assert {
        "@id": cn.concept_low["@id"],
        f"{SKOS}exactMatch": [{"@id": "http://example.com/bar"}],
    } in given, "Missing relationship"


@pytest.mark.postgres
async def test_create_concept_relationships_across_scheme(
    postgres, cn_db_engine, cn, client, relationships
):
    new_scheme = cn.scheme
    new_scheme["@id"] = "http://example.com/foo"
    await client.post(get_full_api_path("concept_scheme", iri=new_scheme["@id"]), json=new_scheme)

    new_concept = cn.concept_low
    new_concept[f"{SKOS}inScheme"] = [{"@id": "http://example.com/foo"}]
    new_concept["@id"] = "http://example.com/bar"
    response = await client.post(
        get_full_api_path("concept", iri=new_concept["@id"]), json=new_concept
    )

    assert response.status_code == 422
    assert response.json()["detail"].endswith(
        "`skos:broadMatch` instead."
    ), "API return value incorrect"

    response = await client.get(get_full_api_path("concept", iri=new_concept["@id"]))
    assert response.status_code == 404


@pytest.mark.postgres
async def test_create_concept_relationships_duplicate(
    postgres, cn_db_engine, cn, client, relationships
):
    new_concept = cn.concept_low
    new_concept[f"{SKOS}broader"].extend(new_concept[f"{SKOS}broader"])
    response = await client.post(
        get_full_api_path("concept", iri=new_concept["@id"]), json=new_concept
    )

    assert response.status_code == 422
    assert response.json()["detail"].endswith("already exists"), "API return value incorrect"

    response = await client.get(get_full_api_path("concept", iri=new_concept["@id"]))
    assert response.status_code == 404


@pytest.mark.postgres
async def test_create_concept_duplicate(postgres, cn_db_engine, cn, client):
    response = await client.post(
        get_full_api_path("concept", iri=cn.concept_top["@id"]), json=cn.concept_top
    )
    assert response.status_code == 409


@pytest.mark.postgres
async def test_update_concept(postgres, cn_db_engine, cn, client):
    updated = cn.concept_top
    updated[RDF["alt_labels"]] = [{"@value": "Dream a little dream", "@language": "en"}]
    if f"{SKOS}narrower" in updated:
        del updated[f"{SKOS}narrower"]

    response = await client.put(get_full_api_path("concept", iri=updated["@id"]), json=updated)
    assert response.status_code == 200
    expected = {
        key: value for key, value in updated.items() if key not in SKOS_RELATIONSHIP_PREDICATES
    }
    given = response.json()

    # https://fastapi.tiangolo.com/tutorial/response-model/#response-model-encoding-parameters
    # Child models don't call `model_dump`, which means that `exclude_unset` or `by_alias` is
    # ignored. See https://github.com/pydantic/pydantic/issues/8792
    for key, value in expected.items():
        assert given[key] == value

    given = (await client.get(get_full_api_path("concept", iri=updated["@id"]))).json()
    for key, value in expected.items():
        assert given[key] == value


@pytest.mark.postgres
async def test_update_concept_hierarchy_conflict(postgres, cn_db_engine, cn, client):
    new = cn.concept_mid
    new[RDF["top_concept_of"]] = [{"@id": cn.scheme["@id"]}]
    if f"{SKOS}broader" in new:
        del new[f"{SKOS}broader"]

    response = await client.put(get_full_api_path("concept", iri=new["@id"]), json=new)
    assert response.status_code == 422
    assert response.json() == {
        "detail": f"Concept is marked as `topConceptOf` but also has broader relationship to `{cn.concept_top['@id']}`"
    }


@pytest.mark.postgres
async def test_update_concept_concept_scheme_not_in_database(postgres, cn_db_engine, cn, client):
    updated = cn.concept_top
    if f"{SKOS}narrower" in updated:
        del updated[f"{SKOS}narrower"]

    updated[RDF["schemes"]] = [{"@id": "http://example.com/foo"}]

    response = await client.put(get_full_api_path("concept", iri=updated["@id"]), json=updated)
    assert response.status_code == 422
    assert response.json() == {
        "detail": "At least one of the specified concept schemes must be in the database: {'http://example.com/foo'}"
    }


@pytest.mark.postgres
async def test_update_concept_relationship_cross_concept_scheme(postgres, cn_db_engine, cn, client):
    new_scheme = cn.scheme
    new_scheme["@id"] = "http://example.com/foo"
    await client.post(get_full_api_path("concept_scheme", iri=new_scheme["@id"]), json=new_scheme)

    updated = cn.concept_top
    if f"{SKOS}narrower" in updated:
        del updated[f"{SKOS}narrower"]

    updated[RDF["schemes"]] = [{"@id": "http://example.com/foo"}]

    response = await client.put(get_full_api_path("concept", iri=updated["@id"]), json=updated)
    assert response.status_code == 422
    assert response.json() == {
        "detail": "Update asked to change concept schemes, but existing concept scheme {'http://data.europa.eu/xsp/cn2024/cn2024'} had hierarchical relationships."
    }


@pytest.mark.postgres
async def test_update_concept_not_found(postgres, cn_db_engine, cn, client):
    obj = cn.concept_low
    del obj[f"{SKOS}broader"]

    response = await client.put(get_full_api_path("concept", iri=obj["@id"]), json=obj)
    assert response.status_code == 404


@pytest.mark.postgres
async def test_delete_concept(postgres, cn_db_engine, cn, client):
    response = await client.get(get_full_api_path("concept", iri=cn.concept_top["@id"]))
    assert response.status_code == 200
    assert response.json()

    response = await client.delete(get_full_api_path("concept", iri=cn.concept_top["@id"]))
    assert response.status_code == 204

    response = await client.delete(get_full_api_path("concept", iri=cn.concept_top["@id"]))
    assert response.status_code == 404

    response = await client.get(get_full_api_path("concept", iri=cn.concept_top["@id"]))
    assert response.status_code == 404
