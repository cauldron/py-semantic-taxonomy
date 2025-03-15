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
    assert result == 1
    mock_kos_graph.correspondence_delete.assert_called_with(iri=entities[3].id_)
