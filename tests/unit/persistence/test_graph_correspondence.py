import pytest

from py_semantic_taxonomy.domain.entities import (
    Correspondence,
    CorrespondenceNotFoundError,
)


async def test_get_object_type_correspondence(sqlite, graph):
    corr = await graph.get_object_type(iri="http://pyst-tests.ninja/correspondence/cn2023_cn2024")
    assert corr is Correspondence, "Wrong result type"


async def test_get_correspondence(sqlite, entities, graph):
    corr = await graph.correspondence_get(
        iri="http://pyst-tests.ninja/correspondence/cn2023_cn2024"
    )
    assert isinstance(corr, Correspondence), "Wrong result type"
    assert corr == entities[3]  # Check all data attributes correct


async def test_get_correspondence_not_found(sqlite, graph):
    with pytest.raises(CorrespondenceNotFoundError):
        await graph.correspondence_get(iri="http://pyst-tests.ninja/correspondence/missing")


# async def test_create_concept(sqlite, cn, entities, graph):
#     expected = Concept.from_json_ld(cn.concept_low)

#     response = await graph.concept_create(concept=expected)
#     assert isinstance(response, Concept), "Wrong result type"
#     assert response == expected, "Data attributes from database differ"

#     given = await graph.concept_get(iri=cn.concept_low["@id"])
#     assert given == expected, "Data attributes from database differ"

#     given = await graph.relationships_get(iri=cn.concept_low["@id"])
#     assert given == [
#         Relationship(
#             source="http://data.europa.eu/xsp/cn2024/010100000080",
#             target="http://data.europa.eu/xsp/cn2024/010021000090",
#             predicate=RelationshipVerbs.broader,
#         )
#     ], "Relationship not created"


# async def test_create_concept_duplicate(sqlite, cn, entities, graph):
#     with pytest.raises(DuplicateIRI):
#         await graph.concept_create(concept=Concept.from_json_ld(cn.concept_top))


# async def test_update_concept(sqlite, cn, entities, graph):
#     expected = Concept.from_json_ld(cn.concept_top)
#     expected.alt_labels = [{"@value": "Dream a little dream", "@language": "en"}]

#     response = await graph.concept_update(concept=expected)
#     assert isinstance(response, Concept), "Wrong result type"
#     assert response == expected, "Data attributes from database differ"

#     given = await graph.concept_get(iri=cn.concept_top["@id"])
#     assert given == expected, "Data attributes from database differ"


# async def test_update_concept_missing(sqlite, cn, entities, graph):
#     expected = Concept.from_json_ld(cn.concept_low)
#     with pytest.raises(ConceptNotFoundError):
#         await graph.concept_update(concept=expected)


# async def test_delete_concept(sqlite, cn, entities, graph):
#     response = await graph.concept_delete(iri=cn.concept_mid["@id"])
#     assert response == 1, "Wrong number of deleted concepts"

#     response = await graph.concept_delete(iri=cn.concept_mid["@id"])
#     assert response == 0, "Wrong number of deleted concepts"
