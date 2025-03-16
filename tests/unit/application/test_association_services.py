import pytest

from py_semantic_taxonomy.domain.entities import AssociationNotFoundError


async def test_association_get(graph_service, entities):
    mock_kos_graph = graph_service.graph
    mock_kos_graph.association_get.return_value = entities[8]

    result = await graph_service.association_get(entities[8].id_)
    assert result == entities[8]
    mock_kos_graph.association_get.assert_called_with(iri=entities[8].id_)


async def test_association_create(graph_service, cn, entities, relationships):
    mock_kos_graph = graph_service.graph
    mock_kos_graph.association_create.return_value = entities[8]

    result = await graph_service.association_create(entities[8])
    assert result == entities[8]
    mock_kos_graph.association_create.assert_called_with(association=entities[8])


async def test_association_delete(graph_service, entities):
    mock_kos_graph = graph_service.graph
    mock_kos_graph.association_delete.return_value = 1

    result = await graph_service.association_delete(iri=entities[8].id_)
    assert result is None
    mock_kos_graph.association_delete.assert_called_with(iri=entities[8].id_)


async def test_association_delete_not_found(graph_service, entities):
    mock_kos_graph = graph_service.graph
    mock_kos_graph.association_delete.return_value = 0

    with pytest.raises(AssociationNotFoundError):
        await graph_service.association_delete(entities[8].id_)
