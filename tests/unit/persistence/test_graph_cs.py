import pytest

from py_semantic_taxonomy.domain.entities import (
    ConceptScheme,
    ConceptSchemeNotFoundError,
    DuplicateIRI,
)


async def test_get_object_type_concept(sqlite, entities, graph):
    cs = await graph.get_object_type(iri=entities[2].id_)
    assert cs is ConceptScheme, "Wrong result type"


async def test_get_concept_scheme(sqlite, entities, graph):
    cs = await graph.concept_scheme_get(iri=entities[2].id_)
    assert isinstance(cs, ConceptScheme), "Wrong result type"
    assert cs == entities[2]  # Check all data attributes correct


async def test_concept_scheme_get_all_iris(sqlite, entities, graph):
    cs = await graph.concept_scheme_get_all_iris()
    assert sorted(cs) == [entities[4].id_, entities[2].id_]


async def test_concept_scheme_list(sqlite, entities, graph):
    cs = await graph.concept_scheme_list()
    assert cs == sorted([entities[4], entities[2]], key=lambda x: x.id_)


async def test_get_concept_scheme_not_found(sqlite, graph):
    with pytest.raises(ConceptSchemeNotFoundError):
        await graph.concept_scheme_get(iri="http://data.europa.eu/xsp/cn2024/woof")


async def test_create_concept_scheme(sqlite, cn, entities, graph):
    new = cn.scheme
    new["@id"] = "http://data.europa.eu/xsp/cn2024/cn2025"
    expected = ConceptScheme.from_json_ld(new)

    response = await graph.concept_scheme_create(concept_scheme=expected)
    assert isinstance(response, ConceptScheme), "Wrong result type"
    assert response == expected, "Data attributes from database differ"

    given = await graph.concept_scheme_get(iri=new["@id"])
    assert given == expected, "Data attributes from database differ"


async def test_create_concept_scheme_duplicate(sqlite, cn, entities, graph):
    with pytest.raises(DuplicateIRI):
        await graph.concept_scheme_create(concept_scheme=ConceptScheme.from_json_ld(cn.scheme))


async def test_update_concept_scheme(sqlite, cn, entities, graph):
    expected = ConceptScheme.from_json_ld(cn.scheme)
    expected.pref_labels = [{"@value": "Combine all them nommies", "@language": "en"}]

    response = await graph.concept_scheme_update(concept_scheme=expected)
    assert isinstance(response, ConceptScheme), "Wrong result type"
    assert response == expected, "Data attributes from database differ"

    given = await graph.concept_scheme_get(iri=cn.scheme["@id"])
    assert given == expected, "Data attributes from database differ"


async def test_update_concept_scheme_missing(sqlite, cn, entities, graph):
    new = cn.scheme
    new["@id"] = "http://data.europa.eu/xsp/cn2024/cn2025"

    expected = ConceptScheme.from_json_ld(new)
    with pytest.raises(ConceptSchemeNotFoundError):
        await graph.concept_scheme_update(concept_scheme=expected)


async def test_delete_concept_scheme(sqlite, cn, entities, graph):
    response = await graph.concept_scheme_delete(iri=cn.scheme["@id"])
    assert response == 1, "Wrong number of deleted concepts"

    response = await graph.concept_delete(iri=cn.scheme["@id"])
    assert response == 0, "Wrong number of deleted concepts"
