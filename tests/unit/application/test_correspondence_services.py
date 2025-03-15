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


# async def test_correspondence_create_missing_correspondence_scheme(graph_service, cn, entities, relationships):
#     mock_kos_graph = graph_service.graph
#     mock_kos_graph.correspondence_scheme_get_all_iris.return_value = ["http://example.com/foo"]

#     with pytest.raises(correspondenceSchemesNotInDatabase) as excinfo:
#         await graph_service.correspondence_create(entities[0])

#     id_ = cn.scheme["@id"]
#     assert excinfo.match(
#         f"At least one of the specified correspondence schemes must be in the database: {{'{id_}'}}"
#     )


# async def test_correspondence_create_error(graph_service, cn, entities, relationships):
#     mock_kos_graph = graph_service.graph
#     mock_kos_graph.correspondence_create.return_value = entities[0]
#     mock_kos_graph.correspondence_scheme_get_all_iris.return_value = [cn.scheme["@id"]]

#     graph_service.relationships_create = AsyncMock(side_effect=DuplicateRelationship())
#     graph_service.correspondence_delete = AsyncMock()

#     try:
#         await graph_service.correspondence_create(correspondence=entities[0], relationships=relationships)
#     except DuplicateRelationship:
#         pass

#     mock_kos_graph.correspondence_create.assert_called_with(correspondence=entities[0])
#     graph_service.relationships_create.assert_called_with(relationships)
#     graph_service.correspondence_delete.assert_called_with(entities[0].id_)


# async def test_correspondence_update(graph_service, cn, entities):
#     mock_kos_graph = graph_service.graph
#     mock_kos_graph.correspondence_update.return_value = entities[0]
#     mock_kos_graph.correspondence_scheme_get_all_iris.return_value = [cn.scheme["@id"]]

#     result = await graph_service.correspondence_update(entities[0])
#     assert result == entities[0]
#     mock_kos_graph.correspondence_update.assert_called_with(correspondence=entities[0])


# async def test_correspondence_update_missing_correspondence_scheme(graph_service, cn, entities, relationships):
#     mock_kos_graph = graph_service.graph
#     mock_kos_graph.correspondence_scheme_get_all_iris.return_value = ["http://example.com/foo"]

#     with pytest.raises(correspondenceSchemesNotInDatabase) as excinfo:
#         await graph_service.correspondence_update(entities[0])

#     id_ = cn.scheme["@id"]
#     assert excinfo.match(
#         f"At least one of the specified correspondence schemes must be in the database: {{'{id_}'}}"
#     )


# async def test_correspondence_update_cross_scheme_relationship(graph_service, cn, entities):
#     original = entities[0]
#     original.schemes = [{"@id": "http://example.com/a"}]
#     updated = entities[1]
#     updated.schemes = [{"@id": "http://example.com/b"}]

#     mock_kos_graph = graph_service.graph
#     mock_kos_graph.correspondence_get.return_value = original
#     mock_kos_graph.correspondence_scheme_get_all_iris.return_value = [
#         "http://example.com/a",
#         "http://example.com/b",
#     ]
#     mock_kos_graph.known_correspondence_schemes_for_correspondence_hierarchical_relationships.return_value = [
#         "http://example.com/a"
#     ]

#     with pytest.raises(RelationshipsInCurrentcorrespondenceScheme) as excinfo:
#         await graph_service.correspondence_update(updated)

#     assert excinfo.match(
#         "Update asked to change correspondence schemes, but existing correspondence scheme {'http://example.com/a'} had hierarchical relationships."
#     )


# async def test_correspondence_update_cross_scheme_relationship_allowed(graph_service, entities):
#     original = entities[0]
#     original.schemes = [{"@id": "http://example.com/a"}]
#     updated = entities[1]
#     updated.schemes = [{"@id": "http://example.com/b"}]

#     mock_kos_graph = graph_service.graph
#     mock_kos_graph.correspondence_get.return_value = original
#     mock_kos_graph.correspondence_scheme_get_all_iris.return_value = [
#         "http://example.com/a",
#         "http://example.com/b",
#     ]
#     mock_kos_graph.known_correspondence_schemes_for_correspondence_hierarchical_relationships.return_value = []

#     assert await graph_service.correspondence_update(updated)


# async def test_correspondence_update_cross_scheme_relationship_not_called(graph_service, cn, entities):
#     original = entities[0]
#     original.schemes = [{"@id": "http://example.com/a"}]

#     mock_kos_graph = graph_service.graph
#     mock_kos_graph.correspondence_get.return_value = original
#     mock_kos_graph.correspondence_scheme_get_all_iris.return_value = [
#         cn.scheme["@id"],
#         "http://example.com/a",
#     ]
#     assert await graph_service.correspondence_update(original)
#     mock_kos_graph.known_correspondence_schemes_for_correspondence_hierarchical_relationships.assert_not_called()


# async def test_correspondence_delete(graph_service, entities):
#     mock_kos_graph = graph_service.graph
#     mock_kos_graph.correspondence_delete.return_value = 1

#     result = await graph_service.correspondence_delete(entities[0].id_)
#     assert result == 1
#     mock_kos_graph.correspondence_delete.assert_called_with(iri=entities[0].id_)
