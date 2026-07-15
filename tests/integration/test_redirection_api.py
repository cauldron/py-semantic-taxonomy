import pytest

from py_semantic_taxonomy.domain.constants import SKOS
from py_semantic_taxonomy.domain.url_utils import get_full_api_path

HTML = {"accept": "text/html"}


@pytest.mark.postgres
async def test_resolve_iri_not_found(postgres, cn_db_engine, client):
    response = await client.get("/foo", follow_redirects=False)
    assert response.status_code == 404
    assert response.json() == {"detail": "No object found with IRI `http://test.ninja/foo`"}


@pytest.mark.postgres
async def test_resolve_iri_concept_scheme_json(postgres, cn_db_engine, cn, client):
    cn.scheme["@id"] = "http://test.ninja/foo"
    await client.post(get_full_api_path("concept_scheme"), json=cn.scheme)

    response = await client.get("/foo", follow_redirects=False)
    assert response.status_code == 200
    for key, value in cn.scheme.items():
        assert response.json()[key] == value


@pytest.mark.postgres
async def test_resolve_iri_concept_scheme_html_redirects_to_web_ui(
    postgres, cn_db_engine, cn, client
):
    cn.scheme["@id"] = "http://test.ninja/foo"
    await client.post(get_full_api_path("concept_scheme"), json=cn.scheme)

    response = await client.get("/foo", headers=HTML, follow_redirects=False)
    assert response.status_code == 307
    assert "/web/concept_scheme/" in response.headers["location"]


@pytest.mark.postgres
async def test_resolve_iri_concept_json(postgres, cn_db_engine, cn, client):
    del cn.concept_low[f"{SKOS}broader"]
    cn.concept_low["@id"] = "http://test.ninja/foo"
    await client.post(get_full_api_path("concept"), json=cn.concept_low)

    response = await client.get("/foo", follow_redirects=False)
    assert response.status_code == 200
    for key, value in cn.concept_low.items():
        assert response.json()[key] == value


@pytest.mark.postgres
async def test_resolve_iri_concept_html_redirects_to_web_ui(postgres, cn_db_engine, cn, client):
    del cn.concept_low[f"{SKOS}broader"]
    cn.concept_low["@id"] = "http://test.ninja/foo"
    await client.post(get_full_api_path("concept"), json=cn.concept_low)

    response = await client.get("/foo", headers=HTML, follow_redirects=False)
    assert response.status_code == 307
    assert "/web/concept/" in response.headers["location"]


@pytest.mark.postgres
async def test_resolve_iri_correspondence_json(postgres, cn_db_engine, cn, client):
    cn.correspondence["@id"] = "http://test.ninja/foo"
    await client.post(get_full_api_path("correspondence"), json=cn.correspondence)

    # Correspondences have no web UI, so even an HTML request gets JSON-LD.
    response = await client.get("/foo", headers=HTML, follow_redirects=False)
    assert response.status_code == 200
    for key, value in cn.correspondence.items():
        assert response.json()[key] == value
