import pytest

from py_semantic_taxonomy.domain.entities import (
    ConceptScheme,
    ConceptSchemeNotFoundError,
    DuplicateIRI,
)


async def test_get_object_type_concept(sqlite, graph):
    cs = await graph.get_object_type(iri="http://data.europa.eu/xsp/cn2024/cn2024")
    assert cs is ConceptScheme, "Wrong result type"


async def test_get_concept_scheme(sqlite, entities, graph):
    cs = await graph.concept_scheme_get(iri="http://data.europa.eu/xsp/cn2024/cn2024")
    assert isinstance(cs, ConceptScheme), "Wrong result type"
    assert cs == entities[2]  # Check all data attributes correct


async def test_get_concept_scheme_not_found(sqlite, graph):
    with pytest.raises(ConceptSchemeNotFoundError):
        await graph.concept_scheme_get(iri="http://data.europa.eu/xsp/cn2024/woof")


async def test_create_scheme_concept(sqlite, cn, entities, graph):
    new = cn.scheme
    new["@id"] = "http://data.europa.eu/xsp/cn2024/cn2025"
    expected = ConceptScheme.from_json_ld(new)

    response = await graph.concept_scheme_create(concept_scheme=expected)
    assert isinstance(response, ConceptScheme), "Wrong result type"
    assert response == expected, "Data attributes from database differ"

    given = await graph.concept_scheme_get(iri=new["@id"])
    assert given == expected, "Data attributes from database differ"


async def test_create_concept_duplicate(sqlite, cn, entities, graph):
    with pytest.raises(DuplicateIRI):
        await graph.concept_scheme_create(concept_scheme=ConceptScheme.from_json_ld(cn.scheme))


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
#     print(response)
#     assert response == 1, "Wrong number of deleted concepts"

#     response = await graph.concept_delete(iri=cn.concept_mid["@id"])
#     print(response)
#     assert response == 0, "Wrong number of deleted concepts"
