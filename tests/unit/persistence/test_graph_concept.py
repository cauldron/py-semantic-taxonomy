import pytest

from py_semantic_taxonomy.domain.constants import RelationshipVerbs
from py_semantic_taxonomy.domain.entities import (
    Concept,
    ConceptNotFoundError,
    DuplicateIRI,
    Relationship,
)


async def test_get_object_type_concept(sqlite, graph):
    concept = await graph.get_object_type(iri="http://data.europa.eu/xsp/cn2024/010011000090")
    assert concept is Concept, "Wrong result type"


async def test_get_concept(sqlite, entities, graph):
    concept = await graph.concept_get(iri="http://data.europa.eu/xsp/cn2024/010011000090")
    assert isinstance(concept, Concept), "Wrong result type"
    assert concept == entities[0]  # Check all data attributes correct


async def test_get_concept_not_found(sqlite, graph):
    with pytest.raises(ConceptNotFoundError):
        await graph.concept_get(iri="http://data.europa.eu/xsp/cn2024/woof")


async def test_create_concept(sqlite, cn, entities, graph):
    expected = Concept.from_json_ld(cn.concept_low)

    response = await graph.concept_create(concept=expected)
    assert isinstance(response, Concept), "Wrong result type"
    assert response == expected, "Data attributes from database differ"

    given = await graph.concept_get(iri=cn.concept_low["@id"])
    assert given == expected, "Data attributes from database differ"

    given = await graph.relationships_get(iri=cn.concept_low["@id"])
    assert given == [
        Relationship(
            source="http://data.europa.eu/xsp/cn2024/010100000080",
            target="http://data.europa.eu/xsp/cn2024/010021000090",
            predicate=RelationshipVerbs.broader,
        )
    ], "Relationship not created"


async def test_create_concept_duplicate(sqlite, cn, entities, graph):
    with pytest.raises(DuplicateIRI):
        await graph.concept_create(concept=Concept.from_json_ld(cn.concept_top))


async def test_update_concept(sqlite, cn, entities, graph):
    expected = Concept.from_json_ld(cn.concept_top)
    expected.alt_labels = [{"@value": "Dream a little dream", "@language": "en"}]

    response = await graph.concept_update(concept=expected)
    assert isinstance(response, Concept), "Wrong result type"
    assert response == expected, "Data attributes from database differ"

    given = await graph.concept_get(iri=cn.concept_top["@id"])
    assert given == expected, "Data attributes from database differ"


async def test_update_concept_missing(sqlite, cn, entities, graph):
    expected = Concept.from_json_ld(cn.concept_low)
    with pytest.raises(ConceptNotFoundError):
        await graph.concept_update(concept=expected)


async def test_delete_concept(sqlite, cn, entities, graph):
    response = await graph.concept_delete(iri=cn.concept_mid["@id"])
    assert response == 1, "Wrong number of deleted concepts"

    response = await graph.concept_delete(iri=cn.concept_mid["@id"])
    assert response == 0, "Wrong number of deleted concepts"


@pytest.mark.postgres
async def test_concepts_get_for_scheme_order(postgres, cn, graph):
    concepts = await graph.concepts_get_for_scheme(cn.scheme["@id"], False)
    assert concepts
    assert isinstance(concepts[0], Concept)
    assert [concept.id_ for concept in concepts] == sorted(
        [cn.concept_top["@id"], cn.concept_mid["@id"]]
    )


@pytest.mark.postgres
async def test_concepts_get_for_scheme_top_concepts(postgres, cn, graph):
    concepts = await graph.concepts_get_for_scheme(cn.scheme_2023["@id"], True)
    assert len(concepts) == 1
    assert isinstance(concepts[0], Concept)
    assert concepts[0].id_ == cn.concept_2023_top["@id"]


@pytest.mark.postgres
async def test_concepts_get_for_scheme_empty(postgres, cn, graph):
    concepts = await graph.concepts_get_for_scheme("http://missing.ninja/foo", False)
    assert concepts == []


@pytest.mark.postgres
async def test_concept_broader_in_ascending_order(postgres, cn, graph):
    async def fake(id_: str, schemes: list[dict]) -> Concept:
        concept = Concept(
            id_=f"http://example.com/{id_}",
            schemes=schemes,
            types=[],
            pref_labels=[],
            status=[],
        )
        await graph.concept_create(concept=concept)
        return concept

    a = await fake("a", [{"@id": cn.scheme["@id"]}, {"@id": cn.scheme_2023["@id"]}])
    b = await fake("b", [{"@id": cn.scheme["@id"]}])
    c = await fake("c", [{"@id": cn.scheme["@id"]}])
    d = await fake("d", [{"@id": cn.scheme_2023["@id"]}])
    e = await fake("e", [{"@id": cn.scheme["@id"]}, {"@id": cn.scheme_2023["@id"]}])
    f = await fake("f", [{"@id": cn.scheme_2023["@id"]}])
    g = await fake("g", [{"@id": cn.scheme["@id"]}])
    h = await fake("h", [{"@id": cn.scheme["@id"]}])

    # A -> (B, C) (D in wrong scheme) -> E (F in wrong scheme) -> G (H with wrong verb)
    await graph.relationships_create(
        [
            Relationship(source=a.id_, target=b.id_, predicate=RelationshipVerbs.broader),
            Relationship(source=a.id_, target=c.id_, predicate=RelationshipVerbs.broader),
            Relationship(source=a.id_, target=d.id_, predicate=RelationshipVerbs.broader),
            Relationship(source=b.id_, target=e.id_, predicate=RelationshipVerbs.broader),
            Relationship(source=c.id_, target=e.id_, predicate=RelationshipVerbs.broader),
            Relationship(source=c.id_, target=f.id_, predicate=RelationshipVerbs.broader),
            Relationship(source=e.id_, target=g.id_, predicate=RelationshipVerbs.broader),
            Relationship(source=e.id_, target=h.id_, predicate=RelationshipVerbs.broad_match),
        ]
    )

    expected = [
        "http://example.com/b",
        "http://example.com/c",
        "http://example.com/e",
        "http://example.com/g",
    ]
    result = await graph.concept_broader_in_ascending_order(a.id_, cn.scheme["@id"])
    result_ids = [obj.id_ for obj in result]
    assert result_ids == expected
