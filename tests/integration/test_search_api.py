import pytest

from py_semantic_taxonomy.adapters.routers.router import Paths


@pytest.mark.typesense
async def test_typesense_searching(sqlite, typesense, anonymous_client, cn):
    result = await anonymous_client.get(Paths.search, params={"query": "Zaum", "language": "de"})
    assert result.status_code == 200
    assert result.json()[0]["id_"] == cn.concept_2023_low["@id"]

    result = await anonymous_client.get(
        Paths.search, params={"query": "Zaum", "language": "de", "semantic": "0"}
    )
    assert result.status_code == 200
    assert result.json() == []

    result = await anonymous_client.get(Paths.suggest, params={"query": "Ese", "language": "de"})
    assert result.status_code == 200
    assert result.json() == [
        {
            "id_": "http://data.europa.eu/xsp/cn2023/010100000080",
            "label": "0101 Pferde, Esel, Maultiere und Maulesel, lebend",
            "highlight": "0101 Pferde, <mark>Ese</mark>l, Maultiere und Maulesel, lebend",
        }
    ]

    result = await anonymous_client.get(Paths.search, params={"query": "Zaum", "language": "jp"})
    assert result.status_code == 422
