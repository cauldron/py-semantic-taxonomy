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
    assert result == 1
    mock_kos_graph.concept_scheme_delete.assert_called_with(iri=entities[2].id_)
