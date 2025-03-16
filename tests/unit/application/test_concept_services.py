from unittest.mock import AsyncMock

import pytest

from py_semantic_taxonomy.domain.entities import (
    ConceptNotFoundError,
    ConceptSchemesNotInDatabase,
    DuplicateRelationship,
    RelationshipsInCurrentConceptScheme,
)


async def test_concept_get(graph_service, entities):
    mock_kos_graph = graph_service.graph
    mock_kos_graph.concept_get.return_value = entities[0]

    result = await graph_service.concept_get(entities[0].id_)
    assert result == entities[0]
    mock_kos_graph.concept_get.assert_called_with(iri=entities[0].id_)


async def test_concept_create(graph_service, cn, entities, relationships):
    mock_kos_graph = graph_service.graph
    mock_kos_graph.concept_create.return_value = entities[0]
    mock_kos_graph.concept_scheme_get_all_iris.return_value = [cn.scheme["@id"]]

    result = await graph_service.concept_create(entities[0])
    assert result == entities[0]
    mock_kos_graph.concept_create.assert_called_with(concept=entities[0])

    result = await graph_service.concept_create(entities[0], relationships)
    assert result == entities[0]
    mock_kos_graph.concept_create.assert_called_with(concept=entities[0])


async def test_concept_create_missing_concept_scheme(graph_service, cn, entities, relationships):
    mock_kos_graph = graph_service.graph
    mock_kos_graph.concept_scheme_get_all_iris.return_value = ["http://example.com/foo"]

    with pytest.raises(ConceptSchemesNotInDatabase) as excinfo:
        await graph_service.concept_create(entities[0])

    id_ = cn.scheme["@id"]
    assert excinfo.match(
        f"At least one of the specified concept schemes must be in the database: {{'{id_}'}}"
    )


async def test_concept_create_error(graph_service, cn, entities, relationships):
    mock_kos_graph = graph_service.graph
    mock_kos_graph.concept_create.return_value = entities[0]
    mock_kos_graph.concept_scheme_get_all_iris.return_value = [cn.scheme["@id"]]

    graph_service.relationships_create = AsyncMock(side_effect=DuplicateRelationship())
    graph_service.concept_delete = AsyncMock()

    try:
        await graph_service.concept_create(concept=entities[0], relationships=relationships)
    except DuplicateRelationship:
        pass

    mock_kos_graph.concept_create.assert_called_with(concept=entities[0])
    graph_service.relationships_create.assert_called_with(relationships)
    graph_service.concept_delete.assert_called_with(entities[0].id_)


async def test_concept_update(graph_service, cn, entities):
    mock_kos_graph = graph_service.graph
    mock_kos_graph.concept_update.return_value = entities[0]
    mock_kos_graph.concept_scheme_get_all_iris.return_value = [cn.scheme["@id"]]

    result = await graph_service.concept_update(entities[0])
    assert result == entities[0]
    mock_kos_graph.concept_update.assert_called_with(concept=entities[0])


async def test_concept_update_missing_concept_scheme(graph_service, cn, entities, relationships):
    mock_kos_graph = graph_service.graph
    mock_kos_graph.concept_scheme_get_all_iris.return_value = ["http://example.com/foo"]

    with pytest.raises(ConceptSchemesNotInDatabase) as excinfo:
        await graph_service.concept_update(entities[0])

    id_ = cn.scheme["@id"]
    assert excinfo.match(
        f"At least one of the specified concept schemes must be in the database: {{'{id_}'}}"
    )


async def test_concept_update_cross_scheme_relationship(graph_service, cn, entities):
    original = entities[0]
    original.schemes = [{"@id": "http://example.com/a"}]
    updated = entities[1]
    updated.schemes = [{"@id": "http://example.com/b"}]

    mock_kos_graph = graph_service.graph
    mock_kos_graph.concept_get.return_value = original
    mock_kos_graph.concept_scheme_get_all_iris.return_value = [
        "http://example.com/a",
        "http://example.com/b",
    ]
    mock_kos_graph.known_concept_schemes_for_concept_hierarchical_relationships.return_value = [
        "http://example.com/a"
    ]

    with pytest.raises(RelationshipsInCurrentConceptScheme) as excinfo:
        await graph_service.concept_update(updated)

    assert excinfo.match(
        "Update asked to change concept schemes, but existing concept scheme {'http://example.com/a'} had hierarchical relationships."
    )


async def test_concept_update_cross_scheme_relationship_allowed(graph_service, entities):
    original = entities[0]
    original.schemes = [{"@id": "http://example.com/a"}]
    updated = entities[1]
    updated.schemes = [{"@id": "http://example.com/b"}]

    mock_kos_graph = graph_service.graph
    mock_kos_graph.concept_get.return_value = original
    mock_kos_graph.concept_scheme_get_all_iris.return_value = [
        "http://example.com/a",
        "http://example.com/b",
    ]
    mock_kos_graph.known_concept_schemes_for_concept_hierarchical_relationships.return_value = []

    assert await graph_service.concept_update(updated)


async def test_concept_update_cross_scheme_relationship_not_called(graph_service, cn, entities):
    original = entities[0]
    original.schemes = [{"@id": "http://example.com/a"}]

    mock_kos_graph = graph_service.graph
    mock_kos_graph.concept_get.return_value = original
    mock_kos_graph.concept_scheme_get_all_iris.return_value = [
        cn.scheme["@id"],
        "http://example.com/a",
    ]
    assert await graph_service.concept_update(original)
    mock_kos_graph.known_concept_schemes_for_concept_hierarchical_relationships.assert_not_called()


async def test_concept_delete(graph_service, entities):
    mock_kos_graph = graph_service.graph
    mock_kos_graph.concept_delete.return_value = 1

    result = await graph_service.concept_delete(entities[0].id_)
    assert result is None
    mock_kos_graph.concept_delete.assert_called_with(iri=entities[0].id_)


async def concept_delete_not_found(graph_service, entities):
    mock_kos_graph = graph_service.graph
    mock_kos_graph.concept_delete.return_value = 0

    with pytest.raises(ConceptNotFoundError):
        await graph_service.concept_delete(entities[0].id_)
