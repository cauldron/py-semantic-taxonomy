import pytest

from py_semantic_taxonomy.domain.constants import RelationshipVerbs
from py_semantic_taxonomy.domain.entities import (
    DuplicateRelationship,
    Relationship,
    RelationshipNotFoundError,
)


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
    with pytest.raises(DuplicateRelationship) as excinfo:
        await graph.relationships_create([relationships[0]])
    assert excinfo.match(
        f"Relationship between source `{relationships[0].source}` and target `{relationships[0].target}` already exists"
    )


async def test_update_relationships(sqlite, graph, relationships):
    result = await graph.relationships_get(iri=relationships[0].source)
    assert result == [relationships[0]]

    rel = Relationship(
        source=relationships[0].source,
        target=relationships[0].target,
        predicate=RelationshipVerbs.exact_match,
    )
    await graph.relationships_update([rel])

    result = await graph.relationships_get(iri=rel.source)
    assert result == [rel]


async def test_update_relationships_not_found_error(sqlite, graph):
    missing = Relationship(
        source="http://example.com/foo",
        target="http://example.com/bar",
        predicate=RelationshipVerbs.exact_match,
    )
    with pytest.raises(RelationshipNotFoundError):
        await graph.relationships_update([missing])


async def test_delete_concept(sqlite, graph, relationships):
    response = await graph.relationships_delete(relationships)
    assert response == 2, "Wrong number of deleted relationships"

    response = await graph.relationships_delete(relationships)
    assert response == 0, "Wrong number of deleted concepts"
