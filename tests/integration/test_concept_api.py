import pytest

from py_semantic_taxonomy.domain.entities import CONCEPT_EXCLUDED


@pytest.mark.postgres
async def test_get_concept(postgres, cn_db, cn, client):
    response = client.get(
        "/concept/", params={"iri": "http://data.europa.eu/xsp/cn2024/010011000090"}
    )
    assert response.status_code == 200
    expected = {key: value for key, value in cn.concept_top.items() if key not in CONCEPT_EXCLUDED}
    given = response.json()

    # https://fastapi.tiangolo.com/tutorial/response-model/#response-model-encoding-parameters
    # Child models don't call `model_dump`, which means that `exclude_unset` or `by_alias` is
    # ignored. See https://github.com/pydantic/pydantic/issues/8792
    for key, value in expected.items():
        assert given[key] == value


@pytest.mark.postgres
async def test_get_concept_404(postgres, cn_db, client):
    response = client.get("/concept/", params={"iri": "http://data.europa.eu/xsp/cn2024/woof"})
    assert response.status_code == 404
