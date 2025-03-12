import pytest

from py_semantic_taxonomy.domain.constants import RelationshipVerbs
from py_semantic_taxonomy.domain.entities import DuplicateRelationship, Relationship


async def test_get_relationships_source(sqlite, graph, relationships):
    given = await graph.relationships_get(iri="http://data.europa.eu/xsp/cn2024/010021000090")
    assert given == [relationships[0]]


async def test_get_relationships_target(sqlite, graph, relationships):
    given = await graph.relationships_get(
        iri="http://data.europa.eu/xsp/cn2024/010021000090", source=False, target=True
    )
    assert given == [relationships[1]]


async def test_get_relationships_both(sqlite, graph, relationships):
    given = await graph.relationships_get(
        iri="http://data.europa.eu/xsp/cn2024/010021000090", target=True
    )
    assert given == relationships


async def test_create_relationships(sqlite, graph):
    rels = [Relationship(source="a", target="b", predicate=RelationshipVerbs.exact_match)]
    out = await graph.relationships_create(rels)
    assert out == rels

    found = await graph.relationships_get(iri="a")
    assert found == rels


async def test_create_relationships_duplicate(sqlite, graph, relationships):
    with pytest.raises(DuplicateRelationship):
        await graph.relationships_create(relationships)
