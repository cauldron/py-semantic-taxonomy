async def test_relationships_get(graph_service, relationships):
    mock_kos_graph = graph_service.graph
    mock_kos_graph.relationships_get.return_value = relationships

    result = await graph_service.relationships_get(iri=relationships[0].source)
    assert result == relationships
    mock_kos_graph.relationships_get.assert_called_with(
        iri=relationships[0].source, source=True, target=False
    )

    result = await graph_service.relationships_get(
        iri=relationships[0].source, source=False, target=True
    )
    assert result == relationships
    mock_kos_graph.relationships_get.assert_called_with(
        iri=relationships[0].source, source=False, target=True
    )


# async def test_relationship_create(graph_service, entities):
#     mock_kos_graph = graph_service.graph
#     mock_kos_graph.relationship_create.return_value = entities[2]

#     result = await graph_service.relationship_create(entities[2])
#     assert result == entities[2]
#     mock_kos_graph.relationship_create.assert_called_with(relationship=entities[2])


# async def test_relationship_update(graph_service, entities):
#     mock_kos_graph = graph_service.graph
#     mock_kos_graph.relationship_update.return_value = entities[2]

#     result = await graph_service.relationship_update(entities[2])
#     assert result == entities[2]
#     mock_kos_graph.relationship_update.assert_called_with(relationship=entities[2])


# async def test_relationship_delete(graph_service, entities):
#     mock_kos_graph = graph_service.graph
#     mock_kos_graph.relationship_delete.return_value = 1

#     result = await graph_service.relationship_delete(entities[2].id_)
#     assert result == 1
#     mock_kos_graph.concept_scheme_delete.assert_called_with(iri=entities[2].id_)
