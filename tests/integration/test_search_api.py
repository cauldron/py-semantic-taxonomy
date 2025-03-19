import pytest

from py_semantic_taxonomy.adapters.routers.router import Paths

CONCEPT = {
    "@id": "http://data.europa.eu/xsp/cn2024/370400000080",
    "@type": ["http://www.w3.org/2004/02/skos/core#Concept"],
    "http://purl.org/ontology/bibo/status": [
        {"@id": "http://purl.org/ontology/bibo/status/accepted"}
    ],
    "http://www.w3.org/2004/02/skos/core#inScheme": [
        {"@id": "http://data.europa.eu/xsp/cn2024/cn2024"}
    ],
    "http://www.w3.org/2004/02/skos/core#prefLabel": [
        {
            "@language": "en",
            "@value": "Photographic plates, film, paper, paperboard and textiles, exposed but not developed",
        },
    ],
}


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


@pytest.mark.typesense
async def test_typesense_concepts_create_delete(postgres, typesense, client, cn_db_engine, cn):
    response = await client.get(Paths.search, params={"query": "kodak", "language": "en"})
    assert response.status_code == 200
    assert response.json()[0]["id_"] != CONCEPT["@id"]

    response = await client.post(Paths.concept, json=CONCEPT)
    assert response.status_code == 200

    response = await client.get(Paths.search, params={"query": "kodak", "language": "en"})
    assert response.status_code == 200
    assert response.json()[0]["id_"] == CONCEPT["@id"]

    CONCEPT["http://www.w3.org/2004/02/skos/core#prefLabel"] = [
        {
            "@language": "en",
            "@value": "Salami Sausage",
        }
    ]
    response = await client.put(Paths.concept, json=CONCEPT)
    assert response.status_code == 200

    response = await client.get(Paths.search, params={"query": "kodak", "language": "en"})
    assert response.status_code == 200
    assert (
        response.json()[0]["label"]
        != "Photographic plates, film, paper, paperboard and textiles, exposed but not developed"
    )

    CONCEPT["http://www.w3.org/2004/02/skos/core#prefLabel"] = [
        {
            "@language": "en",
            "@value": "Photographic plates, film, paper, paperboard and textiles, exposed but not developed",
        }
    ]
    response = await client.put(Paths.concept, json=CONCEPT)
    assert response.status_code == 200

    response = await client.get(Paths.search, params={"query": "kodak", "language": "en"})
    assert response.status_code == 200
    assert response.json()[0]["id_"] == CONCEPT["@id"]

    response = await client.delete(Paths.concept, params={"iri": CONCEPT["@id"]})
    assert response.status_code == 204

    response = await client.get(Paths.search, params={"query": "kodak", "language": "en"})
    assert response.status_code == 200
    assert response.json()[0]["id_"] != CONCEPT["@id"]
