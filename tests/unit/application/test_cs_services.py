async def test_concept_scheme_get(graph_service, entities):
    mock_kos_graph = graph_service.graph
    mock_kos_graph.concept_scheme_get.return_value = entities[2]

    result = await graph_service.concept_scheme_get(entities[2].id_)
    assert result == entities[2]
    mock_kos_graph.concept_scheme_get.assert_called_with(iri=entities[2].id_)


async def test_concept_scheme_create(graph_service, entities):
    mock_kos_graph = graph_service.graph
    mock_kos_graph.concept_scheme_create.return_value = entities[2]

    result = await graph_service.concept_scheme_create(entities[2])
    assert result == entities[2]
    mock_kos_graph.concept_scheme_create.assert_called_with(concept_scheme=entities[2])
