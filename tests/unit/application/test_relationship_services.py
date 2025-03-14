import pytest

from py_semantic_taxonomy.domain.constants import RelationshipVerbs
from py_semantic_taxonomy.domain.entities import (
    HierarchicRelationshipAcrossConceptScheme,
    Relationship,
)


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


async def test_relationship_create(graph_service, relationships):
    mock_kos_graph = graph_service.graph
    mock_kos_graph.relationships_create.return_value = relationships

    result = await graph_service.relationships_create(relationships)
    assert result == relationships
    mock_kos_graph.relationships_create.assert_called_with(relationships)


async def test_relationship_create_cross_concept_scheme_hierarchical(graph_service, relationships):
    mock_kos_graph = graph_service.graph
    mock_kos_graph.relationship_source_target_share_known_concept_scheme.return_value = False

    rel = relationships[0]

    with pytest.raises(HierarchicRelationshipAcrossConceptScheme) as excinfo:
        await graph_service.relationships_create([rel])

    assert excinfo.match(
        f"Hierarchical relationship between `{rel.source}` and `{rel.target}` crosses Concept Schemes. Use an associative relationship like `skos:broadMatch` instead."
    )


async def test_relationship_create_cross_concept_scheme_associative(graph_service, relationships):
    mock_kos_graph = graph_service.graph
    mock_kos_graph.relationship_source_target_share_known_concept_scheme.return_value = False

    associative = Relationship(
        source=relationships[0].source,
        target=relationships[0].target,
        predicate=RelationshipVerbs.broad_match,
    )
    await graph_service.relationships_create([associative])
    mock_kos_graph.relationship_source_target_share_known_concept_scheme.assert_not_called()


async def test_relationship_update(graph_service, relationships):
    mock_kos_graph = graph_service.graph
    mock_kos_graph.relationships_update.return_value = relationships

    result = await graph_service.relationships_update(relationships)
    assert result == relationships
    mock_kos_graph.relationships_update.assert_called_with(relationships)


async def test_relationship_update_cross_concept_scheme_hierarchical(graph_service, relationships):
    mock_kos_graph = graph_service.graph
    mock_kos_graph.relationship_source_target_share_known_concept_scheme.return_value = False

    rel = relationships[0]

    with pytest.raises(HierarchicRelationshipAcrossConceptScheme) as excinfo:
        await graph_service.relationships_update([rel])

    assert excinfo.match(
        f"Hierarchical relationship between `{rel.source}` and `{rel.target}` crosses Concept Schemes. Use an associative relationship like `skos:broadMatch` instead."
    )


async def test_relationship_update_cross_concept_scheme_associative(graph_service, relationships):
    mock_kos_graph = graph_service.graph
    mock_kos_graph.relationship_source_target_share_known_concept_scheme.return_value = False

    associative = Relationship(
        source=relationships[0].source,
        target=relationships[0].target,
        predicate=RelationshipVerbs.broad_match,
    )
    await graph_service.relationships_update([associative])
    mock_kos_graph.relationship_source_target_share_known_concept_scheme.assert_not_called()


async def test_relationship_delete(graph_service, relationships):
    mock_kos_graph = graph_service.graph
    mock_kos_graph.relationships_delete.return_value = 1

    result = await graph_service.relationships_delete(relationships)
    assert result == 1
    mock_kos_graph.relationships_delete.assert_called_with(relationships)
