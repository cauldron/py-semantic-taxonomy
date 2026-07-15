from copy import deepcopy

import pytest

from py_semantic_taxonomy.domain.constants import SKOS, RelationshipVerbs
from py_semantic_taxonomy.domain.entities import (
    Concept,
    ConceptScheme,
    DuplicateRelationship,
    Relationship,
)


async def test_get_relationships_source(sqlite, graph, relationships):
    given = await graph.relationships_get(iri="http://data.europa.eu/xsp/cn2024/010021000090")
    assert given == [relationships[3]]


async def test_get_relationships_target(sqlite, graph, relationships):
    given = await graph.relationships_get(
        iri="http://data.europa.eu/xsp/cn2024/010021000090", source=False, target=True
    )
    assert given == [relationships[2], relationships[4]]


async def test_get_relationships_verb(sqlite, graph, relationships):
    given = await graph.relationships_get(
        iri="http://data.europa.eu/xsp/cn2023/010100000080",
        source=True,
        target=False,
        verb=RelationshipVerbs.broad_match,
    )
    assert given == [relationships[2]]


async def test_get_relationships_both(sqlite, graph, relationships):
    given = await graph.relationships_get(
        iri="http://data.europa.eu/xsp/cn2024/010021000090", target=True
    )
    assert given == [relationships[2], relationships[3], relationships[4]]


async def test_create_relationships(sqlite, graph):
    rels = [Relationship(source="a", target="b", predicate=RelationshipVerbs.exact_match)]
    out = await graph.relationships_create(rels)
    assert out == rels

    found = await graph.relationships_get(iri="a")
    assert found == rels


async def test_create_relationships_exact_duplicate_ignored(sqlite, graph, relationships):
    # relationships[3] already exists in the fixture; re-creating the exact same
    # relationship is a no-op instead of an error (issue #41).
    out = await graph.relationships_create([relationships[3]])
    assert out == [relationships[3]]

    found = await graph.relationships_get(iri=relationships[3].source)
    assert found == [relationships[3]]


async def test_create_relationships_conflicting_predicate(sqlite, graph, relationships):
    # Same source and target but a different predicate is a genuine conflict, not a
    # duplicate to ignore.
    conflict = Relationship(
        source=relationships[3].source,
        target=relationships[3].target,
        predicate=RelationshipVerbs.close_match,
    )
    with pytest.raises(DuplicateRelationship) as excinfo:
        await graph.relationships_create([conflict])
    assert excinfo.match(
        f"Relationship between source `{conflict.source}` and target `{conflict.target}` already exists"
    )


async def test_create_relationships_mixed_batch(sqlite, graph, relationships):
    # A batch mixing an existing exact duplicate with a new relationship inserts the
    # new one and ignores the duplicate.
    new = Relationship(source="x", target="y", predicate=RelationshipVerbs.exact_match)
    out = await graph.relationships_create([relationships[3], new])
    assert out == [relationships[3], new]

    assert await graph.relationships_get(iri="x") == [new]


async def test_create_relationships_intra_batch_exact_duplicate(sqlite, graph):
    # The same new relationship repeated within one call is inserted once, not an error.
    dup = Relationship(source="x", target="y", predicate=RelationshipVerbs.exact_match)
    out = await graph.relationships_create([dup, dup])
    assert out == [dup, dup]

    assert await graph.relationships_get(iri="x") == [dup]


async def test_create_relationships_intra_batch_conflict(sqlite, graph):
    # Two relationships in one call sharing source and target but differing in predicate
    # is a conflict, not a silent failure.
    with pytest.raises(DuplicateRelationship):
        await graph.relationships_create(
            [
                Relationship(source="x", target="y", predicate=RelationshipVerbs.broad_match),
                Relationship(source="x", target="y", predicate=RelationshipVerbs.close_match),
            ]
        )


async def test_create_relationships_retries_after_integrity_race(sqlite, graph):
    # A concurrent writer can insert an overlapping (source, target) pair between our
    # snapshot read and our insert, raising IntegrityError. That must be re-classified
    # and retried, not surfaced as a spurious DuplicateRelationship (issue #41).
    from unittest import mock

    from sqlalchemy.exc import IntegrityError
    from sqlalchemy.ext.asyncio import AsyncConnection
    from sqlalchemy.sql.dml import Insert

    rel = Relationship(source="x", target="y", predicate=RelationshipVerbs.exact_match)
    original = AsyncConnection.execute
    inserts = {"n": 0}

    async def flaky_execute(self, statement, *args, **kwargs):
        if isinstance(statement, Insert):
            inserts["n"] += 1
            if inserts["n"] == 1:
                raise IntegrityError("simulated race", None, Exception("UNIQUE"))
        return await original(self, statement, *args, **kwargs)

    with mock.patch.object(AsyncConnection, "execute", flaky_execute):
        out = await graph.relationships_create([rel])

    assert out == [rel]
    assert await graph.relationships_get(iri="x") == [rel]


async def test_delete_concept(sqlite, graph, relationships):
    response = await graph.relationships_delete(relationships)
    assert response == 5, "Wrong number of deleted relationships"

    response = await graph.relationships_delete(relationships)
    assert response == 0, "Wrong number of deleted concepts"


async def test_relationship_source_target_share_known_concept_scheme_internal(
    sqlite, graph, cn, relationships
):
    assert await graph.relationship_source_target_share_known_concept_scheme(relationships[3])


async def test_relationship_source_target_share_known_concept_scheme_external(
    sqlite, graph, cn, relationships
):
    external = Relationship(
        source=relationships[3].source,
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
        source=relationships[3].source,
        target=new_concept["@id"],
        predicate=RelationshipVerbs.broader,
    )
    assert not (await graph.relationship_source_target_share_known_concept_scheme(cross_cs))

    # Method doesn't care about predicate type (associate versus hierarchical)
    cross_cs = Relationship(
        source=relationships[3].source,
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
