import pytest

from py_semantic_taxonomy.domain.constants import SKOS
from py_semantic_taxonomy.domain.url_utils import get_full_api_path


@pytest.mark.skip(reason="Generic redirection turned off for now")
@pytest.mark.postgres
async def test_generic_get_from_iri_concept(postgres, cn_db_engine, cn, client):
    response = await client.get("/foo", follow_redirects=False)
    assert response.status_code == 404
    assert response.json() == {
        "detail": "KOS graph object with IRI `http://test.ninja/foo` not found"
    }

    del cn.concept_low[f"{SKOS}broader"]
    cn.concept_low["@id"] = "http://test.ninja/foo"
    await client.post(get_full_api_path("concept"), json=cn.concept_low)

    response = await client.get("/foo", follow_redirects=False)
    api_path = get_full_api_path("concept")
    assert response.status_code == 307
    assert (
        response.headers["location"]
        == f"http://test.ninja{api_path}?iri=http%3A%2F%2Ftest.ninja%2Ffoo"
    )

    concept = (await client.get(response.headers["location"])).json()
    for key, value in cn.concept_low.items():
        assert concept[key] == value


@pytest.mark.skip(reason="Generic redirection turned off for now")
@pytest.mark.postgres
async def test_generic_get_from_iri_concept_scheme(postgres, cn_db_engine, cn, client):
    response = await client.get("/foo", follow_redirects=False)
    assert response.status_code == 404
    assert response.json() == {
        "detail": "KOS graph object with IRI `http://test.ninja/foo` not found"
    }

    cn.scheme["@id"] = "http://test.ninja/foo"
    await client.post(get_full_api_path("concept_scheme"), json=cn.scheme)

    response = await client.get("/foo", follow_redirects=False)
    api_path = get_full_api_path("concept_scheme")
    assert response.status_code == 307
    assert (
        response.headers["location"]
        == f"http://test.ninja{api_path}?iri=http%3A%2F%2Ftest.ninja%2Ffoo"
    )

    cs = (await client.get(response.headers["location"])).json()
    for key, value in cn.scheme.items():
        assert cs[key] == value


@pytest.mark.skip(reason="Generic redirection turned off for now")
@pytest.mark.postgres
async def test_generic_get_from_iri_correspondence(postgres, cn_db_engine, cn, client):
    response = await client.get("/foo", follow_redirects=False)
    assert response.status_code == 404
    assert response.json() == {
        "detail": "KOS graph object with IRI `http://test.ninja/foo` not found"
    }

    cn.correspondence["@id"] = "http://test.ninja/foo"
    await client.post(get_full_api_path("correspondence"), json=cn.correspondence)

    response = await client.get("/foo", follow_redirects=False)
    api_path = get_full_api_path("correspondence")
    assert response.status_code == 307
    assert (
        response.headers["location"]
        == f"http://test.ninja{api_path}?iri=http%3A%2F%2Ftest.ninja%2Ffoo"
    )

    cs = (await client.get(response.headers["location"])).json()
    for key, value in cn.correspondence.items():
        assert cs[key] == value
