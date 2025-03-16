from copy import deepcopy

import pytest

from py_semantic_taxonomy.domain.constants import SKOS, RelationshipVerbs
from py_semantic_taxonomy.domain.entities import (
    Concept,
    ConceptScheme,
    DuplicateRelationship,
    Relationship,
    RelationshipNotFoundError,
)


async def test_get_relationships_source(sqlite, graph, relationships):
    given = await graph.relationships_get(iri="http://data.europa.eu/xsp/cn2024/010021000090")
    assert given == [relationships[1]]


async def test_get_relationships_target(sqlite, graph, relationships):
    given = await graph.relationships_get(
        iri="http://data.europa.eu/xsp/cn2024/010021000090", source=False, target=True
    )
    assert given == [relationships[2]]


async def test_get_relationships_both(sqlite, graph, relationships):
    given = await graph.relationships_get(
        iri="http://data.europa.eu/xsp/cn2024/010021000090", target=True
    )
    assert given == relationships[1:]


async def test_create_relationships(sqlite, graph):
    rels = [Relationship(source="a", target="b", predicate=RelationshipVerbs.exact_match)]
    out = await graph.relationships_create(rels)
    assert out == rels

    found = await graph.relationships_get(iri="a")
    assert found == rels


async def test_create_relationships_duplicate(sqlite, graph, relationships):
    with pytest.raises(DuplicateRelationship) as excinfo:
        await graph.relationships_create([relationships[1]])
    assert excinfo.match(
        f"Relationship between source `{relationships[1].source}` and target `{relationships[1].target}` already exists"
    )


async def test_update_relationships(sqlite, graph, relationships):
    result = await graph.relationships_get(iri=relationships[1].source)
    assert result == [relationships[1]]

    rel = Relationship(
        source=relationships[1].source,
        target=relationships[1].target,
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
    assert response == 3, "Wrong number of deleted relationships"

    response = await graph.relationships_delete(relationships)
    assert response == 0, "Wrong number of deleted concepts"


async def test_relationship_source_target_share_known_concept_scheme_internal(
    sqlite, graph, cn, relationships
):
    assert await graph.relationship_source_target_share_known_concept_scheme(relationships[1])


async def test_relationship_source_target_share_known_concept_scheme_external(
    sqlite, graph, cn, relationships
):
    external = Relationship(
        source=relationships[1].source,
        target="http://example.com/bar",
        predicate=RelationshipVerbs.exact_match,
    )
    assert await graph.relationship_source_target_share_known_concept_scheme(external)


async def test_relationship_source_target_share_known_concept_scheme_cross_cs_hierarchical(
    sqlite, graph, cn, relationships
):
    new_scheme = cn.scheme
    new_scheme["@id"] = "http://example.com/foo"
    await graph.concept_scheme_create(ConceptScheme.from_json_ld(new_scheme))

    new_concept = cn.concept_low
    new_concept[f"{SKOS}inScheme"] = [{"@id": "http://example.com/foo"}]
    new_concept["@id"] = "http://example.com/bar"
    await graph.concept_create(Concept.from_json_ld(new_concept))

    cross_cs = Relationship(
        source=relationships[1].source,
        target=new_concept["@id"],
        predicate=RelationshipVerbs.broader,
    )
    assert not (await graph.relationship_source_target_share_known_concept_scheme(cross_cs))

    # Method doesn't care about predicate type (associate versus hierarchical)
    cross_cs = Relationship(
        source=relationships[1].source,
        target=new_concept["@id"],
        predicate=RelationshipVerbs.broad_match,
    )
    assert not (await graph.relationship_source_target_share_known_concept_scheme(cross_cs))


async def test_known_concept_schemes_for_concept_hierarchical_relationships_none(sqlite, graph, cn):
    new_concept = cn.concept_low
    del new_concept[f"{SKOS}broader"]
    new_concept["@id"] = "http://example.com/a"
    await graph.concept_create(Concept.from_json_ld(new_concept))

    found = await graph.known_concept_schemes_for_concept_hierarchical_relationships(
        new_concept["@id"]
    )
    assert found == []


async def test_known_concept_schemes_for_concept_hierarchical_relationships(
    sqlite, graph, cn, relationships
):
    """
    Concept schemes: A, B, C, D, E
    Concepts: 1 [A], 2 [A], 3 [A, B], 4 [C], 5 [A, D], 6 [A, E]

    Hierarchical relationships:
    1 -> 2, 1 -> 3, 6 -> 1

    Associative relationships:
    1 -> 5, 4 -> 1

    Expected for 1: A, B, E
    """
    del cn.concept_low[f"{SKOS}broader"]

    async def new_scheme(code: str) -> str:
        new_scheme = deepcopy(cn.scheme)
        new_scheme["@id"] = f"http://example.com/{code}"
        await graph.concept_scheme_create(ConceptScheme.from_json_ld(new_scheme))
        return f"http://example.com/{code}"

    async def new_concept(code: str, cs: list[str]) -> str:
        new_concept = deepcopy(cn.concept_low)
        new_concept["@id"] = f"http://example.com/{code}"
        new_concept[f"{SKOS}inScheme"] = [{"@id": obj} for obj in cs]
        await graph.concept_create(Concept.from_json_ld(new_concept))
        return f"http://example.com/{code}"

    async def new_relationship(source: str, target: str, hierarchical: bool = True) -> None:
        rel = Relationship(
            source=source,
            target=target,
            predicate=RelationshipVerbs.broader if hierarchical else RelationshipVerbs.exact_match,
        )
        await graph.relationships_create([rel])

    a = await new_scheme("A")
    b = await new_scheme("B")
    c = await new_scheme("C")
    d = await new_scheme("D")
    e = await new_scheme("E")

    one = await new_concept("1", [a])
    two = await new_concept("2", [a])
    three = await new_concept("3", [a, b])
    four = await new_concept("4", [c])
    five = await new_concept("5", [a, d])
    six = await new_concept("6", [a, e])

    await new_relationship(one, two)
    await new_relationship(one, three)
    await new_relationship(six, one)
    await new_relationship(one, five, False)
    await new_relationship(four, one, False)

    found = await graph.known_concept_schemes_for_concept_hierarchical_relationships(one)
    assert found == [a, b, e]
