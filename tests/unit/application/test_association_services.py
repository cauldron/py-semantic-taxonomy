from unittest.mock import AsyncMock

import pytest


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


# async def test_association_update(graph_service, cn, entities):
#     mock_kos_graph = graph_service.graph
#     mock_kos_graph.association_update.return_value = entities[0]
#     mock_kos_graph.association_scheme_get_all_iris.return_value = [cn.scheme["@id"]]

#     result = await graph_service.association_update(entities[0])
#     assert result == entities[0]
#     mock_kos_graph.association_update.assert_called_with(association=entities[0])


# async def test_association_update_missing_association_scheme(graph_service, cn, entities, relationships):
#     mock_kos_graph = graph_service.graph
#     mock_kos_graph.association_scheme_get_all_iris.return_value = ["http://example.com/foo"]

#     with pytest.raises(associationSchemesNotInDatabase) as excinfo:
#         await graph_service.association_update(entities[0])

#     id_ = cn.scheme["@id"]
#     assert excinfo.match(
#         f"At least one of the specified association schemes must be in the database: {{'{id_}'}}"
#     )


# async def test_association_update_cross_scheme_relationship(graph_service, cn, entities):
#     original = entities[0]
#     original.schemes = [{"@id": "http://example.com/a"}]
#     updated = entities[1]
#     updated.schemes = [{"@id": "http://example.com/b"}]

#     mock_kos_graph = graph_service.graph
#     mock_kos_graph.association_get.return_value = original
#     mock_kos_graph.association_scheme_get_all_iris.return_value = [
#         "http://example.com/a",
#         "http://example.com/b",
#     ]
#     mock_kos_graph.known_association_schemes_for_association_hierarchical_relationships.return_value = [
#         "http://example.com/a"
#     ]

#     with pytest.raises(RelationshipsInCurrentassociationScheme) as excinfo:
#         await graph_service.association_update(updated)

#     assert excinfo.match(
#         "Update asked to change association schemes, but existing association scheme {'http://example.com/a'} had hierarchical relationships."
#     )


# async def test_association_update_cross_scheme_relationship_allowed(graph_service, entities):
#     original = entities[0]
#     original.schemes = [{"@id": "http://example.com/a"}]
#     updated = entities[1]
#     updated.schemes = [{"@id": "http://example.com/b"}]

#     mock_kos_graph = graph_service.graph
#     mock_kos_graph.association_get.return_value = original
#     mock_kos_graph.association_scheme_get_all_iris.return_value = [
#         "http://example.com/a",
#         "http://example.com/b",
#     ]
#     mock_kos_graph.known_association_schemes_for_association_hierarchical_relationships.return_value = []

#     assert await graph_service.association_update(updated)


# async def test_association_update_cross_scheme_relationship_not_called(graph_service, cn, entities):
#     original = entities[0]
#     original.schemes = [{"@id": "http://example.com/a"}]

#     mock_kos_graph = graph_service.graph
#     mock_kos_graph.association_get.return_value = original
#     mock_kos_graph.association_scheme_get_all_iris.return_value = [
#         cn.scheme["@id"],
#         "http://example.com/a",
#     ]
#     assert await graph_service.association_update(original)
#     mock_kos_graph.known_association_schemes_for_association_hierarchical_relationships.assert_not_called()


# async def test_association_delete(graph_service, entities):
#     mock_kos_graph = graph_service.graph
#     mock_kos_graph.association_delete.return_value = 1

#     result = await graph_service.association_delete(entities[0].id_)
#     assert result == 1
#     mock_kos_graph.association_delete.assert_called_with(iri=entities[0].id_)
