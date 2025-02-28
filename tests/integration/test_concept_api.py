def test_get_concept(postgres, cn_db, cn, client):
    response = client.get(
        "/concept/", params={"iri": "http://data.europa.eu/xsp/cn2024/010011000090"}
    )
    assert response.status_code == 200
    expected, given = cn[0], response.json()

    # https://fastapi.tiangolo.com/tutorial/response-model/#response-model-encoding-parameters
    # TBD: They should be identical, but FastAPI is including unset default fields even though we
    # have `exclude_unset=True` in our response DTO `model_dump`. Putting in a loggging message
    # makes it seem like `model_dump` isn't being called at all?
    for key, value in expected.items():
        assert given[key] == value


def test_get_concept_404(postgres, cn_db, cn, client):
    response = client.get("/concept/", params={"iri": "http://data.europa.eu/xsp/cn2024/woof"})
    assert response.status_code == 404
