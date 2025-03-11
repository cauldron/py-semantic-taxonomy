from unittest.mock import AsyncMock

import orjson

from py_semantic_taxonomy.adapters.routers.router import GraphService, Paths
from py_semantic_taxonomy.domain.constants import SKOS
from py_semantic_taxonomy.domain.entities import (
    ConceptScheme,
    ConceptSchemeNotFoundError,
    DuplicateIRI,
)


async def test_concept_scheme_get(cn, client, monkeypatch):
    monkeypatch.setattr(
        GraphService,
        "concept_scheme_get",
        AsyncMock(return_value=ConceptScheme.from_json_ld(cn.scheme)),
    )

    response = await client.get(Paths.concept_scheme, params={"iri": cn.scheme["@id"]})
    assert response.status_code == 200
    cs = orjson.loads(response.content)
    for key, value in cs.items():
        if value:
            assert cn.scheme[key] == value


async def test_concept_get_not_found(cn, client, monkeypatch):
    monkeypatch.setattr(
        GraphService, "concept_scheme_get", AsyncMock(side_effect=ConceptSchemeNotFoundError())
    )

    response = await client.get(Paths.concept_scheme, params={"iri": "foo"})
    concept = orjson.loads(response.content)
    assert response.status_code == 404
    assert concept == {
        "message": "Concept Scheme with IRI 'foo' not found",
        "detail": {"iri": "foo"},
    }

# async def test_concept_delete(cn, client, monkeypatch):
#     monkeypatch.setattr(GraphService, "concept_delete", AsyncMock(return_value=1))

#     response = await client.delete(Paths.concept_scheme, params={"iri": cn.concept_top["@id"]})
#     assert response.status_code == 200
