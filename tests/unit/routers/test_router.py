import pytest
from starlette.requests import Request

import py_semantic_taxonomy.adapters.routers.router as router
from py_semantic_taxonomy.domain.entities import Concept


@pytest.mark.skip(
    reason="Can only be covered in integration test because `url_for` needs FastAPI app"
)
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
