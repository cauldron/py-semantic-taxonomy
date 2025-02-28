import pytest
from fastapi import HTTPException
from starlette.requests import Request

import py_semantic_taxonomy.adapters.routers.router as router
from py_semantic_taxonomy.domain.entities import Concept, ConceptNotFoundError


async def test_get_concept(mock_kos_graph, graph_service, entities):
    mock_kos_graph.get_concept.return_value = entities[0]

    p = await router.get_concept(iri="", service=graph_service)
    assert p != entities[0]
    assert p.id_ == entities[0].id_


async def test_get_concept_not_found(mock_kos_graph, graph_service):
    mock_kos_graph.get_concept.side_effect = ConceptNotFoundError()

    with pytest.raises(HTTPException) as exc_info:
        await router.get_concept("foo", service=graph_service)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Concept with iri 'foo' not found"


@pytest.mark.skip(reason="Needs to be integration test because of URL reverse needs FastAPI app")
async def test_concept_redirect(mock_kos_graph, graph_service, entities):
    mock_kos_graph.get_object_type.return_value = Concept

    response = await router.generic_get_from_iri(
        request=Request(
            scope={
                "type": "http",
                "path": "/concept/foo",
                "method": "GET",
                "scheme": "https",
                "client": ("127.0.0.1", 8080),
                "server": ("www.example.com", 443),
                "headers": {},
            }
        ),
        _="",
        service=graph_service,
    )
    assert response.status_code == 307
    assert response.url == "https://www.example.com/concept/foo"
