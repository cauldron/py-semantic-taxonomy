import pytest

from py_semantic_taxonomy.domain.constants import AssociationKind
from py_semantic_taxonomy.domain.entities import (
    Association,
    AssociationNotFoundError,
    DuplicateIRI,
)


async def test_get_object_type_concept(sqlite, entities, graph):
    assoc = await graph.get_object_type(iri=entities[8].id_)
    assert assoc is Association, "Wrong result type"


async def test_get_association(sqlite, entities, graph):
    assoc = await graph.association_get(iri=entities[8].id_)
    assert isinstance(assoc, Association), "Wrong result type"
    assert assoc == entities[8]  # Check all data attributes correct


async def test_get_association_not_found(sqlite, graph):
    with pytest.raises(AssociationNotFoundError):
        await graph.association_get(iri="http://data.europa.eu/xsp/cn2024/woof")


async def test_create_association_simple(sqlite, cn, entities, graph):
    new = Association(
        id_="http://example.com/foo",
        types=cn.association_top["@type"],
        source_concepts=[{"@id": cn.concept_mid["@id"]}],
        target_concepts=[{"@id": cn.concept_2023_top["@id"]}],
    )
    assert new.kind == AssociationKind.simple

    response = await graph.association_create(association=new)
    assert isinstance(response, Association), "Wrong result type"
    assert response == new, "Data attributes from database differ"

    given = await graph.association_get(iri=new.id_)
    assert given == new, "Data attributes from database differ"


async def test_create_association_conditional(sqlite, cn, entities, graph):
    new = Association(
        id_="http://example.com/foo",
        types=cn.association_top["@type"],
        source_concepts=[{"@id": cn.concept_mid["@id"]}, {"@id": cn.concept_top["@id"]}],
        target_concepts=[{"@id": cn.concept_2023_top["@id"]}],
    )
    assert new.kind == AssociationKind.conditional

    response = await graph.association_create(association=new)
    assert isinstance(response, Association), "Wrong result type"
    assert response == new, "Data attributes from database differ"

    given = await graph.association_get(iri=new.id_)
    assert given == new, "Data attributes from database differ"


async def test_create_association_duplicate(sqlite, cn, entities, graph):
    with pytest.raises(DuplicateIRI):
        await graph.association_create(association=Association.from_json_ld(cn.association_top))


async def test_delete_association(sqlite, cn, entities, graph):
    response = await graph.association_delete(iri=cn.association_top["@id"])
    assert response == 1, "Wrong number of deleted concepts"

    response = await graph.concept_delete(iri=cn.association_top["@id"])
    assert response == 0, "Wrong number of deleted concepts"
