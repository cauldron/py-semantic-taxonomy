import pytest

from py_semantic_taxonomy.domain.constants import SKOS, get_full_api_path


@pytest.mark.postgres
async def test_get_concept_scheme(postgres, cn_db_engine, cn, client):
    response = await client.get(get_full_api_path("concept_scheme"), params={"iri": cn.scheme["@id"]})
    assert response.status_code == 200
    given = response.json()
    for key, value in cn.scheme.items():
        assert given[key] == value


@pytest.mark.postgres
async def test_get_concept_scheme_404(postgres, cn_db_engine, client):
    response = await client.get(
        get_full_api_path("concept_scheme"), params={"iri": "http://data.europa.eu/xsp/cn2024/woof"}
    )
    assert response.status_code == 404


@pytest.mark.postgres
async def test_create_concept_scheme(postgres, cn_db_engine, cn, client):
    new = cn.scheme
    new["@id"] = "http://data.europa.eu/xsp/cn2024/cn2025"

    response = await client.post(get_full_api_path("concept_scheme"), json=new)
    assert response.status_code == 200
    given = response.json()
    for key, value in new.items():
        assert given[key] == value

    given = (await client.get(get_full_api_path("concept_scheme"), params={"iri": new["@id"]})).json()
    for key, value in new.items():
        assert given[key] == value


@pytest.mark.postgres
async def test_create_concept_scheme_duplicate(postgres, cn_db_engine, cn, client):
    response = await client.post(get_full_api_path("concept_scheme"), json=cn.scheme)
    assert response.status_code == 409


@pytest.mark.postgres
async def test_update_concept_scheme(postgres, cn_db_engine, cn, client):
    updated = cn.scheme
    updated[f"{SKOS}prefLabel"] = [{"@value": "Combine all them nommies", "@language": "en"}]

    response = await client.put(get_full_api_path("concept_scheme"), json=updated)
    assert response.status_code == 200
    given = response.json()
    for key, value in updated.items():
        assert given[key] == value

    given = (await client.get(get_full_api_path("concept_scheme"), params={"iri": updated["@id"]})).json()
    for key, value in updated.items():
        assert given[key] == value


@pytest.mark.postgres
async def test_update_concept_scheme_not_found(postgres, cn_db_engine, cn, client):
    obj = cn.scheme
    obj["@id"] = "http://data.europa.eu/xsp/cn2024/cn2025"

    response = await client.put(get_full_api_path("concept_scheme"), json=obj)
    assert response.status_code == 404


@pytest.mark.postgres
async def test_delete_concept_scheme(postgres, cn_db_engine, cn, client):
    response = await client.get(get_full_api_path("concept_scheme"), params={"iri": cn.scheme["@id"]})
    assert response.status_code == 200
    assert response.json()

    response = await client.delete(get_full_api_path("concept_scheme"), params={"iri": cn.scheme["@id"]})
    assert response.status_code == 204

    response = await client.delete(get_full_api_path("concept_scheme"), params={"iri": cn.scheme["@id"]})
    assert response.status_code == 404

    response = await client.get(get_full_api_path("concept_scheme"), params={"iri": cn.scheme["@id"]})
    assert response.status_code == 404
