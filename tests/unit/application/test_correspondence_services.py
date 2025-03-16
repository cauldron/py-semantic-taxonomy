import pytest

from py_semantic_taxonomy.domain.entities import CorrespondenceNotFoundError


async def test_correspondence_get(graph_service, entities):
    mock_kos_graph = graph_service.graph
    mock_kos_graph.correspondence_get.return_value = entities[3]

    result = await graph_service.correspondence_get(entities[3].id_)
    assert result == entities[3]
    mock_kos_graph.correspondence_get.assert_called_with(iri=entities[3].id_)


async def test_correspondence_create(graph_service, cn, entities, relationships):
    mock_kos_graph = graph_service.graph
    mock_kos_graph.correspondence_create.return_value = entities[3]

    result = await graph_service.correspondence_create(entities[3])
    assert result == entities[3]
    mock_kos_graph.correspondence_create.assert_called_with(correspondence=entities[3])


async def test_correspondence_update(graph_service, cn, entities):
    mock_kos_graph = graph_service.graph
    mock_kos_graph.correspondence_update.return_value = entities[3]

    result = await graph_service.correspondence_update(entities[3])
    assert result == entities[3]
    mock_kos_graph.correspondence_update.assert_called_with(correspondence=entities[3])


async def test_correspondence_delete(graph_service, entities):
    mock_kos_graph = graph_service.graph
    mock_kos_graph.correspondence_delete.return_value = 1

    result = await graph_service.correspondence_delete(entities[3].id_)
    assert result is None
    mock_kos_graph.correspondence_delete.assert_called_with(iri=entities[3].id_)


async def correspondence_delete_not_found(graph_service, entities):
    mock_kos_graph = graph_service.graph
    mock_kos_graph.association_delete.return_value = 0

    with pytest.raises(CorrespondenceNotFoundError):
        await graph_service.association_delete(entities[8].id_)


async def test_made_of_add(graph_service, cn, made_of, entities):
    mock_kos_graph = graph_service.graph
    mock_kos_graph.made_of_add.return_value = entities[3]

    result = await graph_service.made_of_add(made_of)
    assert result == entities[3]
    mock_kos_graph.made_of_add.assert_called_with(made_of)


async def test_made_of_remove(graph_service, cn, made_of, entities):
    mock_kos_graph = graph_service.graph
    mock_kos_graph.made_of_remove.return_value = entities[3]

    result = await graph_service.made_of_remove(made_of)
    assert result == entities[3]
    mock_kos_graph.made_of_remove.assert_called_with(made_of)
