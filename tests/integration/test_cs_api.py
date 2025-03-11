import pytest

from py_semantic_taxonomy.adapters.routers.router import Paths
from py_semantic_taxonomy.domain.constants import SKOS


@pytest.mark.postgres
async def test_get_concept(postgres, cn_db_engine, cn, client):
    response = await client.get(Paths.concept_scheme, params={"iri": cn.scheme["@id"]})
    assert response.status_code == 200
    given = response.json()
    for key, value in cn.scheme.items():
        assert given[key] == value


@pytest.mark.postgres
async def test_get_concept_404(postgres, cn_db_engine, client):
    response = await client.get(
        Paths.concept_scheme, params={"iri": "http://data.europa.eu/xsp/cn2024/woof"}
    )
    assert response.status_code == 404


@pytest.mark.postgres
async def test_create_concept(postgres, cn_db_engine, cn, client):
    new = cn.scheme
    new["@id"] = "http://data.europa.eu/xsp/cn2024/cn2025"

    response = await client.post(Paths.concept_scheme, json=new)
    assert response.status_code == 200
    given = response.json()
    for key, value in new.items():
        assert given[key] == value

    given = (await client.get(Paths.concept_scheme, params={"iri": new["@id"]})).json()
    for key, value in new.items():
        assert given[key] == value


@pytest.mark.postgres
async def test_create_concept_duplicate(postgres, cn_db_engine, cn, client):
    response = await client.post(Paths.concept_scheme, json=cn.scheme)
    assert response.status_code == 409


# @pytest.mark.postgres
# async def test_update_concept(postgres, cn_db_engine, cn, client):
#     updated = cn.concept_top
#     updated[f"{SKOS}altLabel"] = [{"@value": "Dream a little dream", "@language": "en"}]
#     del updated[f"{SKOS}narrower"]
#     del updated[f"{SKOS}topConceptOf"]

#     response = await client.put(Paths.concept_scheme, json=updated)
#     assert response.status_code == 200
#     expected = {
#         key: value for key, value in updated.items() if key not in SKOS_RELATIONSHIP_PREDICATES
#     }
#     given = response.json()

#     # https://fastapi.tiangolo.com/tutorial/response-model/#response-model-encoding-parameters
#     # Child models don't call `model_dump`, which means that `exclude_unset` or `by_alias` is
#     # ignored. See https://github.com/pydantic/pydantic/issues/8792
#     for key, value in expected.items():
#         assert given[key] == value

#     given = (await client.get(Paths.concept_scheme, params={"iri": updated["@id"]})).json()
#     for key, value in expected.items():
#         assert given[key] == value


# @pytest.mark.postgres
# async def test_update_concept_not_found(postgres, cn_db_engine, cn, client):
#     obj = cn.concept_low
#     del obj[f"{SKOS}broader"]

#     response = await client.put(Paths.concept_scheme, json=obj)
#     assert response.status_code == 404


# @pytest.mark.postgres
# async def test_delete_concept(postgres, cn_db_engine, cn, client):
#     response = await client.get(Paths.concept_scheme, params={"iri": cn.concept_top["@id"]})
#     assert response.status_code == 200
#     assert response.json()

#     response = await client.delete(Paths.concept_scheme, params={"iri": cn.concept_top["@id"]})
#     assert response.status_code == 200
#     assert response.json()["count"] == 1

#     response = await client.delete(Paths.concept_scheme, params={"iri": cn.concept_top["@id"]})
#     assert response.status_code == 200
#     assert response.json()["count"] == 0

#     response = await client.get(Paths.concept_scheme, params={"iri": cn.concept_top["@id"]})
#     assert response.status_code == 404
