import orjson

import py_semantic_taxonomy.adapters.routers.router as router
from py_semantic_taxonomy.adapters.routers import response_dto
from py_semantic_taxonomy.adapters.routers.request_dto import ConceptCreate
from py_semantic_taxonomy.domain.entities import Concept, ConceptNotFoundError, DuplicateIRI


async def test_get_concept(mock_kos_graph, graph_service, entities):
    mock_kos_graph.concept_get.return_value = entities[0]

    p = await router.concept_get(iri="", service=graph_service)
    assert p != entities[0]
    assert p.id_ == entities[0].id_


async def test_get_concept_not_found(mock_kos_graph, graph_service):
    mock_kos_graph.concept_get.side_effect = ConceptNotFoundError()

    response = await router.concept_get("foo", service=graph_service)
    assert response.status_code == 404
    assert orjson.loads(response.body) == {
        "message": "Concept with IRI 'foo' not found",
        "detail": {"iri": "foo"},
    }


async def test_concept_create(mock_kos_graph, graph_service, mock_request, cn):
    mock_kos_graph.concept_create.side_effect = lambda concept: concept

    request = mock_request(
        method="POST",
        path=router.Paths.concept,
        body=orjson.dumps(cn.concept_low),
    )
    response = await router.concept_create(
        request=request, concept=ConceptCreate(**cn.concept_low), service=graph_service
    )
    assert response == response_dto.Concept(**Concept.from_json_ld(cn.concept_low).to_json_ld())


async def test_concept_create_duplicate_iri(mock_kos_graph, graph_service, mock_request, cn):
    mock_kos_graph.concept_create.side_effect = DuplicateIRI()

    request = mock_request(
        method="POST",
        path=router.Paths.concept,
        body=orjson.dumps(cn.concept_top),
    )
    response = await router.concept_create(
        request=request, concept=ConceptCreate(**cn.concept_top), service=graph_service
    )
    assert response.status_code == 409
    assert orjson.loads(response.body) == {
        "message": "Resource with `@id` already exists",
        "detail": {"@id": "http://data.europa.eu/xsp/cn2024/010011000090"},
    }
