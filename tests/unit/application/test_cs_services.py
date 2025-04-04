import pytest

from py_semantic_taxonomy.domain.entities import ConceptSchemeNotFoundError


async def test_concept_scheme_get(graph_service, entities):
    mock_kos_graph = graph_service.graph
    mock_kos_graph.concept_scheme_get.return_value = entities[2]

    result = await graph_service.concept_scheme_get(entities[2].id_)
    assert result == entities[2]
    mock_kos_graph.concept_scheme_get.assert_called_with(iri=entities[2].id_)


async def test_concept_scheme_get_all_iris(graph_service):
    mock_kos_graph = graph_service.graph
    mock_kos_graph.concept_scheme_get_all_iris.return_value = ["http://example.com/foo"]

    result = await graph_service.concept_scheme_get_all_iris()
    assert result == ["http://example.com/foo"]
    mock_kos_graph.concept_scheme_get_all_iris.assert_called_with()


async def test_concept_scheme_list(graph_service, entities):
    mock_kos_graph = graph_service.graph
    mock_kos_graph.concept_scheme_list.return_value = [entities[2], entities[4]]

    result = await graph_service.concept_scheme_list()
    assert result == [entities[2], entities[4]]
    mock_kos_graph.concept_scheme_list.assert_called_with()


async def test_concept_scheme_create(graph_service, entities):
    mock_kos_graph = graph_service.graph
    mock_kos_graph.concept_scheme_create.return_value = entities[2]

    result = await graph_service.concept_scheme_create(entities[2])
    assert result == entities[2]
    mock_kos_graph.concept_scheme_create.assert_called_with(concept_scheme=entities[2])


async def test_concept_scheme_update(graph_service, entities):
    mock_kos_graph = graph_service.graph
    mock_kos_graph.concept_scheme_update.return_value = entities[2]

    result = await graph_service.concept_scheme_update(entities[2])
    assert result == entities[2]
    mock_kos_graph.concept_scheme_update.assert_called_with(concept_scheme=entities[2])


async def test_concept_scheme_delete(graph_service, entities):
    mock_kos_graph = graph_service.graph
    mock_kos_graph.concept_scheme_delete.return_value = 1

    result = await graph_service.concept_scheme_delete(entities[2].id_)
    assert result is None
    mock_kos_graph.concept_scheme_delete.assert_called_with(iri=entities[2].id_)


async def concept_scheme_delete_not_found(graph_service, entities):
    mock_kos_graph = graph_service.graph
    mock_kos_graph.concept_scheme_delete.return_value = 0

    with pytest.raises(ConceptSchemeNotFoundError):
        await graph_service.association_delete(entities[8].id_)
