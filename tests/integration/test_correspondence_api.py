import orjson
import pytest

from py_semantic_taxonomy.adapters.routers.router import Paths
from py_semantic_taxonomy.domain.constants import RDF_MAPPING as RDF
from py_semantic_taxonomy.domain.constants import SKOS
from py_semantic_taxonomy.domain.entities import MadeOf


@pytest.mark.postgres
async def test_get_correspondence(postgres, cn_db_engine, cn, client):
    response = await client.get(Paths.correspondence, params={"iri": cn.correspondence["@id"]})
    assert response.status_code == 200
    given = response.json()

    for key, value in cn.correspondence.items():
        assert given[key] == value


@pytest.mark.postgres
async def test_get_correspondence_404(postgres, cn_db_engine, client):
    response = await client.get(
        Paths.correspondence, params={"iri": "http://pyst-tests.ninja/correspondence/missing"}
    )
    assert response.status_code == 404


@pytest.mark.postgres
async def test_create_correspondence(postgres, cn_db_engine, cn, client):
    new = cn.correspondence
    new["@id"] = "http://pyst-tests.ninja/correspondence/new"

    response = await client.post(Paths.correspondence, json=new)
    assert response.status_code == 200
    given = response.json()
    for key, value in new.items():
        assert given[key] == value

    given = (await client.get(Paths.correspondence, params={"iri": new["@id"]})).json()
    for key, value in new.items():
        assert given[key] == value


@pytest.mark.postgres
async def test_create_correspondence_duplicate(postgres, cn_db_engine, cn, client):
    response = await client.post(Paths.correspondence, json=cn.correspondence)
    assert response.status_code == 409


@pytest.mark.postgres
async def test_update_correspondence(postgres, cn_db_engine, cn, client):
    updated = cn.correspondence
    updated[f"{SKOS}prefLabel"] = [{"@value": "Don't read my correspondence", "@language": "en"}]

    response = await client.put(Paths.correspondence, json=updated)
    assert response.status_code == 200
    given = response.json()
    for key, value in updated.items():
        assert given[key] == value

    given = (await client.get(Paths.correspondence, params={"iri": updated["@id"]})).json()
    for key, value in updated.items():
        assert given[key] == value


@pytest.mark.postgres
async def test_update_correspondence_not_found(postgres, cn_db_engine, cn, client):
    obj = cn.correspondence
    obj["@id"] = "http://pyst-tests.ninja/correspondence/missing"

    response = await client.put(Paths.correspondence, json=obj)
    assert response.status_code == 404


@pytest.mark.postgres
async def test_delete_correspondence(postgres, cn_db_engine, cn, client):
    response = await client.get(Paths.correspondence, params={"iri": cn.correspondence["@id"]})
    assert response.status_code == 200
    assert response.json()

    response = await client.delete(Paths.correspondence, params={"iri": cn.correspondence["@id"]})
    assert response.status_code == 204

    response = await client.delete(Paths.correspondence, params={"iri": cn.correspondence["@id"]})
    assert response.status_code == 404

    response = await client.get(Paths.correspondence, params={"iri": cn.correspondence["@id"]})
    assert response.status_code == 404


@pytest.mark.postgres
async def test_made_of_add(postgres, cn_db_engine, cn, made_of, client):
    cn.correspondence[RDF["made_ofs"]] = sorted(made_of.made_ofs, key=lambda x: x["@id"])

    response = await client.post(Paths.made_of, json=made_of.to_json_ld())
    assert response.status_code == 200
    given = response.json()
    given[RDF["made_ofs"]].sort(key=lambda x: x["@id"])
    for key, value in cn.correspondence.items():
        assert given[key] == value

    given = (
        await client.get(Paths.correspondence, params={"iri": cn.correspondence["@id"]})
    ).json()
    for key, value in cn.correspondence.items():
        assert given[key] == value


@pytest.mark.postgres
async def test_made_of_add_missing(postgres, cn_db_engine, cn, made_of, client):
    made_of.id_ = "http://pyst-tests.ninja/correspondence/missing"

    response = await client.post(Paths.made_of, json=made_of.to_json_ld())
    assert response.status_code == 404


@pytest.mark.postgres
async def test_made_of_remove(postgres, cn_db_engine, cn, made_of, client):
    response = await client.post(Paths.made_of, json=made_of.to_json_ld())
    assert response.status_code == 200

    made_of.made_ofs = [
        {"@id": "http://data.europa.eu/xsp/cn2023/top_level_association"},
    ]
    response = await client.request(
        method="DELETE",
        url=Paths.made_of,
        content=orjson.dumps(made_of.to_json_ld()),
    )
    given = response.json()
    assert given[RDF["made_ofs"]] == [{"@id": "http://data.europa.eu/xsp/cn2023/lower_association"}]

    given = (
        await client.get(Paths.correspondence, params={"iri": cn.correspondence["@id"]})
    ).json()
    assert given[RDF["made_ofs"]] == [{"@id": "http://data.europa.eu/xsp/cn2023/lower_association"}]


@pytest.mark.postgres
async def test_made_of_remove_missing(postgres, cn_db_engine, cn, made_of, client):
    made_of.id_ = "http://pyst-tests.ninja/correspondence/missing"

    response = await client.request(
        method="DELETE",
        url=Paths.made_of,
        content=orjson.dumps(made_of.to_json_ld()),
    )
    assert response.status_code == 404
