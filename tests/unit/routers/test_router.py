import orjson
import pytest
from starlette.requests import Request

from pydantic import ValidationError

import py_semantic_taxonomy.adapters.routers.router as router
from py_semantic_taxonomy.domain.entities import Concept, ConceptNotFoundError


async def test_get_concept(mock_kos_graph, graph_service, entities):
    mock_kos_graph.get_concept.return_value = entities[0]

    p = await router.get_concept(iri="", service=graph_service)
    assert p != entities[0]
    assert p.id_ == entities[0].id_


async def test_get_concept_not_found(mock_kos_graph, graph_service):
    mock_kos_graph.get_concept.side_effect = ConceptNotFoundError()

    response = await router.get_concept("foo", service=graph_service)
    assert response.status_code == 404
    assert response.body == b'{"message":"Concept with iri \'foo\' not found"}'


async def test_create_concept(mock_kos_graph, graph_service, mock_request, cn):
    mock_kos_graph.create_concept.side_effect = lambda concept: concept

    request = mock_request(
        method="POST",
        path=router.Paths.concept,
        body=orjson.dumps(cn.concept_low),
    )
    response = await router.create_concept(
        request=request, concept=await request.json(), service=graph_service
    )
    assert response == Concept.from_json_ld(cn.concept_low)


async def test_create_concept_validation(graph_service, mock_request, cn):
    obj = cn.concept_low
    del obj["@id"]
    request = mock_request(
        method="POST",
        path=router.Paths.concept,
        body=orjson.dumps(obj),
    )
    with pytest.raises(ValidationError):
        await router.create_concept(
            request=request, concept=await request.json(), service=graph_service
        )


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
