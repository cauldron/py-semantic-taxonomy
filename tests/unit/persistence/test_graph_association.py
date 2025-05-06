import pytest

from py_semantic_taxonomy.domain.constants import AssociationKind
from py_semantic_taxonomy.domain.entities import (
    Association,
    AssociationNotFoundError,
    Correspondence,
    DuplicateIRI,
    MadeOf,
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


@pytest.mark.postgres
async def test_associations_get_all_no_filters(postgres, cn, entities, graph):
    assocs = await graph.association_get_all(
        correspondence_iri=None,
        source_concept_iri=None,
        target_concept_iri=None,
        kind=None,
    )
    assert len(assocs) == 2
    assert assocs == [entities[7], entities[8]], "Incorrect data attributes"


@pytest.mark.postgres
async def test_associations_get_all_source_concept(postgres, cn, entities, graph):
    new = Association(
        id_="http://example.com/foo",
        types=cn.association_top["@type"],
        source_concepts=[
            {"@id": cn.concept_2023_top["@id"]},
            {"@id": cn.concept_2023_low["@id"]},
        ],
        target_concepts=[{"@id": cn.concept_top["@id"]}],
    )
    await graph.association_create(association=new)

    assocs = await graph.association_get_all(
        source_concept_iri=entities[5].id_,
        correspondence_iri=None,
        target_concept_iri=None,
        kind=None,
    )
    assert assocs == [entities[8], new], "Incorrect data attributes"


@pytest.mark.postgres
async def test_associations_get_all_target_concept(postgres, cn, entities, graph):
    new = Association(
        id_="http://example.com/foo",
        types=cn.association_top["@type"],
        source_concepts=[
            {"@id": cn.concept_2023_top["@id"]},
        ],
        target_concepts=[{"@id": cn.concept_top["@id"]}, {"@id": cn.concept_2023_low["@id"]}],
    )
    await graph.association_create(association=new)

    assocs = await graph.association_get_all(
        target_concept_iri=cn.concept_top["@id"],
        correspondence_iri=None,
        source_concept_iri=None,
        kind=None,
    )
    assert assocs == [entities[8], new], "Incorrect data attributes"


@pytest.mark.postgres
async def test_associations_get_all_kind_conditional(postgres, cn, entities, graph):
    new = Association(
        id_="http://example.com/foo",
        types=cn.association_top["@type"],
        source_concepts=[
            {"@id": cn.concept_2023_top["@id"]},
            {"@id": cn.concept_2023_low["@id"]},
        ],
        target_concepts=[{"@id": cn.concept_top["@id"]}],
    )
    await graph.association_create(association=new)

    assocs = await graph.association_get_all(
        kind=AssociationKind.conditional,
        source_concept_iri=None,
        target_concept_iri=None,
        correspondence_iri=None,
    )
    assert assocs == [new], "Incorrect data attributes"


@pytest.mark.postgres
async def test_associations_get_all_correspondence(postgres, cn, entities, graph):
    cn.correspondence["@id"] = "http://pyst-tests.ninja/correspondence/new"
    corr = Correspondence.from_json_ld(cn.correspondence)
    await graph.correspondence_create(correspondence=corr)

    assoc = Association(
        id_="http://pyst-tests.ninja/association/foo",
        types=cn.association_top["@type"],
        source_concepts=[
            {"@id": cn.concept_2023_top["@id"]},
            {"@id": cn.concept_2023_low["@id"]},
        ],
        target_concepts=[{"@id": cn.concept_top["@id"]}],
    )
    await graph.association_create(association=assoc)

    made_of = MadeOf(
        id_="http://pyst-tests.ninja/correspondence/new",
        made_ofs=[
            {"@id": "http://pyst-tests.ninja/association/foo"},
        ],
    )
    await graph.made_of_add(made_of)

    assocs = await graph.association_get_all(
        correspondence_iri="http://pyst-tests.ninja/correspondence/new",
        source_concept_iri=None,
        target_concept_iri=None,
        kind=None,
    )
    assert assocs == [assoc], "Incorrect data attributes"


@pytest.mark.postgres
async def test_associations_get_all_all_filters(postgres, cn, entities, graph, made_of):
    await graph.made_of_add(made_of)

    assocs = await graph.association_get_all(
        correspondence_iri=cn.correspondence["@id"],
        source_concept_iri=cn.concept_2023_top["@id"],
        target_concept_iri=cn.concept_top["@id"],
        kind=AssociationKind.simple,
    )
    assert assocs == [entities[8]], "Incorrect data attributes"


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
