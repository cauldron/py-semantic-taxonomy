from unittest.mock import AsyncMock

from py_semantic_taxonomy.domain.entities import DuplicateRelationship


async def test_concept_get(graph_service, entities):
    mock_kos_graph = graph_service.graph
    mock_kos_graph.concept_get.return_value = entities[0]

    result = await graph_service.concept_get(entities[0].id_)
    assert result == entities[0]
    mock_kos_graph.concept_get.assert_called_with(iri=entities[0].id_)


async def test_concept_create(graph_service, entities, relationships):
    mock_kos_graph = graph_service.graph
    mock_kos_graph.concept_create.return_value = entities[0]

    result = await graph_service.concept_create(entities[0])
    assert result == entities[0]
    mock_kos_graph.concept_create.assert_called_with(concept=entities[0])

    result = await graph_service.concept_create(entities[0], relationships)
    assert result == entities[0]
    mock_kos_graph.concept_create.assert_called_with(concept=entities[0])


async def test_concept_create_error(graph_service, entities, relationships):
    mock_kos_graph = graph_service.graph
    mock_kos_graph.concept_create.return_value = entities[0]

    graph_service.relationships_create = AsyncMock(side_effect=DuplicateRelationship())
    graph_service.concept_delete = AsyncMock()

    try:
        await graph_service.concept_create(concept=entities[0], relationships=relationships)
    except DuplicateRelationship:
        pass

    mock_kos_graph.concept_create.assert_called_with(concept=entities[0])
    graph_service.relationships_create.assert_called_with(relationships)
    graph_service.concept_delete.assert_called_with(entities[0].id_)


async def test_concept_update(graph_service, entities):
    mock_kos_graph = graph_service.graph
    mock_kos_graph.concept_update.return_value = entities[0]

    result = await graph_service.concept_update(entities[0])
    assert result == entities[0]
    mock_kos_graph.concept_update.assert_called_with(concept=entities[0])


async def test_concept_delete(graph_service, entities):
    mock_kos_graph = graph_service.graph
    mock_kos_graph.concept_delete.return_value = 1

    result = await graph_service.concept_delete(entities[0].id_)
    assert result == 1
    mock_kos_graph.concept_delete.assert_called_with(iri=entities[0].id_)
