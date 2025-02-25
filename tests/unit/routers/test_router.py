import pytest

from fastapi import HTTPException

from py_semantic_taxonomy.adapters.routers.router import router
from py_semantic_taxonomy.domain.entities import ConceptNotFoundError


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
