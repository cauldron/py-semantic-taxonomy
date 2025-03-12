from py_semantic_taxonomy.domain.entities import Concept, ConceptScheme


async def test_object_type_get_concept(graph_service, entities):
    mock_kos_graph = graph_service.graph
    mock_kos_graph.get_object_type.return_value = Concept

    result = await graph_service.get_object_type(entities[0].id_)
    assert result == Concept
    mock_kos_graph.get_object_type.assert_called_with(iri=entities[0].id_)


async def test_object_type_get_concept_scheme(graph_service, entities):
    mock_kos_graph = graph_service.graph
    mock_kos_graph.get_object_type.return_value = ConceptScheme

    result = await graph_service.get_object_type(entities[2].id_)
    assert result == ConceptScheme
    mock_kos_graph.get_object_type.assert_called_with(iri=entities[2].id_)
