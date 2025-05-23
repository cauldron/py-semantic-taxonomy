import pytest

from py_semantic_taxonomy.domain.url_utils import get_full_api_path


@pytest.mark.postgres
async def test_get_association(postgres, cn_db_engine, cn, client):
    response = await client.get(get_full_api_path("association", iri=cn.association_top["@id"]))
    assert response.status_code == 200
    given = response.json()

    for key, value in cn.association_top.items():
        assert given[key] == value


@pytest.mark.postgres
async def test_get_association_404(postgres, cn_db_engine, client):
    response = await client.get(
        get_full_api_path("association", iri="http://pyst-tests.ninja/association/missing"),
    )
    assert response.status_code == 404


@pytest.mark.postgres
async def test_get_association_all_all_filters(postgres, cn_db_engine, cn, client, made_of):
    await client.post(get_full_api_path("made_of"), json=made_of.to_json_ld())

    response = await client.get(
        get_full_api_path("association_all"),
        params={
            "correspondence_iri": cn.correspondence["@id"],
            "source_concept_iri": cn.concept_2023_top["@id"],
            "target_concept_iri": cn.concept_top["@id"],
            "kind": "simple",
        },
    )
    assert response.status_code == 200
    assert response.json() == [cn.association_top]


@pytest.mark.postgres
async def test_get_association_all_no_filters(postgres, cn_db_engine, cn, client):
    response = await client.get(get_full_api_path("association_all"))
    assert response.status_code == 200
    assert response.json() == [cn.association_low, cn.association_top]


@pytest.mark.postgres
async def test_create_association(postgres, cn_db_engine, cn, client):
    new = cn.association_top
    new["@id"] = "http://pyst-tests.ninja/association/new"

    response = await client.post(get_full_api_path("association"), json=new)
    assert response.status_code == 200
    given = response.json()
    for key, value in new.items():
        assert given[key] == value

    given = (await client.get(get_full_api_path("association", iri=new["@id"]))).json()
    for key, value in new.items():
        assert given[key] == value


@pytest.mark.postgres
async def test_create_association_duplicate(postgres, cn_db_engine, cn, client):
    response = await client.post(
        get_full_api_path("association", iri=cn.association_top["@id"]), json=cn.association_top
    )
    assert response.status_code == 409


@pytest.mark.postgres
async def test_delete_association(postgres, cn_db_engine, cn, client):
    response = await client.get(get_full_api_path("association", iri=cn.association_top["@id"]))
    assert response.status_code == 200
    assert response.json()

    response = await client.delete(get_full_api_path("association", iri=cn.association_top["@id"]))
    assert response.status_code == 204

    response = await client.delete(get_full_api_path("association", iri=cn.association_top["@id"]))
    assert response.status_code == 404

    response = await client.get(get_full_api_path("association", iri=cn.association_top["@id"]))
    assert response.status_code == 404
