import pytest

from py_semantic_taxonomy.adapters.routers.router import Paths
from py_semantic_taxonomy.domain.constants import SKOS


@pytest.mark.postgres
async def test_get_concept_scheme(postgres, cn_db_engine, cn, client):
    response = await client.get(Paths.concept_schemes, params={"iri": cn.scheme["@id"]})
    assert response.status_code == 200
    given = response.json()
    for key, value in cn.scheme.items():
        assert given[key] == value


@pytest.mark.postgres
async def test_get_concept_scheme_404(postgres, cn_db_engine, client):
    response = await client.get(
        Paths.concept_schemes, params={"iri": "http://data.europa.eu/xsp/cn2024/woof"}
    )
    assert response.status_code == 404


@pytest.mark.postgres
async def test_create_concept_scheme(postgres, cn_db_engine, cn, client):
    new = cn.scheme
    new["@id"] = "http://data.europa.eu/xsp/cn2024/cn2025"

    response = await client.post(Paths.concept_schemes, json=new)
    assert response.status_code == 200
    given = response.json()
    for key, value in new.items():
        assert given[key] == value

    given = (await client.get(Paths.concept_schemes, params={"iri": new["@id"]})).json()
    for key, value in new.items():
        assert given[key] == value


@pytest.mark.postgres
async def test_create_concept_scheme_duplicate(postgres, cn_db_engine, cn, client):
    response = await client.post(Paths.concept_schemes, json=cn.scheme)
    assert response.status_code == 409


@pytest.mark.postgres
async def test_update_concept_scheme(postgres, cn_db_engine, cn, client):
    updated = cn.scheme
    updated[f"{SKOS}prefLabel"] = [{"@value": "Combine all them nommies", "@language": "en"}]

    response = await client.put(Paths.concept_schemes, json=updated)
    assert response.status_code == 200
    given = response.json()
    for key, value in updated.items():
        assert given[key] == value

    given = (await client.get(Paths.concept_schemes, params={"iri": updated["@id"]})).json()
    for key, value in updated.items():
        assert given[key] == value


@pytest.mark.postgres
async def test_update_concept_scheme_not_found(postgres, cn_db_engine, cn, client):
    obj = cn.scheme
    obj["@id"] = "http://data.europa.eu/xsp/cn2024/cn2025"

    response = await client.put(Paths.concept_schemes, json=obj)
    assert response.status_code == 404


@pytest.mark.postgres
async def test_delete_concept_scheme(postgres, cn_db_engine, cn, client):
    response = await client.get(Paths.concept_schemes, params={"iri": cn.scheme["@id"]})
    assert response.status_code == 200
    assert response.json()

    response = await client.delete(Paths.concept_schemes, params={"iri": cn.scheme["@id"]})
    assert response.status_code == 204

    response = await client.delete(Paths.concept_schemes, params={"iri": cn.scheme["@id"]})
    assert response.status_code == 404

    response = await client.get(Paths.concept_schemes, params={"iri": cn.scheme["@id"]})
    assert response.status_code == 404
